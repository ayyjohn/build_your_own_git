import os
import sys
import zlib

NULL = b"\x00"
UTF8 = "utf-8"


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
        # format is `git catfile -p 0a5e5a61944bc3228ba609690585a9b52b1e31b7`
        # thus argv[2] will always be "-p" for now
        blob_sha = sys.argv[3]
        # first 2 chars are directory, rest is filename
        dirname, filename = blob_sha[:2], blob_sha[2:]
        with open(f".git/objects/{dirname}/{filename}", "rb") as f:
            file_contents = zlib.decompress(f.read())
            file_header, file_body = file_contents.split(NULL)
            decoded_file_header = decode(file_header)
            decoded_file_body = decode(file_body)
            print(decoded_file_body, end="")
    else:
        raise RuntimeError(f"Unknown command #{command}")


def decode(b):
    return b.decode(UTF8)


if __name__ == "__main__":
    main()
