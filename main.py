"""
API中转站 - 主程序
上游：支持 siliconflow / groq / openai / bailian（通过 PROVIDER 环境变量切换）
部署：Railway / 本地均可

启动方式（切换上游）:
  python main.py                           # 默认阿里云百炼
  PROVIDER=siliconflow python main.py       # 硅基流动
  PROVIDER=groq python main.py              # Groq
  PROVIDER=openai python main.py            # OpenAI
"""
import sqlite3, uuid, hashlib, time, os, json
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 配置
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from datetime import datetime
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel
import httpx

# ==================== 配置（优先读环境变量）====================
# ★★★ 上游切换：修改 PROVIDER 即可 ★★★
#   可选: "siliconflow" | "groq" | "openai" | "bailian"
PROVIDER = os.environ.get("PROVIDER", "bailian")

# 各平台配置（填入你的真实 Key）
UPSTREAM_CONFIG = {
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key":  os.environ.get("SF_API_KEY", ""),   # 硅基流动 Key
        "models": [
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen3-235B-A22B",
            "Qwen/Qwen2.5-72B-Instruct",
            "Qwen/Qwen2.5-7B-Instruct",
            "THUDM/glm-4-9b-chat",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
        ],
        "pricing": {  # 元/百万tokens，零售价
            "deepseek-ai/DeepSeek-V3":              {"input": 3,  "output": 9},
            "deepseek-ai/DeepSeek-R1":              {"input": 6,  "output": 18},
            "Qwen/Qwen3-235B-A22B":                 {"input": 6,  "output": 18},
            "Qwen/Qwen2.5-72B-Instruct":           {"input": 4,  "output": 12},
            "Qwen/Qwen2.5-7B-Instruct":             {"input": 1,  "output": 3},
            "THUDM/glm-4-9b-chat":                  {"input": 1,  "output": 3},
            "meta-llama/Meta-Llama-3.1-70B-Instruct":{"input": 4, "output": 12},
        },
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key":  os.environ.get("GROQ_API_KEY", ""),  # Groq Key (gsk_xxx)
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "pricing": {
            "llama-3.3-70b-versatile":  {"input": 0.6,  "output": 2.4},
            "llama-3.1-70b-versatile":  {"input": 0.6,  "output": 2.4},
            "llama-3.1-8b-instant":     {"input": 0.2,  "output": 0.8},
            "mixtral-8x7b-32768":       {"input": 0.24, "output": 0.96},
            "gemma2-9b-it":             {"input": 0.2,  "output": 0.8},
        },
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key":  os.environ.get("OPENAI_API_KEY", ""),
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        "pricing": {
            "gpt-4o":      {"input": 15, "output": 60},
            "gpt-4o-mini": {"input": 1.5, "output": 6},
            "gpt-4-turbo":{"input": 30, "output": 90},
            "gpt-3.5-turbo": {"input": 3, "output": 12},
        },
    },
    "bailian": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key":  os.environ.get("DASHSCOPE_API_KEY", ""),  # 阿里云百炼 Key
        "models": [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-max-long上下文",
            "qwen-coder-plus",
            "qwen-long",          # 支持长上下文
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
            "qwen2.5-1.5b-instruct",
            "qwen2-7b-instruct",
        ],
        "pricing": {  # 元/百万tokens（对用户售价，有利润空间）
            "qwen-turbo":           {"input": 3,    "output": 6},
            "qwen-plus":            {"input": 10,   "output": 25},
            "qwen-max":             {"input": 80,   "output": 200},
            "qwen-max-long上下文":   {"input": 80,   "output": 200},
            "qwen-coder-plus":      {"input": 35,   "output": 90},
            "qwen-long":            {"input": 20,   "output": 50},
            "qwen2.5-72b-instruct": {"input": 10,   "output": 25},
            "qwen2.5-32b-instruct": {"input": 5,    "output": 12},
            "qwen2.5-14b-instruct": {"input": 2.5,  "output": 6},
            "qwen2.5-7b-instruct":  {"input": 1,    "output": 2.5},
            "qwen2.5-1.5b-instruct":{"input": 0.8,  "output": 1.5},
            "qwen2-7b-instruct":    {"input": 1,    "output": 2.5},
        },
    },
}

