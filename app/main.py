import binascii
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
        with open(obj_path(obj), "rb") as f:
            data = zlib.decompress(f.read())
            ftlen, _, contents = data.partition(b'\x00')
            ftype, _ = ftlen.split()
            if ftype == b"blob":
                print(contents.decode(), end="")
            elif ftype == b"tree":
                ls_tree(obj)
            else:
                print(f"error: object `{opt}' has unknown type {ftype}")
    elif opt[0] == '-':
        print(f"error: unknown switch `{opt}'")


def hash_object(opts):
    write = False
    path = None

    if not isinstance(opts, list):
        opts = [opts]

    for opt in opts:
        if opt == "-w":
            write = True
        elif opt[0] == "-":
            sys.exit(f"error: unknown switch `{opt}'")
        else:
            path = opt

    if not os.path.exists(path):
        sys.exit(f"fatal: could not open '{path}' for reading: No such file or directory")

    if os.path.isdir(path):
        sys.exit(f"fatal: Unable to hash {path}")

    with open(path, "rb") as f:
        contents = f.read()

    data = (b'blob %d\x00' % len(contents)) + contents
    obj = hashlib.sha1(data).hexdigest()

    if write:
        with open(obj_path(obj, mknew=True), "wb") as blob:
            blob.write(zlib.compress(data))

    return obj


def ls_tree(opts):
    name_only = False
    obj = None

    if not isinstance(opts, list):
        opts = [opts]

    for opt in opts:
        if opt == "--name-only":
            name_only = True
        elif opt[0] == "-":
            sys.exit(f"error: unknown switch `{opt}'")
        else:
            obj = opt

    with open(obj_path(obj), "rb") as tree:
        data = zlib.decompress(tree.read())
        _, _, contents = data.partition(b'\x00')

    while contents:
        pre, _, contents = contents.partition(b'\x00')
        sha, contents = contents[:20], contents[20:]

        if name_only:
            pre = pre.split(b' ')
            line = pre[1]
        else:
            if pre[:1] == b'4':
                pre = b'0' + pre
                ftype = b"tree"
            else:
                ftype = b"blob"

            pre = pre.split(b' ')
            line = pre[0] + b' ' + ftype + b' ' + binascii.hexlify(sha) + b'\t' + pre[1]

        print(line.decode())


def write_tree(cwd="."):
    ls_cwd = os.listdir(cwd)
    contents = b''
    for entry in sorted(ls_cwd):
        if entry == ".git":
            continue
        path = os.path.join(cwd, entry)
        if os.path.isdir(path):
            mode = b"40000"
            obj = write_tree(path)
        else:  # isfile
            mode = b"100" + oct(os.stat(path).st_mode)[-3:].encode()
            obj = hash_object(path)

        obj = binascii.unhexlify(obj)
        contents += mode + b' ' + entry.encode() + b'\x00' + obj

    data = (b'tree %d\x00' % len(contents)) + contents
    obj = hashlib.sha1(data).hexdigest()

    with open(obj_path(obj, mknew=True), "wb") as tree:
        tree.write(zlib.compress(data))

    return obj


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
        if len(sys.argv) < 3:
            return
        print(hash_object(sys.argv[2:]))
    elif command == "ls-tree":
        if len(sys.argv) < 3:
            return
        ls_tree(sys.argv[2:])
    elif command == "write-tree":
        print(write_tree())
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
