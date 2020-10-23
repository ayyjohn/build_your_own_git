import os
import sys
import zlib

NULL = b"\x00"


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
        # format is
        # git cat-file -p 0a5e5a61944bc3228ba609690585a9b52b1e31b7
        # argv[2] will always be "-p" for now
        blob_sha = sys.argv[3]
        # first 2 chars are directory
        dirname, filename = blob_sha[:2], blob_sha[2:]
        with open(f".git/objects/{dirname}/{filename}", "rb") as f:
            file_contents = zlib.decompress(f.read())
            file_header, file_body = file_contents.split(NULL)
            file_header = file_header.decode("utf-8")
            file_body = file_body.decode("utf-8")
            print(file_body, end="")

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
