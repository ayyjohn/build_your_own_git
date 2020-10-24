import hashlib
import os
import sys
import time
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
        tree_sha = sys.argv[3]
        dir_name, file_name = get_dir_and_file_names_from_hash(tree_sha)
        with open(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}/{file_name}", "rb") as tree_file:
            contents = zlib.decompress(tree_file.read())
            # debug_print(contents)
            headers, body = contents.split(NULL, 1)
            files_info = parse_tree_body(body)
            for mode, name, sha in files_info:
                # debug_print(mode, name, sha)
                print(name)
    elif command == "write-tree":
        # format is `git write-tree`
        tree_hash = write_tree(ROOT_PATH, {})
        print(tree_hash)
    elif command == "commit-tree":
        # format is `./your_git.sh commit-tree <tree_sha> -p <commit_sha> -m <message>
        tree_sha, parent_commit_sha, message = sys.argv[2], sys.argv[4], sys.argv[6]
        commit_body = create_commit_body(tree_sha, parent_commit_sha, message)
        contents = b"commit " + encode(str(len(commit_body))) + NULL + encode(commit_body)
        commit_sha = hash_data(contents).hexdigest()
        dir_name, file_name = get_dir_and_file_names_from_hash(commit_sha)
        object_dir = Path(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}")
        object_dir.mkdir(exist_ok=True)
        with open(f"{ROOT_PATH}/{OBJECTS_DIR}/{dir_name}/{file_name}", "wb+") as commit_file:
            commit_file.write(zlib.compress(contents))
        print(commit_sha)
    else:
        raise RuntimeError(f"Unknown command #{command}")


def write_tree(current_path, tree_hashes):
    subdir, dirs, files = next(os.walk(current_path))
    entries = []
    for dir in dirs:
        if ".git" in dir:
            continue
        dir_path = subdir + os.sep + dir
        # recurse first if any subdirs exist
        write_tree(dir_path, tree_hashes)
        dir_mode = mode(dir_path)
        tree_hash = tree_hashes[dir_path]
        entry = (encode(str(dir_mode)), encode(dir), tree_hash)
        entries.append(entry)
    for file_name in files:
        file_path = subdir + os.sep + file_name
        blob_hash, compressed_data = hash_and_compress_file(file_path)
        file_mode = mode(file_path)
        entry = (encode(str(file_mode)), encode(file_name), blob_hash.digest())
        entries.append(entry)
    entries.sort(key=lambda x: x[1])  # sort entries by name
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


def parse_tree_body(body):
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


def create_commit_body(tree_sha, parent_sha, message):
    """
    example: (added my own newlines)
    b'commit 250\x00tree 82374f9c56b35a2d97aba4d79573fad1919a5db2\nparent 89e61fe19223c58bf848cbe4d420158520cf11da\n
    author Alec Johnson <alecjohnson55@gmail.com> 1603500811 -0700\ncommitter Alec Johnson <alecjohnson55@gmail.com> 1603500811 -0700\n\n
    switch back to just names\n'

    body is of the form
    tree {tree_sha}\nparent {parent_sha}\nauthor {author info}\ncommitter {committer info} {timestamp} {timezone?}\n\n{commit message}\n
    """
    now = int(time.time())
    # todo fix -0700?
    # todo is \n part of message or nah
    body = f"tree {tree_sha}\nparent {parent_sha}\nauthor Alec Johnson <alecjohnson55@gmail.com> {now} -0700\ncommitter Alec Johnson <alecjohnson55@gmail.com> {now} -0700\n\n{message}\n"
    return body


def mode(file_path):
    return oct(os.stat(file_path).st_mode)[2:]


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
