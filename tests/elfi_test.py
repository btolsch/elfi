import os
import sys
from testfixtures import tempdir
import unittest
from mock import patch
from time import time

#import module with relative path when invoked from command line
sys.path.insert(0, os.path.realpath(os.path.abspath(
					os.path.join('/'.join(sys.argv[0].split('/')[:-1]),
					'..' #relative path to elfi module
				))))
import elfi
sys.path.pop(0)

sys.path.insert(0, os.path.realpath(os.path.abspath(
					os.path.join('/'.join(sys.argv[0].split('/')[:-1]),
					'.' #relative path to maketree module
				))))
from maketree import makeDirTree, dirTreeMatches
sys.path.pop(0)

class TestElfi(unittest.TestCase):
	def setUp(self):
		self.base = 'base'
		self.backup = 'backup'
		self.current_time_ns = lambda: int(round(time() * 1000000000))

	def tearDown(self):
		pass

	@patch('elfi.remove_from_backup', autospec=True)
	@patch('elfi.copy_to_backup', autospec=True)
	@tempdir()
	def test_DirsIdentical(self, cp, rm, d):
		dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
						('hello', (
							'test.py', 'test.c', 'test',
							('world', (
								'foo', 'banana'
							))
						)),
						'alpha', 'beta'
					)
		mtime = self.current_time_ns()
		makeDirTree(d, dirtree, relpath=self.backup, mtime=mtime)
		makeDirTree(d, dirtree, relpath=self.base, mtime=mtime)

		print('dirs identical')
		elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		print('dirs identical')

		self.assertNotCalled(cp, 'cp',
					"Identical directories shouldn't require a copy.")
		self.assertNotCalled(rm, 'rm',
					"Identical directories shouldn't require a remove.")

	@tempdir()
	def test_BackupEmpty(self, d):
		dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
						('hello', (
							'test.py', 'test.c', 'test',
							('world', (
								'foo', 'banana'
							))
						)),
						'alpha', 'beta'
					)
		d.makedir(self.backup)
		makeDirTree(d, dirtree, relpath=self.base)

		print('backup empty')
		elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		print('backup empty')

		self.assertTrue(dirTreeMatches(d.getpath(self.base), dirtree))
		self.assertTrue(dirTreeMatches(d.getpath(self.backup), dirtree))

	@tempdir()
	def test_BaseEmpty(self, d):
		dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
						('hello', (
							'test.py', 'test.c', 'test',
							('world', (
								'foo', 'banana'
							))
						)),
						'alpha', 'beta'
					)
		makeDirTree(d, dirtree, relpath=self.backup)
		d.makedir(self.base)

		print('base empty')
		elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		print('base empty')

		self.assertTrue(dirTreeMatches(d.getpath(self.base), ()))
		self.assertTrue(dirTreeMatches(d.getpath(self.backup), ()))

	@tempdir()
	def test_ModifiedFiles(self, d):
		dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
						('hello', (
							'test.py', 'test.c', 'test',
							('world', (
								'foo', 'banana'
							))
						)),
						'alpha', 'beta'
					)
		modify_paths = ('foo.txt',
						os.path.join('hello', 'test.c'),
						os.path.join('hello', 'test.py'),
						os.path.join('hello', 'world', 'foo'),
						os.path.join('hello', 'world', 'banana')
						)

		mtime = self.current_time_ns()
		makeDirTree(d, dirtree, relpath=self.base, mtime=mtime)
		makeDirTree(d, dirtree, relpath=self.backup, mtime=mtime)

		mtime_plus = (mtime + 1000000000, mtime + 1000000000)

		for mod_path in modify_paths:
			os.utime(d.getpath(os.path.join(self.base, mod_path)), ns=mtime_plus)

		print('modified files')
		elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		print('modified files')

		self.assertTrue(dirTreeMatches(d.getpath(self.base), dirtree))
		self.assertTrue(dirTreeMatches(d.getpath(self.backup), dirtree))

		for basedir in (self.base, self.backup):
			for path, dirs, files in os.walk(d.getpath(basedir)):
				for direntry in dirs + files:
					direntry_path = os.path.join(path, direntry)
					direntry_mtime = int(os.path.getmtime(direntry_path))
					if os.path.join(path[len(d.getpath(basedir))+1:], direntry) in modify_paths:
						mtime_answer = int(mtime_plus[0] / 1000000000)
					else:
						mtime_answer = int(mtime / 1000000000)
					self.assertEqual(direntry_mtime, mtime_answer)

	def test_NewFiles(self):
		pass
		#self.assertTrue(False)

	def test_NewDirectories(self):
		pass
		#self.assertTrue(False)

	def test_DeletedFiles(self):
		pass
		#self.assertTrue(False)

	def test_DeletedDirectories(self):
		pass
		#self.assertTrue(False)

	def assertNotCalled(self, mock, mock_name, reason=''):
		if mock.called:
			error_msg = mock_name + ' called '
			error_msg += 'once' if mock.called == 1 else '{} times'
			error_msg += ', last with {}'
			if reason:
				error_msg += '. ' + reason
			if mock.called == 1:
				error_msg = error_msg.format(mock.call_args)
			else:
				error_msg = error_msg.format(mock.call_count, mock.call_args)
			raise AssertionError(error_msg)


if __name__ == '__main__':
	unittest.main()
