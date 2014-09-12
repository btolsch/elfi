#!/usr/bin/env python3
import os
import shutil
import sys
from testfixtures import tempdir
import unittest
from unittest.mock import patch
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
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        self.initTempDir(d, dirtree)

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        for diff_set in diff_sets:
            self.assertEqual(len(diff_set), 0, 'Should be no difference between directories.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertNotCalled(cp, 'cp', "Identical directories shouldn't require a copy.")
        self.assertNotCalled(rm, 'rm', "Identical directories shouldn't require a remove.")

    def test_BackupEmpty(self):
        dirtrees = (
            ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                ('hello', (
                    'test.py', 'test.c', 'test',
                    ('world', (
                        'foo', 'banana'
                    ))
                )),
                'alpha', 'beta'
            ),
            ('hello.txt', ('hello', ('foo', 'bar'))),
        )
        for dirtree in dirtrees:
            self.backupEmptyTest(dirtree)

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def test_BaseEmpty(self, cp, rm, d):
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        self.touchTree(d, dirtree, relpath=self.backup)
        d.makedir(self.base)
        rel_path_set = elfi.build_backup_path_set(build_path_set_dirtree(dirtree))

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(len(diff_sets[0]), 0, 'Should be no additions to backup.')
        self.assertEqual(set(diff_sets[1]), rel_path_set, 'All paths in backup should be removed.')
        self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertRmCallsEqual(d, rm, rel_path_set)
        self.assertNotCalled(cp, 'cp', 'Should only remove when base is empty.')

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def test_ModifiedFiles(self, cp, rm, d):
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        modify_tree =    ('foo.txt',
                            ('hello', (
                                'test.c', 'test.py',
                                ('world', (
                                    'foo', 'banana'
                                ))
                            )),
                            'alpha'
                        )
        modify_paths = build_path_set_dirtree(modify_tree, exclude_dirs=True)

        self.initTempDir(d, dirtree)
        self.touchTree(d, modify_tree, relpath=self.base)

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(len(diff_sets[0]), 0, 'Should be no additions to backup.')
        self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals from backup.')
        self.assertEqual(set(diff_sets[2]), set(modify_paths), 'Extra/missing update')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertCpCallsEqual(d, cp, elfi.build_backup_path_set(modify_paths))
        self.assertNotCalled(rm, 'rm', 'Should only remove when base is missing files.')

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def test_NewFiles(self, cp, rm, d):
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        new_tree = ('baz.txt',
                        ('hello', (
                            'test.cpp', 'README',
                            ('world', (
                                'hand', 'python'
                            )),
                        )),
                    )
        new_paths = build_path_set_dirtree(new_tree, exclude_dirs=True)

        self.initTempDir(d, dirtree)
        self.touchTree(d, new_tree, relpath=self.base)
        rel_path_set = elfi.build_backup_path_set(new_paths)

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(set(diff_sets[0]), rel_path_set, 'All new paths should be added.')
        self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals from backup.')
        self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates to backup.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertCpCallsEqual(d, cp, rel_path_set)
        self.assertNotCalled(rm, 'rm', 'Should only remove when base is missing files.')

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def test_NewDirectories(self, cp, rm, d):
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        newdir_paths = ('foo/', 'foo/bar/', 'foo/bar/baz/', 'hello/blah/',
                        'hello/world/sub/')

        self.initTempDir(d, dirtree)
        rel_path_set = elfi.build_backup_path_set(newdir_paths)
        for dir in newdir_paths:
            d.makedir(os.path.join(self.base, dir))

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(set(diff_sets[0]), rel_path_set, 'Root of new directory trees should be considered new.')
        self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals in backup.')
        self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertCpCallsEqual(d, cp, rel_path_set)
        self.assertNotCalled(rm, 'rm', 'Should only copy to an empty backup.')

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def test_DeletedFiles(self, cp, rm, d):
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        delete_files = ('blah.txt', 'hello/test.c', 'hello/world/banana',
                        'alpha', 'hello/test.py')

        self.initTempDir(d, dirtree)
        rel_path_set = elfi.build_backup_path_set(delete_files)
        for path in rel_path_set:
            os.remove(d.getpath(os.path.join(self.base, path)))

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(len(diff_sets[0]), 0, 'Should be no additions to backup.')
        self.assertEqual(set(diff_sets[1]), rel_path_set, 'Extra/missing file removals in backup.')
        self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertRmCallsEqual(d, rm, rel_path_set)
        self.assertNotCalled(cp, 'cp', 'Should only remove from backup.')

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def test_DeletedDirectories(self, cp, rm, d):
        dirtree =    ('foo.txt', 'blah.txt', 'a.txt', 'a.c',
                        ('hello', (
                            'test.py', 'test.c', 'test',
                            ('world', (
                                'foo', 'banana'
                            ))
                        )),
                        'alpha', 'beta'
                    )
        delete_dirs = ('hello/', 'hello/world/')

        self.initTempDir(d, dirtree)
        rel_path_set = elfi.build_backup_path_set(delete_dirs)
        for path in rel_path_set:
            shutil.rmtree(d.getpath(os.path.join(self.base, path)))

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(len(diff_sets[0]), 0, 'Should be no additions to backup.')
        self.assertEqual(set(diff_sets[1]), rel_path_set, 'Extra/missing file removals in backup.')
        self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertRmCallsEqual(d, rm, rel_path_set)
        self.assertNotCalled(cp, 'cp', 'Should only remove from backup.')

    @patch('elfi.remove_from_backup', autospec=True)
    @patch('elfi.copy_to_backup', autospec=True)
    @tempdir()
    def backupEmptyTest(self, dirtree, cp, rm, d):
        d.makedir(self.backup)
        self.touchTree(d, dirtree, relpath=self.base)
        rel_path_set = elfi.build_backup_path_set(build_path_set_dirtree(dirtree))

        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        diff_sets = elfi.diff_walk(abs_base, abs_backup)
        self.assertEqual(set(diff_sets[0]), rel_path_set, 'All paths in base should be considered new.')
        self.assertEqual(len(diff_sets[1]), 0, 'Should be no removals in backup.')
        self.assertEqual(len(diff_sets[2]), 0, 'Should be no updates in backup.')

        elfi.do_backup(abs_base, abs_backup, *diff_sets)

        self.assertCpCallsEqual(d, cp, rel_path_set)
        self.assertNotCalled(rm, 'rm', 'Should only copy to an empty backup.')

    def initTempDir(self, d, dirtree):
        mtime = self.current_time_ns() - 1000000000
        make_dir_tree(d, dirtree, relpath=self.base, mtime=mtime)
        make_dir_tree(d, dirtree, relpath=self.backup, mtime=mtime)

    def touchTree(self, d, dirtree, relpath='', mtime=None):
        #dirtree represents a directory: (name, (contents, ...))
        for direntry in dirtree:
            if isinstance(direntry, str):
                d.write(os.path.join(relpath, direntry), b'')
                if mtime:
                    os.utime(d.getpath(os.path.join(relpath, direntry)), ns=(mtime, mtime))
            else:
                self.touchTree(d, direntry[1], os.path.join(relpath, direntry[0]), mtime)

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

    def assertCpCallsEqual(self, d, cp_mock, targets, reason='Extra/missing call to cp'):
        abs_base = d.getpath(self.base)
        abs_backup = d.getpath(self.backup)

        rel_args_set = {(abs_base, abs_backup, p) for p in targets}

        self.assertCallListsEqual(cp_mock, rel_args_set, reason)

    def assertRmCallsEqual(self, d, rm_mock, targets, reason='Extra/missing call to rm'):
        abs_backup = d.getpath(self.backup)

        rel_args_set = {(abs_backup, p) for p in targets}

        self.assertCallListsEqual(rm_mock, rel_args_set, reason)

    def assertCallListsEqual(self, mock_fn, target_list, reason='Extra/missing call'):
        #test that target_list is subset of call list
        for rel_args in target_list:
            mock_fn.assert_any_call(*rel_args)

        #test that call list is subset of target_list
        for args, kwargs in mock_fn.call_args_list:
            self.assertIn(args, target_list, reason)


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
