import hashlib
import os
import sys
import zlib


def obj_path(obj, mknew=False):
    path = f".git/objects/{obj[:2]}/{obj[2:]}"

    if mknew and not os.path.exists(f".git/objects/{obj[:2]}"):
        os.makedirs(f".git/objects/{obj[:2]}")
    elif not os.path.exists(path):
        sys.exit(f"fatal: Not a valid object name {obj}")

    return path


def cat_file(opt, obj):
    if opt == "-p":
        with open(obj_path(obj), "rb") as blob:
            data = zlib.decompress(blob.read())
            _, contents = data.split(b'\x00')
            print(contents.decode(), end="")
    elif opt[0] == '-':
        print(f"error: unknown switch `{opt}'")


def hash_object(opt, path):
    if opt == "-w":
        if not os.path.exists(path):
            sys.exit()

        with open(path, "rb") as f:
            contents = f.read()

        data = (b'blob %d\x00' % len(contents)) + contents
        obj = hashlib.sha1(data).hexdigest()

        with open(obj_path(obj, mknew=True), "wb") as blob:
            blob.write(zlib.compress(data))

        print(obj, end="")
    elif opt[0] == '-':
        print(f"error: unknown switch `{opt}'")


def ls_tree(opt, obj):
    if opt == "--name-only":
        with open(obj_path(obj), "rb") as tree:
            data = zlib.decompress(tree.read())
            _, _, contents = data.partition(b'\x00')

        entries_names = (x.split(b' ')[-1].decode() for x in
                         contents.split(b'\x00')[:-1])
        print(*entries_names, sep='\n')
    elif opt[0] == '-':
        print(f"error: unknown switch `{opt}'")


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
    elif command == "ls-tree":
        if len(sys.argv) != 4:
            print("fatal: two arguments required")
            return
        ls_tree(sys.argv[2], sys.argv[3])
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
