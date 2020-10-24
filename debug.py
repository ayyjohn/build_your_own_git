import os
import zlib

for root, dirs, files in os.walk("./.git/objects"):
    print(root, dirs, files)
    for file in files:
        with open(root + os.sep + file, "rb") as f:
            data = zlib.decompress(f.read())
            if data.startswith(b"tree"):
                print(data)
                print("")


"""
b"tree 136\x00100644 hello.txt\x00;\x18\xe5\x12\xdb\xa7\x9eL\x83\x00\xdd\x08\xae\xb3\x7f\x8er\x8b\x8d\xad40000 swag\x00'vt\xe7\xe2\xfd\x86L\xbcr=&\x03\xa8@P*P;\xee40000 twerk\x00\xc7\x1f\xf5\xa7\x15\xfd\xecy\x82\xc3\x91\x1euI\x92C\x99\x96\xa3 100644 yeet.txt\x00\xa3oBX\x04\xf8\xb9)9 \xaawY\xdcv\x1cCw\xcb\xdc"
"""
