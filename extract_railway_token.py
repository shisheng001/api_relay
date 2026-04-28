import base64
import os
import re

# Search for Railway session tokens in Edge's localStorage leveldb log files
leveldb_path = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data", "Default", "Local Storage", "leveldb")

print(f"Searching in: {leveldb_path}")

tokens_found = []

for filename in os.listdir(leveldb_path):
    if filename.endswith('.log') or filename.endswith('.ldb'):
        filepath = os.path.join(leveldb_path, filename)
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Look for base64-encoded tokens that look like Railway tokens
            # Pattern: starts with "Indr" (base64 of 'NWk')
            matches = re.finditer(b'([A-Za-z0-9+/]{40,}={0,2})', content)
            for m in matches:
                token = m.group(1).decode('ascii', errors='ignore')
                # Try to decode
                try:
                    decoded = base64.b64decode(token + '==')
                    # Check if it looks like JSON
                    if b'"session' in decoded or b'"token' in decoded or b'railway' in decoded.lower():
                        print(f"\nFound token in {filename}:")
                        print(f"  Encoded: {token[:50]}...")
                        print(f"  Decoded: {decoded[:200]}")
                        tokens_found.append((token, decoded))
                except:
                    pass
                    
            # Also look for the session ID directly
            if b'8f9831d3' in content:
                idx = content.index(b'8f9831d3')
                chunk = content[max(0,idx-20):idx+200]
                print(f"\nFound session 8f9831d3 in {filename}:")
                print(f"  Raw bytes: {chunk}")
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Try decoding the specific token we found
specific_token = "IndrX0xRN0EzRW5rX0RpMmQ2MUM3N3dNR0x5ZzhzMTQ2aEM3WFpxUWVVNDZtX2NsaWVudFNlc3Npb24i"
print(f"\nDecoding specific token:")
try:
    decoded = base64.b64decode(specific_token + '==')
    print(f"Decoded: {decoded}")
except Exception as e:
    print(f"Failed: {e}")
    # Try URL-safe base64
    try:
        import base64
        decoded = base64.urlsafe_b64decode(specific_token + '==')
        print(f"Decoded (urlsafe): {decoded}")
    except Exception as e2:
        print(f"Failed (urlsafe): {e2}")
