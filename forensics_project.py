# mmcat file.dd x > partx.dd 
# should have no output on success; keep increasing x starting from x=0 until "Partition address is too large (maximum: ?)"
# fsstat all partitions "Cannot determine file system type" on failure
# looking for "File System Type: " and then read to the end of line

import subprocess
import re
import json
import sys
from datetime import datetime
import pytz
import os

############################
# LIST OF VARIABLES
############################
# var (type): description

# commands (str): list of all successful commands
# md5sum_str (str): image's hash value (MD5)
# sha1sum_str (str): image's hash value (SHA-1)
# mmls_str (str): "mmls practice1.dd" output
# num_of_parts (int): number of partitions
# data_parts (int list): IDs of data partitions
# partition_names (str list): list of data partition names (part2, part3 etc)
# partition_fs_types (str list): list of filesystem type
# fls_str (str list): list of fls -rd output
# deleted_filepath (str 2D list): list of deleted_filepath list (deleted files only)
# inode (str 2D list): list of inode list (deleted files only)
# istat (str 2D list): list of istat output list (deleted files only)
# creationdate (str 2D list): list of file creation date (deleted files only)

image_file_name = sys.argv[1]
image_file = "uploads/" + image_file_name
commands = []

############################
# md5sum command/image's hash value (MD5) 
############################

try:
	cmd = 'md5sum ' + image_file
	result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
	commands.append(cmd)
	md5sum_str = result.decode('utf-8')
	md5sum_str = md5sum_str.split()[0]
	print(f"md5sum_str: \n{md5sum_str}\n")
except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

############################
# sha1sum command/image's hash value (SHA-1) 
############################

try:
	cmd = 'sha1sum ' + image_file
	result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
	sha1sum_str = result.decode('utf-8')
	sha1sum_str = sha1sum_str.split()[0]
	commands.append(cmd)
	print(f"sha1sum_str: \n{sha1sum_str}\n")
except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

############################
# mmls command
############################

try:
	cmd = 'mmls ' + image_file
	result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
	commands.append(cmd)
except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)


# count the number of partitions
# the number of '\n' in mmls_result - 5
mmls_str = result.decode('utf-8')
num_of_parts = mmls_str.count('\n') - 5
print(f"num_of_parts: \n{num_of_parts}\n")

############################
# find data partitions
############################

# find :000, :001 etc.
pattern = re.compile(r":\d+")
matches = pattern.finditer(mmls_str)

# store their positions to the list "positions"
positions = [match.start() for match in matches]

# get IDs for data partitions
data_parts = []
index = 0
for pos in positions:
	substr = mmls_str[(pos - 9):(pos - 6)]
	data_parts.append(int(substr))
	index += 1

print(f"data_parts: \n{data_parts}\n")

############################
# CARVE OUT data PARTITIONS only
############################

partition_names = []
for i in range(num_of_parts):
    if i not in data_parts:
        continue
    try:
        cmd = 'mmcat ' + image_file + ' ' + str(i) + ' > part' + str(i) + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        commands.append(cmd)
        partition_names.append('part' + str(i))
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)
        break

partition_hashes = []
for i in range(len(partition_names)):
    try:
        cmd = 'md5sum ' + partition_names[i] + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        commands.append(cmd)
        md5sum_str = result.decode('utf-8')
        md5sum_str = md5sum_str.split()[0]
        partition_hashes.append(md5sum_str)
    except subprocess.CalledProcessError as e:
            print(e.returncode)
            print(e.output)
#######################################
# FIGURE OUT FILE SYSTEM OF PARTITIONS
#######################################
partition_fs_types = []
for i in data_parts:
    try:
        cmd = 'fsstat part' + str(i) + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        commands.append(cmd)
        result_str = result.decode('utf-8')
        substr = 'File System Type: '
        start_ind = result_str.find(substr) + len(substr)
        tmp_str = result_str[start_ind:]
        end_ind = tmp_str.find('\n')
        file_system_type = tmp_str[:end_ind]
        partition_fs_types.append(file_system_type)
    except subprocess.CalledProcessError as e:
        print(e.output)
        partition_fs_types.append(None)

print(f"partition_names: \n{partition_names}\n")
print(f"partition_fs_types: \n{partition_fs_types}\n")

#######################################
# File Recovery
#######################################
for i in range(len(data_parts)):
    # goto next loop if file type is not determine
    if partition_fs_types[i] == None:
        continue

    try:
        # Create a new folder for each partition
        # Overwrite the directory if the directory exists
        cmd = 'mkdir -p ./' + partition_names[i]
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        commands.append(cmd)
        # File Recovery
        cmd = 'tsk_recover -e ' + partition_names[i] + '.dd ./' + partition_names[i]
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        commands.append(cmd)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)
	
#######################################
# List path for deleted files in FAT/NTFS system
#######################################

