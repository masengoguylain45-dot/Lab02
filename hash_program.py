"""
Lab 02 - Step 4: Hashing Program
Name: Guylain Masengo
Student ID: 801284-376

A from-scratch command-line tool that:
  1. Generates a hash table (JSON) for every file in a chosen directory.
  2. Verifies a directory against a previously generated hash table,
     reporting valid / invalid / new / deleted files.
  Bonus: detects when a file has simply been renamed (same content,
  new filename) instead of reporting it as a delete + a new file.
"""

import hashlib
import json
import os
import sys

HASH_ALGORITHM = "sha256"
CHUNK_SIZE = 65536  # 64 KB, read in chunks so large files don't blow up memory


def hash_file(filepath):
    """Calculates the cryptographic hash of a single file's contents."""
    hasher = hashlib.new(HASH_ALGORITHM)
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def traverse_directory(directory):
    """
    Walks the given directory (recursively) and hashes every file found.
    Returns a dict mapping a relative file path -> its hash.
    Relative paths are used (instead of absolute paths) so the hash table
    stays valid even if the whole folder is later moved.
    """
    file_hashes = {}
    for root, _dirs, files in os.walk(directory):
        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, directory)
            # Normalize to forward slashes so the table looks the same on
            # Windows, macOS, and Linux.
            rel_path = rel_path.replace(os.sep, "/")
            try:
                file_hashes[rel_path] = hash_file(full_path)
            except (OSError, PermissionError) as e:
                print(f"  [!] Skipped {rel_path}: {e}")
    return file_hashes


def generate_table(directory, table_path="hash_table.json"):
    """
    Hashes every file in `directory`, then writes a JSON hash table to
    `table_path` containing the directory that was hashed and each file's
    relative path + hash.
    """
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory.")
        return

    print(f"Hashing files in: {directory}")
    file_hashes = traverse_directory(directory)

    table = {
        "directory": os.path.abspath(directory),
        "algorithm": HASH_ALGORITHM,
        "files": file_hashes,
    }

    with open(table_path, "w") as f:
        json.dump(table, f, indent=2, sort_keys=True)

    print(f"Hashed {len(file_hashes)} file(s).")
    print("Hash table generated")
    print(f"Saved to: {os.path.abspath(table_path)}")


def load_table(table_path="hash_table.json"):
    """Reads a previously generated hash table from disk."""
    if not os.path.isfile(table_path):
        print(f"Error: hash table '{table_path}' not found. Generate one first (option 1).")
        return None
    with open(table_path, "r") as f:
        return json.load(f)


def validate_hash(table_path="hash_table.json"):
    """
    Loads the stored hash table, re-hashes the directory it points to,
    and compares the results against the stored values.

    Reports, per file:
      - "<path> hash is valid"          -> unchanged
      - "<path> hash is invalid"        -> content changed
      - "<path> is a new file"          -> present now, not in old table
      - "<path> has been deleted"       -> present in old table, missing now

    BONUS: if a "deleted" file's old hash exactly matches a "new" file's
    hash, that pair is reported as a rename instead, and the table is
    updated in place so future verifications use the new filename.
    """
    table = load_table(table_path)
    if table is None:
        return

    directory = table["directory"]
    old_hashes = table["files"]

    if not os.path.isdir(directory):
        print(f"Error: original directory '{directory}' no longer exists.")
        return

    print(f"Verifying files in: {directory}")
    current_hashes = traverse_directory(directory)

    old_paths = set(old_hashes.keys())
    current_paths = set(current_hashes.keys())

    unchanged_or_modified = old_paths & current_paths
    deleted_paths = old_paths - current_paths
    new_paths = current_paths - old_paths

    # ---- BONUS: rename detection ----
    # A "deleted" file and a "new" file that share the exact same hash are
    # almost certainly the same file, just renamed (its content is
    # identical, only the path changed).
    renamed_pairs = []
    still_deleted = set(deleted_paths)
    still_new = set(new_paths)

    for old_path in deleted_paths:
        old_hash = old_hashes[old_path]
        match = next((p for p in still_new if current_hashes[p] == old_hash), None)
        if match:
            renamed_pairs.append((old_path, match))
            still_deleted.discard(old_path)
            still_new.discard(match)

    table_changed = False

    # Report unchanged / modified files
    for path in sorted(unchanged_or_modified):
        if old_hashes[path] == current_hashes[path]:
            print(f"{path} hash is valid")
        else:
            print(f"{path} hash is invalid")
            old_hashes[path] = current_hashes[path]  # keep table current
            table_changed = True

    # Report renames (bonus)
    for old_path, new_path in sorted(renamed_pairs):
        print(f"File name change detected, {old_path} has been renamed to {new_path}")
        del old_hashes[old_path]
        old_hashes[new_path] = current_hashes[new_path]
        table_changed = True

    # Report genuinely new files
    for path in sorted(still_new):
        print(f"{path} is a new file")
        old_hashes[path] = current_hashes[path]
        table_changed = True

    # Report genuinely deleted files
    for path in sorted(still_deleted):
        print(f"{path} has been deleted")
        del old_hashes[path]
        table_changed = True

    if table_changed:
        table["files"] = old_hashes
        with open(table_path, "w") as f:
            json.dump(table, f, indent=2, sort_keys=True)


def main():
    print("=" * 50)
    print(" Lab 02 - File Hashing Program")
    print("=" * 50)
    print("1. Generate a new hash table")
    print("2. Verify hashes against an existing table")
    choice = input("Choose an option (1 or 2): ").strip()

    if choice == "1":
        directory = input("Enter the directory path to hash: ").strip()
        generate_table(directory)
    elif choice == "2":
        table_path = input(
            "Enter hash table filename [press Enter for hash_table.json]: "
        ).strip() or "hash_table.json"
        validate_hash(table_path)
    else:
        print("Invalid choice. Please run the program again and enter 1 or 2.")
        sys.exit(1)


if __name__ == "__main__":
    main()