# 当前激活的上游
cfg = UPSTREAM_CONFIG.get(PROVIDER, UPSTREAM_CONFIG["siliconflow"])
UPSTREAM_BASE_URL = cfg["base_url"]
UPSTREAM_API_KEY  = cfg["api_key"]
AVAILABLE_MODELS = cfg["models"]
PRICING = cfg["pricing"]
# 补充 default
PRICING["default"] = {"input": 3, "output": 9}

# ==================== 路径 ====================
BASE_DIR = Path(__file__).parent
DATABASE_PATH = str(BASE_DIR / "api_relay.db")

# ==================== 数据库 ====================
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            api_key TEXT UNIQUE NOT NULL,
            username TEXT,
            balance REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS usage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)
    # 默认创建管理员 admin/admin123（首次运行后请改密码）
    admin_pwd = hashlib.sha256(b"admin123").hexdigest()
    c.execute("INSERT OR IGNORE INTO admins (username, password_hash) VALUES ('admin', ?)", (admin_pwd,))
    conn.commit()
    conn.close()

# ==================== 工具函数 ====================
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_api_key():
    return f"sk-relay-{uuid.uuid4().hex}"

def get_user(api_key: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE api_key=? AND is_active=1", (api_key,)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None

def deduct(user_id: str, cost: float) -> bool:
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE users SET balance=balance-? WHERE id=? AND balance>=?",
            (cost, user_id, cost)
        )
        conn.commit()
    finally:
        conn.close()
    return cur.rowcount > 0

def log_usage(user_id: str, model: str, inp: int, out: int, cost: float):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO usage_records(user_id,model,input_tokens,output_tokens,cost) VALUES(?,?,?,?,?)",
            (user_id, model, inp, out, cost)
        )
        conn.commit()
    finally:
        conn.close()

def calc_cost(model: str, inp: int, out: int) -> float:
    p = PRICING.get(model, PRICING["default"])
    return round((inp * p["input"] + out * p["output"]) / 1_000_000, 6)

# ==================== 应用 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="API中转站", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ==================== 鉴权辅助 ====================
def auth(authorization: Optional[str]):
    if not authorization:
        raise HTTPException(401, detail={"error": {"message": "Missing API key", "type": "auth_error"}})
    key = authorization.replace("Bearer ", "", 1).strip()
    user = get_user(key)
    if not user:
        raise HTTPException(401, detail={"error": {"message": "Invalid API key", "type": "auth_error"}})
    return user

# ==================== OpenAI 兼容代理 ====================
@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: str = Header(None)):
    user = auth(authorization)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, detail={"error": {"message": "Invalid JSON"}})

    model   = body.get("model", "deepseek-ai/DeepSeek-V3")
    stream  = body.get("stream", False)

    headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type":  "application/json",
    }

    # ── 流式模式 ──────────────────────────────────────────────────
    if stream:
        async def stream_gen() -> AsyncGenerator[bytes, None]:
            total_in, total_out = 0, 0
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    f"{UPSTREAM_BASE_URL}/chat/completions",
                    json=body,
                    headers=headers,
                ) as resp:
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        yield (line + "\n\n").encode()
                        # 粗略统计 token（流式无精确 usage）
                        if line.startswith("data:") and "[DONE]" not in line:
                            try:
                                chunk = json.loads(line[5:])
                                u = chunk.get("usage") or {}
                                total_in  += u.get("prompt_tokens", 0)
                                total_out += u.get("completion_tokens", 0)
                            except Exception:
                                pass

            cost = calc_cost(model, total_in, total_out)
            if cost > 0:
                if deduct(user["id"], cost):
                    log_usage(user["id"], model, total_in, total_out, cost)

        return StreamingResponse(stream_gen(), media_type="text/event-stream")

    # ── 非流式模式 ────────────────────────────────────────────────
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(
                f"{UPSTREAM_BASE_URL}/chat/completions",
                json=body, headers=headers
            )
        except httpx.TimeoutException:
            raise HTTPException(504, detail={"error": {"message": "Upstream timeout"}})
        except Exception as e:
            raise HTTPException(502, detail={"error": {"message": str(e)}})

    result = resp.json()

    # 计费
    usage = result.get("usage", {})
    inp  = usage.get("prompt_tokens", 0)
    out  = usage.get("completion_tokens", 0)
    cost = calc_cost(model, inp, out)
    if cost > 0:
        if not deduct(user["id"], cost):
            result.setdefault("warning", "余额不足，请联系管理员充值")
        else:
            log_usage(user["id"], model, inp, out, cost)

    return result


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [{"id": m, "object": "model", "owned_by": "relay"} for m in AVAILABLE_MODELS]
    }

