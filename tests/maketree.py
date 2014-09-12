import os

def make_dir_tree(tempdir, dirtree, relpath='', mtime=None):
    #dirtree represents a directory: (name, (contents, ...))
    for direntry in dirtree:
        if isinstance(direntry, str):
            path = os.path.join(relpath, direntry)
            tempdir.write(path, b'')
            if mtime:
                os.utime(tempdir.getpath(path), ns=(mtime, mtime))
        else:
            make_dir_tree(tempdir, direntry[1], os.path.join(relpath, direntry[0]), mtime)
            if mtime:
                os.utime(tempdir.getpath(os.path.join(relpath, direntry[0])), ns=(mtime, mtime))

def dir_tree_matches(path, dirtree):
    return build_path_set_dirtree(dirtree) == build_path_set_walk(path)

def build_path_set_dirtree(dirtree, path='', exclude_dirs=False):
    path_set = set()
    for direntry in dirtree:
        if isinstance(direntry, str):
            path_set.add(os.path.join(path, direntry))
        else:
            dirpath = os.path.join(path, direntry[0], '')
            if not exclude_dirs:
                path_set.add(dirpath)
            path_set |= build_path_set_dirtree(direntry[1], dirpath, exclude_dirs=exclude_dirs)
    return path_set

def build_path_set_walk(basepath):
    basepath = os.path.abspath(basepath) + os.path.sep
    path_set = set()
    for path, dirs, files in os.walk(basepath):
        path = path[len(basepath):]
        path_set |= {os.path.join(path, dir, '') for dir in dirs}
        path_set |= {os.path.join(path, file) for file in files}
    return path_set
