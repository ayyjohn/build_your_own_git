from collections import deque

import requests

STOP = "0000"

# curl -X GET -o - https://github.com/git/git.git/info/refs?service=git-upload-pack | head -n 5
# this one works if uncommented
discover_url = "https://github.com/ayyjohn/book_info.git/info/refs?service=git-upload-pack"
index_response = requests.get(discover_url).content.decode("utf-8").split("\n")
print(index_response)
print()

# objects start at 3rd line and go until '0000' is found
objects = index_response[2:]
advertised = set()
# common = set()
# want = set()
for i, line in enumerate(objects):
    if line == STOP:
        break
    object_hash, name = line.split()
    advertised.add(object_hash)

print(advertised)
print()


LINE_START = b"0032want "

repo_url = "https://github.com/ayyjohn/book_info.git/git-upload-pack"
main_hash = next(iter(advertised)).encode("utf-8")[4:]
headers = {"Content-type": "application/x-git-upload-pack-request"}
data = LINE_START + main_hash + b"\n"
data += b"0000"
data += b"0009done\n"
print(f"request body: {data}")
response = requests.post(url=repo_url, data=data, headers=headers)
split_resp = response.content.split(b"\n")
print(split_resp)
# print(packfile.decode("utf-8"))
