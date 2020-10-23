import hashlib
import os
import sys
import zlib
from pathlib import Path

GIT_DIR = ".git"
OBJECTS_DIR = f"{GIT_DIR}/objects"
REFS_DIR = f"{GIT_DIR}/refs"
HEAD_FILE = f"{GIT_DIR}/HEAD"

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
        dirname, filename = get_dir_and_file_names_from_hash(blob_hash)
        with open(f"{OBJECTS_DIR}/{dirname}/{filename}", "rb") as f:
            file_contents = zlib.decompress(f.read())
            file_header, file_body = file_contents.split(NULL)
            decoded_file_header = decode(file_header)
            decoded_file_body = decode(file_body)
            print(decoded_file_body, end="")
    elif command == "hash-object":
        # format is `git hash-object -w filename`
        # thus argv[2] will always be "-w" for now
        input_file_name = sys.argv[3]
        blob_hash = hash_file(input_file_name)
        dirname, output_file_name = get_dir_and_file_names_from_hash(blob_hash)

        object_dir = Path(f"{OBJECTS_DIR}/{dirname}")
        object_dir.mkdir(exist_ok=True)
        with open(f"{OBJECTS_DIR}/{dirname}/{output_file_name}", "wb") as blob:
            blob.write(zlib.compress(contents))
        print(blob_hash, end="")
    else:
        raise RuntimeError(f"Unknown command #{command}")


def decode(b):
    return b.decode(UTF8)


def hash_file(file_name):
    with open(file_name, "rb") as f:
        data = f.read()
        # format of file contents are `blob <filelength>\x00<filedata>`
        contents = b"blob " + str(len(data)).encode(UTF8) + NULL + data
        blob_hash = hash_data(contents)
    return blob_hash


def hash_data(data):
    sha = hashlib.sha1()
    sha.update(data)
    return sha.hexdigest()


def get_dir_and_file_names_from_hash(blob_hash):
    return blob_hash[:2], blob_hash[2:]


def create_git_dirs():
    objects = Path(OBJECTS_DIR)
    objects.mkdir(parents=True, exist_ok=True)
    refs = Path(REFS_DIR)
    refs.mkdir(exist_ok=True)


def create_head_file():
    with open(HEAD_FILE, "w") as f:
        f.write("ref: refs/heads/master\n")


if __name__ == "__main__":
    main()
