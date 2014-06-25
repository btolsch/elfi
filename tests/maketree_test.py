import os
import sys
from testfixtures import tempdir
import unittest
from time import time

sys.path.insert(0, os.path.realpath(os.path.abspath(
					os.path.join('/'.join(sys.argv[0].split('/')[:-1]),
					'.' #relative path to maketree module
				))))
import maketree
sys.path.pop(0)

class TestMakeTree(unittest.TestCase):
	def setUp(self):
		self.dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
							('hello', (
								'test.py', 'test.c', 'test',
								('world', (
									'foo', 'banana'
								))
							)),
							'alpha', 'beta'
						)
		self.dirtree_paths = {'foo.txt', 'blah.txt', 'a.txt', 'a.c',
								'hello', 'hello/test.py', 'hello/test.c',
								'hello/test', 'hello/world', 'hello/world/foo',
								'hello/world/banana', 'alpha', 'beta'
							}
		pass

	def tearDown(self):
		pass

	@tempdir()
	def test_MakeDirTree(self, d):
		maketree.make_dir_tree(d, self.dirtree)
		self.assertTrue(maketree.dir_tree_matches(d.getpath('.'), self.dirtree))

	@tempdir()
	def test_MakeDirTreeMtime(self, d):
		base = 'base'
		backup = 'backup'
		mtime = int(round(time() * 1000000000))
		maketree.make_dir_tree(d, self.dirtree, relpath=backup, mtime=mtime)
		maketree.make_dir_tree(d, self.dirtree, relpath=base, mtime=mtime)

		for basedir in (base, backup):
			for path, dirs, files in os.walk(d.getpath(basedir)):
				for file in files:
					file_mtime = int(os.path.getmtime(os.path.join(path, file)))
					self.assertEqual(file_mtime, int(mtime / 1000000000))
				for dir in dirs:
					dir_mtime = int(os.path.getmtime(os.path.join(path, dir)))
					self.assertEqual(dir_mtime, int(mtime / 1000000000))
		

	def test_BuildPathSet(self):
		built_pathset = maketree.build_path_set_dirtree(self.dirtree)
		self.assertTrue(built_pathset == self.dirtree_paths)

	@tempdir()
	def test_BuildPathSetWalk(self, d):
		d.makedir('one/two/three')
		d.write('one/two/three/four.txt', b'')
		d.write('one/two/three.txt', b'')
		d.write('one/two.txt', b'')
		d.write('one.txt', b'')

		pathset =	{'one', 'one.txt', 'one/two', 'one/two.txt',
					'one/two/three', 'one/two/three.txt',
					'one/two/three/four.txt'
					}
		built_pathset = maketree.build_path_set_walk(d.getpath('.'))
		self.assertTrue(built_pathset == pathset)

	@tempdir()
	def test_DirTreeMatchesEmpty(self, d):
		self.assertTrue(maketree.dir_tree_matches(d.getpath('.'), ()))

if __name__ == "__main__":
	unittest.main()
