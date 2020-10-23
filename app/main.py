import os
import sys
import zlib


def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/master\n")
        print("Initialized git directory")
    elif command == "cat-file":
        # argv[2] will always be "-p" for now
        blob_sha = sys.argv[3]
        # first 2 chars are directory
        dirname, filename = blob_sha[:2], blob_sha[2:]
        with open(f".git/objects/{dirname}/{filename}", "rb") as f:
            # git cat-file -p 0a5e5a61944bc3228ba609690585a9b52b1e31b7
            print(zlib.decompress(f.read()), end="")

        print("dumpty scooby donkey dumpty vanilla monkey", end="")
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
