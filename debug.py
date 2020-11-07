import os
import zlib

for root, dirs, files in os.walk("./.git/objects"):
    print(root, dirs, files)
    for file in files:
        with open(root + os.sep + file, "rb") as f:
            data = zlib.decompress(f.read())
            if data.startswith(b"commit"):
                print(data)
                print("")

