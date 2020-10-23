import hashlib
import os
import sys
import zlib

NULL = b"\x00"
UTF8 = "utf-8"


def main():
    command = sys.argv[1]
    if command == "init":
        create_git_dirs()
        create_head_file()
        print("Initialized git directory")
    elif command == "cat-file":
        # format is `git catfile -p 0a5e5a61944bc3228ba609690585a9b52b1e31b7`
        # thus argv[2] will always be "-p" for now
        blob_hash = sys.argv[3]
        # first 2 chars are directory, rest is filename
        dirname, filename = blob_hash[:2], blob_hash[2:]
        with open(f".git/objects/{dirname}/{filename}", "rb") as f:
            file_contents = zlib.decompress(f.read())
            file_header, file_body = file_contents.split(NULL)
            decoded_file_header = decode(file_header)
            decoded_file_body = decode(file_body)
            print(decoded_file_body, end="")
    elif command == "hash-object":
        # format is `git hash-object -w filename`
        # thus argv[2] will always be "-w" for now
        file_name = sys.argv[3]
        with open(file_name, "rb") as f:
            data = f.read()
            contents = b"blob " + str(len(data)).encode(UTF8) + b"\x00" + data
            sha = hashlib.sha1()
            sha.update(contents)
            blob_hash = sha.hexdigest()
            dirname, filename = blob_hash[:2], blob_hash[2:]
            os.mkdir(f".git/objects/{dirname}")
            with open(f".git/objects/{dirname}/{filename}", "wb") as blob:
                blob.write(zlib.compress(contents))
            print(blob_hash, end="")
    else:
        raise RuntimeError(f"Unknown command #{command}")


def decode(b):
    return b.decode(UTF8)


def create_git_dirs():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")


def create_head_file():
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")


if __name__ == "__main__":
    main()
