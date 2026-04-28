import sqlite3
import os

# Edge cookies database
edge_path = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies")
print(f"Path: {edge_path}")
print(f"Exists: {os.path.exists(edge_path)}")

# Railway stores auth in localStorage, not cookies typically
# Let's check for railway in localStorage
localstorage_path = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Edge", "User Data", "Default", "Local Storage", "leveldb")
print(f"LevelDB path: {localstorage_path}")

# Just list files
if os.path.exists(localstorage_path):
    files = os.listdir(localstorage_path)
    print(f"Files count: {len(files)}")
    # Look for railway-related keys
    for f in files[:5]:
        print(f"  {f}")
