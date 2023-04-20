# mmcat file.dd x > partx.dd 
# should have no output on success; keep increasing x starting from x=0 until "Partition address is too large (maximum: ?)"
# fsstat all partitions "Cannot determine file system type" on failure
# looking for "File System Type: " and then read to the end of line

import subprocess

image_file = "file.dd"
############################
# CARVE OUT ALL PARTITIONS
############################
num_partitions = 0
partition_names = []
while True:
    #result = subprocess.run(["mmcat", "file.dd", str(x), ">",  "part" + str(x) + ".dd"], capture_output=True)
    try:
        cmd = 'mmcat ' + image_file + ' ' + str(num_partitions) + ' > part' + str(num_partitions) + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        partition_names.append('part' + str(num_partitions))
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)
        break
    num_partitions += 1

#######################################
# FIGURE OUT FILE SYSTEM OF PARTITIONS
#######################################
partition_fs_types = []
for i in range(num_partitions + 1):
    try:
        cmd = 'fsstat part' + str(i) + '.dd'
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        substr = b'File System Type: '
        start_ind = result.find(substr) + len(substr)
        tmp_str = result[start_ind:]
        end_ind = tmp_str.find(b'\n')
        file_system_type = tmp_str[:end_ind]
        partition_fs_types.append(file_system_type)
    except subprocess.CalledProcessError as e:
        print(e.output)
        partition_fs_types.append(None)

print('partition names: ', partition_names)
print('partition_fs_types: ', partition_fs_types)