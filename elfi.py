#!/usr/bin/env python3
import os
import shutil
import sys
from itertools import filterfalse

#TODO
# - logging instead of printing
# - tests
# - actually make directory changes
# - filters to exclude certain files
# - tar and compress option

def diff_walk(base, backup):
	base = os.path.abspath(base)
	backup = os.path.abspath(backup)

	if not os.path.exists(base):
		raise IOError('File not found: {}'.format(base))

	if not os.path.isdir(base):
		print('Warning: base path not a directory, changing to base directory')
		base = os.path.dirname(base)

	os.makedirs(backup, exist_ok=True)

	add_list = []
	remove_list = []
	update_list = []

	#walk base root to find difference between dir trees
	for base_path, dirs, files in os.walk(base):
		rel_path = os.path.join(get_rel_path(base, base_path), '')
		backup_path = os.path.join(backup, rel_path)

		if not os.path.exists(backup_path):
			add_list.append(rel_path)
			continue

		backup_listing = os.listdir(backup_path)
		base_listing = dirs + files

		for direntry in files:
			if not direntry in backup_listing:
				add_list.append(os.path.join(rel_path, direntry))

		for direntry in backup_listing:
			rel_direntry = os.path.join(rel_path, direntry)
			base_direntry = os.path.join(base_path, direntry)
			backup_direntry = os.path.join(backup_path, direntry)
			if os.path.isdir(backup_direntry):
				rel_direntry = os.path.join(rel_direntry, '')

			if not direntry in base_listing:
				remove_list.append(rel_direntry)
			elif newer(base_direntry, backup_direntry):
				if not os.path.isdir(base_direntry):
					update_list.append(rel_direntry)
			elif newer(backup_direntry, base_direntry):
				print('Warning: backup file newer than original:')
				print('    {}'.format(os.path.join(rel_path, direntry)))

	add_set = build_backup_path_set(add_list)
	remove_set = build_backup_path_set(remove_list)
	update_set = build_backup_path_set(update_list)

	return (add_set, remove_set, update_set)

def do_backup(base, backup, add_set, remove_set, update_set):
	for item in add_set | update_set:
		base_path = os.path.join(base, item)
		copy_to_backup(base, backup, item)

	for item in remove_set:
		remove_from_backup(backup, item)

def build_backup_path_set(paths):
	"""Build a set of paths that excludes all files belew any directory.

	E.g. would exclude hello/world.txt if hello/ is in paths
	"""
	path_set = set(paths)
	for path in paths:
		exclude_subtree = set(filterfalse(lambda p: p.startswith(path), paths))
		exclude_subtree.add(path)
		path_set &= exclude_subtree
	return path_set

def get_rel_path(base, path):
	path = path[len(base):]
	if path.startswith(os.path.sep):
		path = path[1:]
	return path

#TODO symbolic link copying and testing
def copy_to_backup(base, backup, relpath):
	base_path = os.path.join(base, relpath)
	backup_path = os.path.join(backup, relpath)
	if os.path.isfile(base_path):
		shutil.copy2(base_path, backup_path)
	elif os.path.isdir(base_path):
		shutil.copytree(base_path, backup_path)
	else:
		print('Warning: copying {} not supported.'.format(base_path))

#TODO symbolic link removal and testing
def remove_from_backup(backup, relpath):
	backup_path = os.path.join(backup, relpath)
	if os.path.isfile(backup_path):
		os.remove(backup_path)
	elif os.path.isdir(backup_path) and not os.path.islink(backup_path):
		shutil.rmtree(backup_path)
	else:
		print('Warning: removing {} not supported.'.format(backup_path))

def newer(path1, path2):
	return int(os.path.getmtime(path1)) > int(os.path.getmtime(path2))

def print_diff_walk(add_set, remove_set, update_set):
	"""Prints the changes detected by diff_walk()."""
	print('To be added to backup:')
	for item in sorted(add_set):
		print('    {}'.format(item))
	print('To be removed from backup:')
	for item in sorted(remove_set):
		print('    {}'.format(item))
	print('To be updated in backup:')
	for item in sorted(update_set):
		print('    {}'.format(item))

def print_walk(base):
	"""Prints the result of walking starting at the path argument."""
	for path, dirs, files in os.walk(base):
		path = path[len(basepath):] + os.path.sep
		print(path)
		print('dirs:\t{}'.format(dirs))
		print('files:\t{}'.format(files))
		print()

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print('usage: elfi.py base_path backup_path')
		exit(1)
	base = sys.argv[1]
	backup = sys.argv[2]
	print_diff_walk(*diff_walk(base, backup))
	exit(0)
