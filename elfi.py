import os
import shutil
import sys

#TODO
# - logging instead of printing
# - tests
# - actually make directory changes
# - filters to exclude certain files
# - tar and compress option

def diff_walk(base_root, backup_root):
	#canonicalize root paths
	base_root = os.path.abspath(base_root)
	backup_root = os.path.abspath(backup_root)

	#fail if base directory doesn't exist
	if not os.path.exists(base_root):
		raise IOError('File not found: {}'.format(base_root))

	if not os.path.isdir(base_root):
		print('Warning: base path not a directory, changing to base directory')
		base_root = os.path.dirname(base_root)

	#create backup dir if it doesn't exist
	os.makedirs(backup_root, exist_ok=True)

	#initialize add/remove/update lists
	add_list = []
	remove_list = []
	update_list = []

	#walk base root to find difference between dir trees
	for base_path, dirs, files in os.walk(base_root):
		#get equivalent path in backup directory
		rel = get_rel_path(base_root, base_path)
		backup_path = os.path.join(backup_root, rel)

		if not os.path.exists(backup_path):
			add_backup_path(add_list, rel)
			continue

		backup_listing = os.listdir(backup_path)
		base_listing = dirs + files

		for direntry in files:
			if not direntry in backup_listing:
				add_backup_path(add_list, os.path.join(rel, direntry))

		for direntry in backup_listing:
			rel_direntry = os.path.join(rel, direntry)
			base_direntry = os.path.join(base_path, direntry)
			backup_direntry = os.path.join(backup_path, direntry)
			if not direntry in base_listing:
				add_backup_path(remove_list, rel_direntry)
			elif newer(base_direntry, backup_direntry):
				if not os.path.isdir(base_direntry):
					update_list.append(rel_direntry)
			elif newer(backup_direntry, base_direntry):
				print('Warning: backup file newer than original:')
				print('    {}'.format(os.path.join(rel, direntry)))

	print('To be added to backup:')
	for item in add_list:
		print('    {}'.format(item))
	print('To be removed from backup:')
	for item in remove_list:
		print('    {}'.format(item))
	print('To be updated in backup:')
	for item in update_list:
		print('    {}'.format(item))

	for item in add_list + update_list:
		base_path = os.path.join(base_root, item)
		if os.path.isdir(base_path):
			shutil.copytree(base_path, os.path.join(backup_root, item))
		else:
			shutil.copy2(base_path, os.path.join(backup_root, item))

	for item in remove_list:
		path = os.path.join(backup_root, item)
		if os.path.isfile(path):
			os.remove(path)
		elif os.path.isdir(path):
			shutil.rmtree(path)
		else:
			print('Warning: removing {} not supported.'.format(path))

def add_backup_path(list, path):
	for add_path in list:
		if path.startswith(os.path.join(add_path, '')):
			break
	else:
		list.append(path)

def get_rel_path(base, path):
	path = path[len(base):]
	if path.startswith('/'):
		path = path[1:]
	return path

def newer(path1, path2):
	return int(os.path.getmtime(path1)) > int(os.path.getmtime(path2))

def print_walk(basepath):

	for path, dirs, files in os.walk(basepath):
		path = path[len(basepath):] + '/'
		print(path)
		print('dirs:\t{}'.format(dirs))
		print('files:\t{}'.format(files))
		print()

if __name__ == "__main__":
	if len(sys.argv) != 3:
		print('usage: elfi.py base_path backup_path')
		exit(1)
	print('Walking with root {} ...'.format(sys.argv[1]))
	diff_walk(sys.argv[1], sys.argv[2])
	exit(0)
