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
from maketree import make_dir_tree, build_path_set_dirtree
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
		make_dir_tree(d, dirtree, relpath=self.backup, mtime=mtime)
		make_dir_tree(d, dirtree, relpath=self.base, mtime=mtime)

		diff_sets = elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		elfi.do_backup(d.getpath(self.base), d.getpath(self.backup), *diff_sets)

		self.assertNotCalled(cp, 'cp',
					"Identical directories shouldn't require a copy.")
		self.assertNotCalled(rm, 'rm',
					"Identical directories shouldn't require a remove.")

	@patch('elfi.remove_from_backup', autospec=True)
	@patch('elfi.copy_to_backup', autospec=True)
	@tempdir()
	def test_BackupEmpty(self, cp, rm, d):
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
		make_dir_tree(d, dirtree, relpath=self.base)

		diff_sets = elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		elfi.do_backup(d.getpath(self.base), d.getpath(self.backup), *diff_sets)

		rel_args_set = {(d.getpath(self.base),
						d.getpath(self.backup),
						p)
			for p in elfi.build_backup_path_set(build_path_set_dirtree(dirtree))}

		#test that rel_args_set is subset of call list
		for rel_args in rel_args_set:
			cp.assert_any_call(*rel_args)

		#test that call list is subset of rel_args_set
		for args, kwargs in cp.call_args_list:
			self.assertTrue(args in rel_args_set, 'Extra call made to cp')

		self.assertNotCalled(rm, 'rm', 'Should only copy to an empty backup.')

	@patch('elfi.remove_from_backup', autospec=True)
	@patch('elfi.copy_to_backup', autospec=True)
	@tempdir()
	def test_BaseEmpty(self, cp, rm, d):
		dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
						('hello', (
							'test.py', 'test.c', 'test',
							('world', (
								'foo', 'banana'
							))
						)),
						'alpha', 'beta'
					)
		make_dir_tree(d, dirtree, relpath=self.backup)
		d.makedir(self.base)

		diff_sets = elfi.diff_walk(d.getpath(self.base), d.getpath(self.backup))
		elfi.do_backup(d.getpath(self.base), d.getpath(self.backup), *diff_sets)

		rel_args_set = {(d.getpath(self.backup), p)
			for p in elfi.build_backup_path_set(build_path_set_dirtree(dirtree))}

		self.assertCallListEquals(rm, rel_args_set, 'Extra call made to rm')
		self.assertNotCalled(cp, 'cp', 'Should only remove when base is empty.')

	@patch('elfi.remove_from_backup', autospec=True)
	@patch('elfi.copy_to_backup', autospec=True)
	@tempdir()
	def test_ModifiedFiles(self, cp, rm, d):
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
		make_dir_tree(d, dirtree, relpath=self.base, mtime=mtime)
		make_dir_tree(d, dirtree, relpath=self.backup, mtime=mtime)

		mtime_plus = (mtime + 1000000000, mtime + 1000000000)

		for mod_path in modify_paths:
			os.utime(d.getpath(os.path.join(self.base, mod_path)), ns=mtime_plus)

		abs_base = d.getpath(self.base)
		abs_backup = d.getpath(self.backup)

		diff_sets = elfi.diff_walk(abs_base, abs_backup)
		elfi.do_backup(abs_base, abs_backup, *diff_sets)

		mod_args_set = {(abs_base, abs_backup, p)
			for p in elfi.build_backup_path_set(modify_paths)}

		self.assertCallListEquals(cp, mod_args_set, 'Extra call to cp')
		self.assertNotCalled(rm, 'rm', 'Should only remove when base is missing files.')

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

	def assertNotCalled(self, mock_fn, mock_name, reason=''):
		if mock_fn.called:
			error_msg = mock_name + ' called '
			error_msg += 'once' if mock_fn.called == 1 else '{} times'
			error_msg += ', last with {}'
			if reason:
				error_msg += '. ' + reason
			if mock.called == 1:
				error_msg = error_msg.format(mock_fn.call_args)
			else:
				error_msg = error_msg.format(mock_fn.call_count, mock_fn.call_args)
			raise AssertionError(error_msg)

	def assertCallListEquals(self, mock_fn, target_list, reason='Extra call'):
		#test that target_list is subset of call list
		for rel_args in target_list:
			mock_fn.assert_any_call(*rel_args)

		#test that call list is subset of target_list
		for args, kwargs in mock_fn.call_args_list:
			self.assertTrue(args in target_list, reason)


class TestPathSet(unittest.TestCase):
	def setUp(self):
		self.depth_first_paths = (
			#dir supercedes contents and single deep file
			(('hello/world/foo.txt', 'hello/world/bar.txt',
					'hello/world/', 'hello/foo/bar.txt'),
				set(('hello/world/', 'hello/foo/bar.txt'))
			),
			#dir with similar name to file
			(('hello/foo/bar.txt', 'hello/foo/', 'hello/foo.txt'),
				set(('hello/foo/', 'hello/foo.txt'))
			)
		)

		self.breadth_first_paths = (
			#dir supercedes context and single deep file
			(('hello/world/', 'hello/world/bar.txt', 'hello/world/foo.txt',
					'hello/foo/bar.txt'),
				set(('hello/world/', 'hello/foo/bar.txt'))
			),
			#dir with similar name to file
			(('hello/foo/', 'hello/foo/bar.txt', 'hello/foo.txt'),
				set(('hello/foo/', 'hello/foo.txt'))
			)
		)

		self.mixed_paths = (
			#dir supercedes context and single deep file
			(('hello/world/bar.txt', 'hello/world/', 'hello/foo/bar.txt',
					'hello/world/foo.txt'),
				set(('hello/world/', 'hello/foo/bar.txt'))
			),
			#dir with similar name to file
			(('hello/foo/', 'hello/foo.txt', 'hello/foo/bar.txt'), 
				set(('hello/foo/', 'hello/foo.txt'))
			)
		)

	def tearDown(self):
		pass

	def test_DepthFirstOrderBuild(self):
		for paths, answer in self.depth_first_paths:
			path_set = elfi.build_backup_path_set(paths)
			self.assertEqual(path_set, answer)

	def test_DepthFirstOrderIncremental(self):
		pass

	def test_BreadthFirstOrderBuild(self):
		for paths, answer in self.breadth_first_paths:
			path_set = elfi.build_backup_path_set(paths)
			self.assertEqual(path_set, answer)

	def test_BreadthFirstOrderIncremental(self):
		pass

	def test_MixedOrderBuild(self):
		for paths, answer in self.mixed_paths:
			path_set = elfi.build_backup_path_set(paths)
			self.assertEqual(path_set, answer)

	def test_MixedOrderIncremental(self):
		pass

if __name__ == '__main__':
	unittest.main()
