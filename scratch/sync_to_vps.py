import os
import paramiko
from scp import SCPClient

def progress(filename, size, sent):
    print(f"\rUploading {filename.decode() if isinstance(filename, bytes) else filename}: {sent}/{size} bytes ({(sent/size)*100:.1f}%)", end="")

def main():
    host = "103.1.236.14"
    port = 22
    username = "mlap"
    password = "110415@Xohii"
    remote_root = "/opt/fast-platform"
    
    print("📡 Establishing SSH connection to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username, password)
    
    # SFTP client
    sftp = ssh.open_sftp()
    
    # 1. Target files to sync
    files_to_sync = [
        "backend/database/models/auth.py",
        "backend/database/models/__init__.py",
        "backend/controllers/auth.py",
        "backend/services/oauth_service.py",
        "backend/services/viral_share_service.py",
        "backend/controllers/client/viral.py",
        "frontend/src/lib/components/storefront/product-detail/shared/ShareToUnlock.svelte",
        "frontend/src/lib/components/storefront/product-detail/shared/ShareToUnlockPromoMobile.svelte"
    ]
    
    print("\n🚀 Uploading core files...")
    for rel_path in files_to_sync:
        local_path = os.path.join("/home/lv/Desktop/fast-platform-core", rel_path)
        remote_path = os.path.join(remote_root, rel_path)
        
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_path)
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            print(f"Creating remote directory: {remote_dir}")
            # Recursively create remote directory if not exists
            parts = remote_dir.split('/')
            current = ""
            for part in parts:
                if not part:
                    continue
                current += "/" + part
                try:
                    sftp.stat(current)
                except FileNotFoundError:
                    sftp.mkdir(current)
        
        print(f"Syncing: {rel_path} -> {remote_path}")
        sftp.put(local_path, remote_path)
        print("Done!")

    # 2. Upload compiled frontend assets (dist folder)
    print("\n📦 Uploading compiled production frontend assets (frontend/dist)...")
    scp = SCPClient(ssh.get_transport())
    local_dist = "/home/lv/Desktop/fast-platform-core/frontend/dist"
    remote_dist = os.path.join(remote_root, "frontend/dist")
    
    # Remove existing remote dist folder first to avoid merge conflicts
    print("Cleaning remote frontend/dist folder...")
    ssh.exec_command(f"rm -rf {remote_dist}")
    
    print(f"Copying folder: {local_dist} -> {remote_dist}")
    scp.put(local_dist, recursive=True, remote_path=os.path.join(remote_root, "frontend"))
    
    # Close connections
    scp.close()
    sftp.close()
    ssh.close()
    print("\n\n✅ ALL FILES SYNCED SUCCESSFULLY TO REMOTE VPS!")

if __name__ == "__main__":
    main()