# ==================== 用户接口 ====================
class CreateUserReq(BaseModel):
    username: Optional[str] = None

@app.post("/api/user/create")
async def create_user(req: CreateUserReq):
    uid = str(uuid.uuid4())
    key = generate_api_key()
    name = (req.username or f"user_{uid[:6]}").strip()
    conn = get_db()
    try:
        # 检查用户名是否已存在
        existing = conn.execute(
            "SELECT id FROM users WHERE username=?", (name,)
        ).fetchone()
        if existing:
            raise HTTPException(400, detail="用户名已被占用，请换一个名字")
        conn.execute(
            "INSERT INTO users(id,api_key,username,balance) VALUES(?,?,?,5)",
            (uid, key, name)
        )
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "api_key": key, "username": name, "balance": 5,
            "message": "新用户赠送5元试用额度"}

@app.get("/api/user/info")
async def user_info(authorization: str = Header(None)):
    user = auth(authorization)
    return {"username": user["username"], "balance": round(user["balance"], 4),
            "created_at": user["created_at"]}

@app.get("/api/user/usage")
async def user_usage(authorization: str = Header(None), limit: int = 20):
    user = auth(authorization)
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM usage_records WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user["id"], limit)
        ).fetchall()
    finally:
        conn.close()
    return {"records": [dict(r) for r in rows]}

# ==================== 管理员接口 ====================
class AdminLogin(BaseModel):
    username: str
    password: str

class RechargeReq(BaseModel):
    user_id: str
    amount: float

@app.post("/api/admin/login")
async def admin_login(req: AdminLogin):
    hashed = hashlib.sha256(req.password.encode()).hexdigest()
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM admins WHERE username=? AND password_hash=?",
            (req.username, hashed)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(401, detail="用户名或密码错误")
    token = hashlib.md5(f"{req.username}{time.time()}".encode()).hexdigest()
    return {"success": True, "token": token}

@app.get("/api/admin/users")
async def admin_users(page: int = 1, limit: int = 20, admin_token: str = Header(None)):
    if not admin_token:
        raise HTTPException(401, detail="需要管理员权限")
    offset = (page - 1) * limit
    conn = get_db()
    try:
        rows  = conn.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                             (limit, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()
    return {"users": [dict(r) for r in rows], "total": total}

@app.post("/api/admin/recharge")
async def admin_recharge(req: RechargeReq, admin_token: str = Header(None)):
    if not admin_token:
        raise HTTPException(401, detail="需要管理员权限")
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE users SET balance=balance+? WHERE id=?", (req.amount, req.user_id)
        )
        if cur.rowcount == 0:
            conn.close()
            raise HTTPException(404, detail="用户不存在")
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "message": f"充值 ¥{req.amount} 成功"}

@app.post("/api/admin/user/create")
async def admin_create_user(req: CreateUserReq, admin_token: str = Header(None)):
    if not admin_token:
        raise HTTPException(401, detail="需要管理员权限")
    uid = str(uuid.uuid4())
    key = generate_api_key()
    name = req.username or f"user_{uid[:6]}"
    conn = get_db()
    try:
        conn.execute("INSERT INTO users(id,api_key,username,balance) VALUES(?,?,?,0)",
                     (uid, key, name))
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "api_key": key, "username": name}

# ==================== 前端页面 ====================
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

def _read_template(name: str) -> str:
    path = os.path.join(TEMPLATES_DIR, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return "<h1>模板文件不存在</h1>"

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return _read_template("admin.html")

@app.get("/user", response_class=HTMLResponse)
async def user_page():
    return _read_template("user.html")

@app.get("/recharge", response_class=HTMLResponse)
async def recharge_page():
    return _read_template("recharge.html")

# ==================== 其他 ====================
@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat(),
            "upstream": UPSTREAM_BASE_URL}

@app.get("/", response_class=HTMLResponse)
async def root():
    return _read_template("index.html")

# ==================== 入口 ====================
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
