#!/usr/bin/env python3
import os
import time
import subprocess

WATCH_DIR = "/media/lv/data/fast-platform-core"
EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', 'backups', 'logs', '.pytest_cache', '__pycache__'}

def get_file_mtimes():
    mtimes = {}
    for root, dirs, files in os.walk(WATCH_DIR):
        # Prune excluded directories in-place to avoid searching them
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            # Only ignore temp files, editor swap files, etc.
            if file.startswith('.#') or file.endswith('.swp') or file == '.DS_Store':
                continue
            path = os.path.join(root, file)
            try:
                mtimes[path] = os.path.getmtime(path)
            except OSError:
                pass
    return mtimes

def sync_to_vps():
    print("\n⚡ File change detected! Syncing to VPS...", flush=True)
    # Execute rsync directly
    cmd = [
        "rsync", "-avz",
        "--exclude", ".git/",
        "--exclude", "node_modules/",
        "--exclude", ".venv/",
        "--exclude", "backups/",
        "--exclude", ".env",
        "--exclude", "logs/",
        "--exclude", ".pytest_cache/",
        "-e", "ssh -o StrictHostKeyChecking=no",
        "./", "mlap@103.1.236.14:/opt/fast-platform/"
    ]
    try:
        subprocess.run(cmd, cwd=WATCH_DIR, check=True)
        print("✅ Sync complete!", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Sync failed: {e}", flush=True)

def main():
    print("👀 Watching for local file changes in {}...".format(WATCH_DIR), flush=True)
    print("Auto-syncing to VPS on save. Press Ctrl+C to stop.", flush=True)
    
    last_mtimes = get_file_mtimes()
    
    try:
        while True:
            time.sleep(1.0)
            current_mtimes = get_file_mtimes()
            
            # Check for changes, additions, or deletions
            changed = False
            for path, mtime in current_mtimes.items():
                if path not in last_mtimes or mtime > last_mtimes[path]:
                    print(f"📝 Modified: {os.path.relpath(path, WATCH_DIR)}", flush=True)
                    changed = True
            
            for path in last_mtimes:
                if path not in current_mtimes:
                    print(f"🗑️ Deleted: {os.path.relpath(path, WATCH_DIR)}", flush=True)
                    changed = True
            
            if changed:
                sync_to_vps()
                last_mtimes = current_mtimes
    except KeyboardInterrupt:
        print("\n👋 Stopped watching.", flush=True)

if __name__ == "__main__":
    main()
