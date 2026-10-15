import os
import sys

def remove_mac_junk(target_dir):
    abs_path = os.path.abspath(target_dir)
    
    if not os.path.exists(abs_path):
        print(f"Error: Path '{abs_path}' does not exist.")
        return

    removed_count = 0
    freed_bytes = 0

    print(f"Scanning directory: {abs_path}\n")

    for root, _, files in os.walk(abs_path):
        for file in files:
            # Match .DS_Store, ._*, or files starting with ._
            if file == ".DS_Store" or file.startswith("._"):
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    removed_count += 1
                    freed_bytes += file_size
                    print(f"Removed: {file_path}")
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}")

    print("\n--- Summary ---")
    print(f"Files deleted: {removed_count}")
    print(f"Space freed:   {freed_bytes / 1024:.2f} KB")

if __name__ == "__main__":
    # Pass directory as a CLI argument or default to the current working directory
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    remove_mac_junk(directory)