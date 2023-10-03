from bs4 import BeautifulSoup
import requests
import os
import csv
import pandas as pd
from datetime import datetime, date
from git import Repo, log
import subprocess
import json
import shutil
from tqdm import tqdm

# Function for getting the urls
def get_link(page_num, base_url):
    current_page = 'https://opendev.org/explore/repos?page=%d&sort=recentupdate&q=&topic=false&language=&only_show_relevant=false'%page_num
    r = requests.get(current_page)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Get all the blocks & next page
    lists = soup.findAll('a', class_="name")
    url_lists = [base_url+list['href'] for list in lists]
    
    return url_lists
    
# Get the language percentage
def lang_percentage(repo_url):
    # Get the language percentage from the page
    r = requests.get(repo_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    percentage_part = soup.findAll(class_="item gt-df gt-ac gt-jc")
    # Skip if the percentage part is empty
    if len(percentage_part) == 0:
        return 0
    for per in percentage_part:
        newtext = per.text.strip()
        # Get rid of all the \t
        newtext = ''.join([t for t in newtext.split('\t') if t != ''])
        newtext = [t for t in newtext.split('\n') if t != '']
        if newtext[0] == 'Puppet':
            return float(newtext[1].strip('%'))/100
    return 0

opendev_repositories = []

# Date lists
number_of_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# Repo link storage
opendev_path = '../replication/opendev_repos.txt'

# Percentage storage
title = ['Repo_url', 'Puppet_percentage']
opendev_percentage = '../replication/opendev_repos.csv'

# Base for the repos
base_url = 'https://opendev.org'

# If the link file does not exist, get all the links(openstack)
if not os.path.exists(opendev_path):
    for page_number in range(1, 120):
        url_lists = get_link(page_number, base_url)
        opendev_repositories.extend(url_lists)
    with open(r'%s'%opendev_path, 'w') as fp:
        fp.write('\n'.join(opendev_repositories))
# Else we load from file directly
else:
    with open(r'%s'%opendev_path, 'r') as fp:
        for line in fp:
            opendev_repositories.append(line.strip())
  


# Repos that satisfy the constraints
if not os.path.exists(opendev_percentage):
    opendev_puppet_repos = []
    progress_bar = tqdm(total=len(opendev_repositories), desc="Processing")
    for repo in opendev_repositories:
        # Skip all the repos without puppet code
        percentage = lang_percentage(repo)
        if percentage < 0.11:
            continue
        else:
            opendev_puppet_repos.append({'Repo_url':repo, 'Puppet_percentage':percentage})
        progress_bar.update(1)
    progress_bar.close()
    # Save a csv
    with open(opendev_percentage, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=title)
        writer.writeheader()
        writer.writerows(opendev_puppet_repos)
    # Update the repositories
    opendev_repositories = [repo['Repo_url'] for repo in opendev_puppet_repos]
else:
    opendev_df = pd.DataFrame(pd.read_csv(opendev_percentage))
    opendev_repositories = list(opendev_df['Repo_url'])

valid_repos = []
# Iterate through all the repositories
for repo in opendev_repositories:
    # Whether the repo is valid
    flag = True
    if not os.path.exists('../repositories/Opendev/%s'%repo.split('/')[-1]):
        Repo.clone_from(repo, '../replication/repositories/Opendev/%s'%repo.split('/')[-1])
        
    r = Repo('../replication/repositories/Opendev/%s'%repo.split('/')[-1])
    
    # Get the first commit
    first_commit = r.git.log("--reverse", "--pretty=%at", "--date=iso", n="1").splitlines()[0]
    first_commit_date = datetime.utcfromtimestamp(int(first_commit)).date()
    
    last_commit = r.git.log("-n", "1", "--pretty=%at", "--date=iso").splitlines()[0]
    last_commit_date = datetime.utcfromtimestamp(int(last_commit)).date()
    # Change the date if it is after the publish date (we assume 2019/08/01)
    if last_commit_date > date(2019, 8, 1):
        last_commit_date = date(2019, 8, 1)
    
    # Iterate through the years and check the number of commits
    for year in range(first_commit_date.year, last_commit_date.year+1):
        if year == first_commit_date.year:
            start_month = first_commit_date.month
        else:
            start_month = 1
        for month in range(start_month, 13):
            start_date = datetime(year, month, 1)
            # Check whether Feb is special
            if year % 4 == 0 and month == 2:
                end_date = datetime(year, 2, 29)
            else:
                end_date = datetime(year, month, number_of_days[month-1])
            number = 0
            # Count the number of commits
            for commit in r.iter_commits(since=start_date, until=end_date):
                number += 1
            # Break if monthly commit is less than 2
            if number < 2:
                flag = False
                break
            # Break if reached the last month
            if year == last_commit_date.year and month == last_commit_date.month:
                break
        if not flag:
            # Delete the folder and break
            shutil.rmtree('../replication/repositories/Mirantis/%s'%repo.split('/')[-1])
            print('%s has been removed! '%repo.split('/')[-1])
            break
    if flag:
        valid_repos.append(repo.split('/')[-1])
        print('%s has been appended! '%repo.split('/')[-1])
print(len(valid_repos))
