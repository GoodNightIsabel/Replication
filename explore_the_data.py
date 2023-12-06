import pandas as pd
import subprocess
import os
'''
df = pd.DataFrame(pd.read_csv('./LOG6307E/replication/datasets/IST_OST.csv'))
files = list(df['file_'])
repos = set(file.split('/')[-4] for file in files)
print(len(repos))
exit()
'''

def get_folder_size(folder_path):
    total_size = 0

    # Walk through the directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)

    # Convert the size to a human-readable format (e.g., bytes, KB, MB, GB)
    return total_size

def get_pp_file_size(folder_path):
    total_size = 0
    # Walk through the directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            if '.pp' in filename or '.erb' in filename or '.ebb' in filename or '.yaml' in filename:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)

    # Convert the size to a human-readable format (e.g., bytes, KB, MB, GB)
    return total_size

# Specify the path to the folder you want to measure
folder_path = './LOG6307E/replication/repositories/Mirantis/puppet-ssh'

# Get and print the size of the folder
print()


# For all in mirantis
root = './LOG6307E/replication/repositories/Mirantis/'
for folder in os.listdir(root):
    folder_path = root+folder
    if get_folder_size(folder_path) == 0:
        continue
    print(folder, ':', get_pp_file_size(folder_path)/get_folder_size(folder_path))