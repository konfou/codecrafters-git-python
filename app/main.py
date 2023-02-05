import hashlib
import os
import sys
import zlib


def cat_file(opt, obj):
    if opt == "-p":
        with open(f".git/objects/{obj[:2]}/{obj[2:]}", "rb") as blob:
            data = zlib.decompress(blob.read())
            _, contents = data.split(b'\x00')
            print(contents.decode(), end="")


def hash_object(opt, path):
    if opt == "-w":
        with open(path, "rb") as f:
            contents = f.read()

        data = (b'blob %d\x00' % len(contents)) + contents
        obj = hashlib.sha1(data).hexdigest()

        if not os.path.exists(f".git/objects/{obj[:2]}"):
            os.makedirs(f".git/objects/{obj[:2]}")

        with open(f".git/objects/{obj[:2]}/{obj[2:]}", "wb") as blob:
            blob.write(zlib.compress(data))

        print(obj, end="")


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")

    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/master\n")
        print("Initialized git directory")
    elif command == "cat-file":
        if len(sys.argv) != 4:
            print("fatal: two arguments required")
            return
        cat_file(sys.argv[2], sys.argv[3])
    elif command == "hash-object":
        if len(sys.argv) != 4:
            print("fatal: two arguments required")
            return
        hash_object(sys.argv[2], sys.argv[3])
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
