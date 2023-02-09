from datetime import datetime
import binascii
import hashlib
import os
import sys
import zlib


AUTHOR_NAME = "Author"
AUTHOR_EMAIL = "author@example.net"
COMMITER_NAME = AUTHOR_NAME
COMMITER_EMAIL = AUTHOR_EMAIL


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
            if ftype in (b"blob", b"commit"):
                print(contents.decode(), end="")
            elif ftype == b"tree":
                ls_tree(obj)
            else:
                print(f"error: object `{opt}' has unknown type {ftype}")
    elif opt[0] == '-':
        print(f"error: unknown switch `{opt}'")


def hash_contents(contents, obj_type="blob", write=False):
    if not contents:
        raise RuntimeError("fn hash_contents: Contents to hash required.")

    data = b'%s %d\x00' % (obj_type.encode(), len(contents)) + contents
    obj = hashlib.sha1(data).hexdigest()

    if write:
        with open(obj_path(obj, mknew=True), "wb") as f:
            f.write(zlib.compress(data))

    return obj


def hash_object(opts, obj_type="blob", write=False):
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

    if not path:
        raise RuntimeError("fn hash_object: Path required.")

    if not os.path.exists(path):
        sys.exit(f"fatal: could not open '{path}' for reading: No such file or directory")

    if os.path.isdir(path):
        sys.exit(f"fatal: Unable to hash {path}")

    with open(path, "rb") as f:
        contents = f.read()

    return hash_contents(contents, obj_type, write)


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

    return hash_contents(contents, "tree", True)


def commit_tree(opts):
    tree_sha = None
    parent_sha = None
    message = None
    skip_next = False

    # XXX: use getopt/argparse
    for i, opt in enumerate(opts):
        if skip_next:
            skip_next = False
            continue
        if opt == "-p":
            parent_sha = opts[i + 1]
            skip_next = True
        elif opt == "-m":
            message = opts[i + 1]
            skip_next = True
        elif opt[0] == "-":
            sys.exit(f"error: unknown switch `{opt}'")
        else:
            tree_sha = opt

    # lazy error handling
    _ = obj_path(tree_sha)
    _ = obj_path(parent_sha)

    now = datetime.now().astimezone()
    # "%s" is not portable; depends on system's strftime
    # timestamp = now.strftime("%s %z")
    timestamp = str(int(now.timestamp())) + now.strftime("%z")

    contents = f"tree {tree_sha}\nparent {parent_sha}\n"
    contents += f"author {AUTHOR_NAME} <{AUTHOR_EMAIL}> {timestamp}\n"
    contents += f"commiter {COMMITER_NAME} <{COMMITER_EMAIL}> {timestamp}\n"
    contents += f"\n{message}\n"
    contents = contents.encode()

    return hash_contents(contents, "commit", True)


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
    elif command == "commit-tree":
        if len(sys.argv) < 7:
            print("fatal: five arguments required")
            return
        print(commit_tree(sys.argv[2:]))
    else:
        raise sys.exit(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
