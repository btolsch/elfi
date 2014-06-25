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

		abs_base = d.getpath(self.base)
		abs_backup = d.getpath(self.backup)

		diff_sets = elfi.diff_walk(abs_base, abs_backup)
		for diff_set in diff_sets:
			self.assertEqual(len(diff_set), 0, 'Should be no difference between directories.')

		elfi.do_backup(abs_base, abs_backup, *diff_sets)

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
		self.backupEmptyTest(cp, rm, d, dirtree)

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

		abs_base = d.getpath(self.base)
		abs_backup = d.getpath(self.backup)

		rel_path_set = elfi.build_backup_path_set(build_path_set_dirtree(dirtree))
		rel_args_set = {(d.getpath(self.backup), p) for p in rel_path_set}

		diff_sets = elfi.diff_walk(abs_base, abs_backup)
		self.assertEqual(len(diff_sets[0]), 0, 'Should be no additions to backup.')
		self.assertEqual(set(diff_sets[1]), rel_path_set, 'All paths in backup should be removed.')
		self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

		elfi.do_backup(abs_base, abs_backup, *diff_sets)

		self.assertCallListsEqual(rm, rel_args_set, 'Extra call made to rm')
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
		self.assertEqual(len(diff_sets[0]), 0, 'Should be no additions to backup.')
		self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals from backup.')
		self.assertEqual(set(diff_sets[2]), set(modify_paths), 'Extra update or update missing.')

		elfi.do_backup(abs_base, abs_backup, *diff_sets)

		mod_args_set = {(abs_base, abs_backup, p)
			for p in elfi.build_backup_path_set(modify_paths)}

		self.assertCallListsEqual(cp, mod_args_set, 'Extra call to cp')
		self.assertNotCalled(rm, 'rm', 'Should only remove when base is missing files.')

	@patch('elfi.remove_from_backup', autospec=True)
	@patch('elfi.copy_to_backup', autospec=True)
	@tempdir()
	def test_NewFiles(self, cp, rm, d):
		dirtree =	('foo.txt', 'blah.txt', 'a.txt', 'a.c',
						('hello', (
							'test.py', 'test.c', 'test',
							('world', (
								'foo', 'banana'
							))
						)),
						'alpha', 'beta'
					)
		new_paths = ('baz.txt',
						os.path.join('hello', 'test.cpp'),
						os.path.join('hello', 'README'),
						os.path.join('hello', 'world', 'hand'),
						os.path.join('hello', 'world', 'python')
						)

		mtime = self.current_time_ns()
		make_dir_tree(d, dirtree, relpath=self.base, mtime=mtime)
		make_dir_tree(d, dirtree, relpath=self.backup, mtime=mtime)

		for p in new_paths:
			d.write(os.path.join(self.base, p), b'')

		abs_base = d.getpath(self.base)
		abs_backup = d.getpath(self.backup)

		rel_path_set = elfi.build_backup_path_set(new_paths)
		rel_args_set = {(abs_base, abs_backup, p) for p in rel_path_set}

		diff_sets = elfi.diff_walk(abs_base, abs_backup)
		self.assertEqual(set(diff_sets[0]), rel_path_set, 'All new paths should be added.')
		self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals from backup.')
		self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates to backup.')

		elfi.do_backup(abs_base, abs_backup, *diff_sets)

		self.assertCallListsEqual(cp, rel_args_set, 'Extra call to cp')
		self.assertNotCalled(rm, 'rm', 'Should only remove when base is missing files.')

	def test_NewDirectories(self):
		pass

	def test_DeletedFiles(self):
		pass

	def test_DeletedDirectories(self):
		pass

	@patch('elfi.remove_from_backup', autospec=True)
	@patch('elfi.copy_to_backup', autospec=True)
	@tempdir()
	def test_DirPrefixOfSiblingFile(self, cp, rm, d):
		dirtree = ('hello.txt', ('hello', ('foo', 'bar')))
		self.backupEmptyTest(cp, rm, d, dirtree)

	def backupEmptyTest(self, cp, rm, d, dirtree):
		d.makedir(self.backup)
		make_dir_tree(d, dirtree, relpath=self.base)

		abs_base = d.getpath(self.base)
		abs_backup = d.getpath(self.backup)

		rel_path_set = elfi.build_backup_path_set(build_path_set_dirtree(dirtree))
		rel_args_set = {(abs_base, abs_backup, p) for p in rel_path_set}

		diff_sets = elfi.diff_walk(abs_base, abs_backup)
		self.assertEqual(set(diff_sets[0]), rel_path_set, 'All paths in base should be considered new.')
		self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals in backup.')
		self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

		elfi.do_backup(abs_base, abs_backup, *diff_sets)

		self.assertCallListsEqual(cp, rel_args_set, 'Extra call made to cp')
		self.assertNotCalled(rm, 'rm', 'Should only copy to an empty backup.')


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

	def assertCallListsEqual(self, mock_fn, target_list, reason='Extra call'):
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
			),
			#no superceding
			(('hello/foo/foo.txt', 'hello/foo/bar.txt', 'hello/foo/baz.txt',
					'hello/bar/foo.txt', 'hello/world.txt'),
				set(('hello/foo/foo.txt', 'hello/foo/bar.txt',
					'hello/foo/baz.txt', 'hello/bar/foo.txt',
					'hello/world.txt'))
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
			),
			#no superceding
			(('hello/world.txt', 'hello/foo/foo.txt',
					'hello/foo/bar.txt', 'hello/foo/baz.txt',
					'hello/bar/foo.txt'),
				set(('hello/foo/foo.txt', 'hello/foo/bar.txt',
					'hello/foo/baz.txt', 'hello/bar/foo.txt',
					'hello/world.txt'))
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
			),
			#no superceding
			(('hello/world.txt', 'hello/foo/bar.txt',
					'hello/foo/foo.txt', 'hello/bar/foo.txt',
					'hello/foo/baz.txt'),
				set(('hello/foo/foo.txt', 'hello/foo/bar.txt',
					'hello/foo/baz.txt', 'hello/bar/foo.txt',
					'hello/world.txt'))
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
