import os

#TODO need a way to make mtime's all the same
def makeDirTree(tempdir, dirtree, relpath='', mtime=None):
	#dirtree represents a directory: (name, (contents, ...))
	for direntry in dirtree:
		if isinstance(direntry, str):
			path = os.path.join(relpath, direntry)
			tempdir.write(path, b'')
			if mtime:
				os.utime(tempdir.getpath(path), ns=(mtime, mtime))
		else:
			makeDirTree(tempdir, direntry[1], os.path.join(relpath, direntry[0]))
			if mtime:
				os.utime(tempdir.getpath(os.path.join(relpath, direntry[0])), ns=(mtime, mtime))

def dirTreeMatches(path, dirtree):
	return buildPathSet(dirtree) == buildPathSetWalk(path)

def buildPathSet(dirtree, path=''):
	path_set = set()
	for direntry in dirtree:
		if isinstance(direntry, str):
			path_set.add(os.path.join(path, direntry))
		else:
			dirpath = os.path.join(path, direntry[0])
			path_set.add(dirpath)
			path_set = path_set | buildPathSet(direntry[1], dirpath)
	return path_set

def buildPathSetWalk(basepath):
	basepath = os.path.abspath(basepath) + '/'
	path_set = set()
	for path, dirs, files in os.walk(basepath):
		path = path[len(basepath):]
		for direntry in dirs + files:
			path_set.add(os.path.join(path, direntry))
	return path_set
