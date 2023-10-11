from bs4 import BeautifulSoup
import requests
import os
import csv
import pandas as pd
from datetime import datetime, date
from git import Repo, log
import json
from tqdm import tqdm
import zipfile
import shutil
import time
from http.client import IncompleteRead
import logging
logging.basicConfig(
    filename='mozilla_logging.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Function for getting the urls
def get_link(current_page, base_url):
    r = requests.get(current_page)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Get all the blocks & next page
    lists = soup.findAll('a', class_="name")
    url_lists = [base_url+list['href'] for list in lists]
    
    return url_lists

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

    return total_size

base_url = 'https://hg.mozilla.org/'
mozilla_path = '../mozilla_repos.txt'
mozilla_repositories = []

# Get the repository layout
r = requests.get(base_url)
soup = BeautifulSoup(r.text, 'html.parser')
tables = soup.findAll('table')
repository_layout = [t.text for t in tables[1].findAll('a')]


# If the link file does not exist, parse all the mercurial repos
if not os.path.exists(mozilla_path):
    for mercurial in repository_layout:
        if mercurial == '/':
            current_url = base_url
        else:
            current_url = base_url+mercurial+'/'
        logging.info('Scraping page %s, please be patient...'%mercurial)
        r = requests.get(current_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.findAll('table')
        repositories = [current_url+t.text.strip() for t in tables[0].findAll('b')]
        mozilla_repositories.extend(repositories)
        # Sleep for a while
        time.sleep(3)
        logging.info("Sleep for a while so that they can't see me")
    with open(r'%s'%mozilla_path, 'w') as fp:
        fp.write('\n'.join(mozilla_repositories))
# Else we load from file directly
else:
    with open(r'%s'%mozilla_path, 'r') as fp:
        logging.info("Nice, we have all the repositories!")
        for line in fp:
            mozilla_repositories.append(line.strip())
            
# Iterate through all the repositories
# sleep for a while after 10 repos checked
count = 1
flag = False
for repo in mozilla_repositories:
    print(repo.split('/')[-1])
    if repo.split('/')[-1] == 'mozilla-esr68':
        flag = True
        continue
    if flag == False:
        continue
    # Download the repository
    file_url = repo+"/archive/tip.zip"
    try:
        response = requests.get(file_url)
    except IncompleteRead:
        # Oh well, reconnect and keep trucking
        continue
    # This is a temporary path for the zip file
    temp_zip = "../repositories/Mozilla/%s/tip.zip"%(repo.split('/')[-2])
    # Folder for saving
    extracted_dir = "../repositories/Mozilla/%s/"%(repo.split('/')[-2])
    # Check the folder
    if not os.path.exists(extracted_dir):
        os.mkdir(extracted_dir)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Open the local file in binary write mode and write the response content to it
        with open(temp_zip, "wb") as local_file:
            local_file.write(response.content)
    else:
        logging.warning(f"Failed to download file. Status code: {response.status_code}")

    # Open the ZIP file for reading
    with zipfile.ZipFile(temp_zip, "r") as zip_ref:
        # Extract all the contents to the specified directory
        zip_ref.extractall(extracted_dir)
        
    # Delete the original zip file
    os.remove(temp_zip)
    
    # Find the new folder
    mozilla_folders = os.listdir(extracted_dir)
    sorted_files = sorted(mozilla_folders, key=lambda x: os.path.getmtime(os.path.join(extracted_dir, x)), reverse=True)
    
    # Rename the folder with their name(strip the last string)
    new_name = '-'.join(sorted_files[0].split('-')[:-1])
    os.rename(extracted_dir+sorted_files[0], extracted_dir+new_name)
    
    # Analyze the language portion
    portion = get_pp_file_size(extracted_dir+new_name)/get_folder_size(extracted_dir+new_name)
    
    # Delete the folder if the portion is less than 0.11
    if portion < 0.11:
        shutil.rmtree(extracted_dir+new_name)
        logging.info("%s deleted"%new_name)
    else:
        logging.info("%s saved"%new_name)
    if count % 10 == 0:
        time.sleep(3)
        logging.info('Sorry, need some rest')
    count += 1
    