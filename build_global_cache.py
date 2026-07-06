import sys
import os
import psutil
from memory.storage.extension_tree import ExtensionIndexTree

def main():
    tree = ExtensionIndexTree()
    cache_path = os.path.expanduser("~/.nexus_global_cache.json")
    
    roots_to_scan = []
    for p in psutil.disk_partitions():
        if 'fixed' in p.opts.lower() or p.fstype:
            roots_to_scan.append(p.mountpoint)
            
    print(f"Building Global Extension Cache across: {roots_to_scan}...")
    print(f"Saving to: {cache_path}")
    
    for scan_root in roots_to_scan:
        print(f"Scanning {scan_root}...")
        for root, dirs, files in os.walk(scan_root):
            # Prune Windows system and heavy hidden folders to speed up scanning
            dirs[:] = [d for d in dirs if d not in ('$Recycle.Bin', 'System Volume Information', 'Windows')]
            
            for d in dirs:
                if d == ".git":
                    tree.add_path(os.path.join(root, d))
            for f in files:
                tree.add_path(os.path.join(root, f))
                
    tree.save_to_disk(cache_path)
    print("Done!")

if __name__ == "__main__":
    main()
