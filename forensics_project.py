# mmcat file.dd x > partx.dd 
# should have no output on success; keep increasing x starting from x=0 until "Partition address is too large (maximum: ?)"
# fsstat all partitions "Cannot determine file system type" on failure
# looking for "File System Type: " and then read to the end of line

import subprocess
import re

############################
# LIST OF VARIABLES
############################
# var (type): description

# md5sum_str (str): image's hash value (MD5)
# sha1sum_str (str): image's hash value (SHA-1)
# mmls_str (str): "mmls practice1.dd" output
# num_of_parts (int): number of partitions
# data_parts (int list): IDs of data partitions
# partition_names (str list): list of data partition names (part2, part3 etc)
# partition_fs_types (str list): list of filesystem type
# fls_str (str list): list of fls -rd output
# filepath (str 2D list): list of filepath list (deleted files only)
# inode (str 2D list): list of inode list (deleted files only)
# istat (str 2D list): list of istat output list (deleted files only)
# creation date (str 2D list): list of file creation date (deleted files only)

image_file = "uploads/practice1.dd"

############################
# md5sum command/image's hash value (MD5) 
############################

try:
	cmd = 'md5sum ' + image_file
	result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
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
        partition_names.append(None)
        continue
    try:
        cmd = 'mmcat ' + image_file + ' ' + str(i) + ' > part' + str(i) + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        partition_names.append('part' + str(i))
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)
        break

#######################################
# FIGURE OUT FILE SYSTEM OF PARTITIONS
#######################################
partition_fs_types = []
for i in range(num_of_parts):
    if i not in data_parts:
        partition_fs_types.append(None)
        continue
    try:
        cmd = 'fsstat part' + str(i) + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
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
for i in range(num_of_parts):
    # goto next loop if file type is not determine
    if partition_fs_types[i] == None:
        continue

    try:
        # Create a new folder for each partition
        # Overwrite the directory if the directory exists
        cmd = 'mkdir -p ./' + partition_names[i]
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        # File Recovery
        cmd = 'tsk_recover -e ' + partition_names[i] + '.dd ./' + partition_names[i]
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)
	
#######################################
# List path for deleted files in FAT/NTFS system
#######################################

fls_str = []
filepath = []
for i in range(num_of_parts):
    # goto next loop if file type is not determine
    if partition_fs_types[i] == None:
        fls_str.append(None)
        filepath.append(None)
        continue
    elif "FAT" in partition_fs_types[i]:
    	fstype = "fat"
    elif "NTFS" in partition_fs_types[i]:
    	fstype = "ntfs"
    else:
        fls_str.append(None)
        filepath.append(None)
        continue  

    try:
        # fls -f ntfs part12.dd
        cmd = 'fls -f ' + fstype + ' -rd ' + partition_names[i] + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        fls_str.append(result.decode('utf-8'))
        # Extract filepath
        pattern = r'\t(.*?)\n'
        filepath.append(re.findall(pattern, fls_str[i])) 
        
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

print(f"filepath (str 2D list): \n{filepath}\n")	

#######################################
# Extract inode
#######################################

inode = []

for i in range(num_of_parts):
    if filepath[i] == None:
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
creationdate = [[] for _ in range(num_of_parts)]

for i in range(num_of_parts):
    if inode[i] == None:
    	istat.append(None)
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
            temp = result.decode('utf-8')
            pattern = r'Created:\t(.+)\n'
            temp = re.search(pattern, temp)
            creationdate[i].append(temp.group(1))
        except subprocess.CalledProcessError as e:
            print(e.returncode)
            print(e.output)
print(f"creationdate (str 2D list): \n{creationdate}\n")		





















	