fls_str = []
deleted_filepath = []
for i in range(len(data_parts)):
    # goto next loop if file type is not determine
    if partition_fs_types[i] == None:
        fls_str.append(None)
        deleted_filepath.append(None)
        continue
    elif "FAT" in partition_fs_types[i]:
    	fstype = "fat"
    elif "NTFS" in partition_fs_types[i]:
    	fstype = "ntfs"
    else:
        fls_str.append(None)
        deleted_filepath.append(None)
        continue  

    try:
        # fls -f ntfs part12.dd
        cmd = 'fls -f ' + fstype + ' -rd ' + partition_names[i] + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        commands.append(cmd)
        fls_str.append(result.decode('utf-8'))
        # Extract deleted_filepath
        pattern = r'\t(.*?)\n'
        deleted_filepath.append(re.findall(pattern, fls_str[i]))
        
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

print(f"deleted_filepath (str 2D list): \n{deleted_filepath}\n")

#######################################
# Extract inode
#######################################

inode = []

for i in range(len(data_parts)):
    if deleted_filepath[i] == None:
        inode.append(None)
        continue
    else:
        pattern = r'\s*\s(\d+)(?::|-)'
        inode.append(re.findall(pattern, fls_str[i]))
print(f"inode (str 2D list): \n{inode}\n")	

#######################################
# Get creation date for deleted files
#######################################

istat = []
creationdate = [[] for _ in range(len(data_parts))]

for i in range(len(data_parts)):
    if inode[i] == None:
    	istat.append(None)
    	creationdate[i] = None
    	continue
    elif "FAT" in partition_fs_types[i]:
    	fstype = "fat"
    elif "NTFS" in partition_fs_types[i]:
    	fstype = "ntfs"
    	    
    for j in inode[i]:
        try:
	#  istat -f ntfs part12.dd 241
            cmd = 'istat -f ' + fstype + ' ' + partition_names[i] + '.dd ' + j
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            commands.append(cmd)
            temp = result.decode('utf-8')
            pattern = r'Created:\t(.+)\n'
            temp = re.search(pattern, temp)
            creationdate[i].append(temp.group(1))
        except subprocess.CalledProcessError as e:
            print(e.returncode)
            print(e.output)
print(f"creationdate (str 2D list): \n{creationdate}\n")	

#######################################
# Get hash for deleted files
#######################################

# hashdeletedf = [[] for _ in range(len(data_parts))]
# md5sumtmp = []

# for i in range(len(data_parts)):
#     if partition_fs_types[i] == None:
#         hashdeletedf.append(None)
#     elif "FAT" not in partition_fs_types[i] and "NTFS" not in partition_fs_types[i]:
#     	hashdeletedf.append(None)
#     	continue
#     else:
#         for j in deleted_filepath[i]:
#             try:
#                 print(f"INDEX{i}{partition_names[i]}{j}")
#                 cmd = 'md5sum ./' + partition_names[i] + '/' + j
#                 result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
#                 md5sum_str = result.decode('utf-8')
#                 md5sum_str = md5sum_str.split()[0]
#                 hashdeletedf[i].append(md5sum_str)
#             except subprocess.CalledProcessError as e:
#                 print(e.returncode)
#                 print(e.output)

# print(f"hashdeletedf (str 2D list): \n{hashdeletedf}\n")


print(f"*** RESULTS ***\n")
print(f"md5sum_str: \n{md5sum_str}\n")
print(f"sha1sum_str: \n{sha1sum_str}\n")
print(f"num_of_parts: \n{num_of_parts}\n")
print(f"data_parts: \n{data_parts}\n")
print(f"partition_names: \n{partition_names}\n")
print(f"partition_fs_types: \n{partition_fs_types}\n")
print(f"deleted_filepath (str 2D list): \n{deleted_filepath}\n")
print(f"inode (str 2D list): \n{inode}\n")	
print(f"creationdate (str 2D list): \n{creationdate}\n")
print(f"successful commands:\n {commands}\n")	

# print('creationdate: ', len(creationdate), len(creationdate[3]))
# print('hashes: ', len(hashdeletedf), len(hashdeletedf[3]))

now = datetime.now()
dt_us_eastern = datetime.now(pytz.timezone('America/New_York'))
dt_string = dt_us_eastern.strftime("%m/%d/%Y %H:%M:%S")

#######################################
# Output information to json file
#######################################
def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir\
(path)]
    else:
        d['type'] = "file"
    return d

report = {}
report['time'] = dt_string
report['name'] = image_file_name
report['hash'] = md5sum_str
partitions = []
for i in range(len(data_parts)):
    partitions_obj = {}
    partitions_obj['name'] = partition_names[i]
    partitions_obj['fileSystem'] = partition_fs_types[i]
    partitions_obj['hash'] = partition_hashes[i]
    if partition_fs_types[i] is not None:
        partitions_obj['tskRecover'] = path_to_dict(partition_names[i])
    if partition_fs_types[i] is not None and deleted_filepath[i] is not None:
        deleted_files_arr = []
        for j in range(len(deleted_filepath[i])):
            deleted_files_obj = {}
            deleted_files_obj['name'] = deleted_filepath[i][j]
            # deleted_files_obj['hash'] = hashdeletedf[i][j] # TODO: get deleted_hashes
            deleted_files_obj['creationDate'] = creationdate[i][j]
            deleted_files_arr.append(deleted_files_obj)
        partitions_obj['deletedFiles'] = deleted_files_arr
    partitions.append(partitions_obj)
report['partitions'] = partitions
report['commands'] = commands

with open('report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=4)










	
