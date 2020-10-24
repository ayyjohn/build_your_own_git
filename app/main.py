import hashlib
import os
import sys
import zlib
from pathlib import Path

GIT_DIR = ".git"
ROOT_PATH = os.path.abspath(os.getcwd())
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
        # format is `git cat-file -p 0a5e5a61944bc3228ba609690585a9b52b1e31b7`
        # thus argv[2] will always be "-p" for now
        blob_hash = sys.argv[3]
        # first 2 chars are directory, rest is file_name
        dir_name, file_name = get_dir_and_file_names_from_hash(blob_hash)
        with open(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}/{file_name}", "rb") as f:
            file_contents = zlib.decompress(f.read())
            # debug_print(file_contents)
            file_header, file_body = file_contents.split(NULL)
            decoded_file_header = decode(file_header)
            decoded_file_body = decode(file_body)
            print(decoded_file_body, end="")
    elif command == "hash-object":
        # format is `git hash-object -w file_name`
        # thus argv[2] will always be "-w" for now
        input_file_name = sys.argv[3]
        blob_hash, compressed_data = hash_and_compress_file(input_file_name)
        dir_name, output_file_name = get_dir_and_file_names_from_hash(blob_hash.hexdigest())

        object_dir = Path(f"{OBJECTS_DIR}/{dir_name}")
        object_dir.mkdir(exist_ok=True)
        with open(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}/{output_file_name}", "wb") as blob:
            blob.write(compressed_data)
        print(blob_hash.hexdigest(), end="")
    elif command == "ls-tree":
        # format is `git ls-tree --name-only <tree_sha>`
        # thus argv[2] will always be "--name-only" for now
        """
        output should get just the names from this
        100644 blob c18dd8d83ceed1806b50b0aaa46beb7e335fff13    .gitignore
        100644 blob 4be0fbf52cf36629e048c5cb692d57231df07f14    README.md
        040000 tree 4742c33faa9e076e80313be7b4f3bfd42e5a60b9    app
        100644 blob a7343766b507bf56012c2bfbc9f0e1601013be6a    codecrafters.yml
        100755 blob 79eae6a5419dca2d5494200c12143638e9ecb393    your_git.sh

        """
        tree_sha = sys.argv[3]
        dir_name, file_name = get_dir_and_file_names_from_hash(tree_sha)
        with open(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}/{file_name}", "rb") as tree_file:
            contents = zlib.decompress(tree_file.read())
            # debug_print(contents)
            headers, body = contents.split(NULL, 1)
            file_info = parse_body(body)
            # sort by name
            for mode, name, sha in sorted(file_info, key=lambda x: x[1]):
                # debug_print(mode, name, sha)
                print(name)
    elif command == "write-tree":
        tree_hash = write_tree(ROOT_PATH, ROOT_PATH, {})
        print(tree_hash)
        # format is `git write-tree`
    else:
        raise RuntimeError(f"Unknown command #{command}")


def write_tree(current_path, root_path, tree_hashes):
    # let's start by assuming there's exactly one file in the current dir
    subdir, dirs, files = next(os.walk(current_path))
    entries = []
    for dir in dirs:
        if ".git" in dir:
            continue
        write_tree(subdir + os.sep + dir, root_path, tree_hashes)
        dir_mode = oct(os.stat(subdir + os.sep + dir).st_mode)[2:]
        tree_hash = tree_hashes[subdir + os.sep + dir]
        entry = (encode(str(dir_mode)), encode(dir), tree_hash)
        entries.append(entry)
    for file_name in files:
        file_path = subdir + os.sep + file_name
        blob_hash, compressed_data = hash_and_compress_file(file_path)
        file_mode = oct(os.stat(file_path).st_mode)[2:]
        entry = (encode(str(file_mode)), encode(file_name), blob_hash.digest())
        entries.append(entry)
    joined_entries = [mode + b" " + name + NULL + sha for mode, name, sha in entries]
    body = b"".join(joined_entries)
    content = b"tree " + encode(str(len(body))) + NULL + body
    tree_hash = hash_data(content)
    dir_name, file_name = get_dir_and_file_names_from_hash(tree_hash.hexdigest())
    object_dir = Path(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}")
    object_dir.mkdir(exist_ok=True)
    tree_hashes[subdir] = tree_hash.digest()
    # debug_print(content)
    with open(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}/{file_name}", "wb+") as tree_file:
        tree_file.write(zlib.compress(content))
    return tree_hash.hexdigest()


def parse_body(body):
    """
    body is of the form
    {mode} {name}\x00{hash}{mode} {name}\x00{hash}{mode} {name}\x00{hash}{mode}...
    where the hash is always 20 bytes
    """
    entries = []
    # debug_print(body)
    while body:
        first_space_index = body.index(b" ")
        first_null_index = body.index(NULL)
        mode = body[0:first_space_index]
        name = body[first_space_index + 1 : first_null_index]
        end_of_sha_index = first_null_index + 21
        sha = body[first_null_index:end_of_sha_index]
        entry = (decode(mode), decode(name), sha.hex())
        entries.append(entry)
        body = body[end_of_sha_index:]
    # debug_print(entries)
    return entries


def decode(b):
    return b.decode(UTF8)


def encode(s):
    return s.encode(UTF8)


def hash_and_compress_file(file_name):
    with open(file_name, "rb") as f:
        data = f.read()
        # format of file contents are `blob <filelength>\x00<filedata>`
        contents = b"blob " + str(len(data)).encode(UTF8) + NULL + data
        blob_hash = hash_data(contents)
    return blob_hash, zlib.compress(contents)


def hash_data(data):
    sha = hashlib.sha1()
    sha.update(data)
    return sha


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


def debug_print(x):
    print(x)


if __name__ == "__main__":
    main()
