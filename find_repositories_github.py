from bs4 import BeautifulSoup
import requests
import os
import csv
import pandas as pd
from datetime import datetime, date
from git import Repo, log
import subprocess
import json

# Function for getting the urls
def get_link(current_page, base_url):
    r = requests.get(current_page)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Get all the blocks & next page
    lists = soup.findAll('a', class_="Link d-inline-block")
    next_page = soup.find('a', class_="next_page")
    url_lists = [base_url+list['href'] for list in lists]
    
    # Return next page if not none
    if next_page is None:
        return url_lists, None
    else:
        return url_lists, base_url+next_page['href']
    
# Get the language percentage
def lang_percentage(repo_url):
    # Get /author/repo
    repo = repo_url[18:]
    # Define the GitHub CLI API command as a list of strings
    gh_cli_command = [
        "gh",  # GitHub CLI command
        "api",  # GitHub CLI API subcommand
        "-H", "Accept: application/vnd.github+json",  # Specify the Accept header
        "-H", "X-GitHub-Api-Version: 2022-11-28",  # Specify the API version header
        "/repos%s/languages"%repo  # The GitHub API endpoint you want to access
    ]

    # Run the GitHub CLI API command and capture the output
    try:
        output = subprocess.check_output(gh_cli_command)
        # If you want to decode the output to a string (assuming it's in bytes)
        decoded_output = output.decode('utf-8')
        # Calculate the percentage
        data_dict = json.loads(decoded_output)
        if 'Puppet' not in data_dict.keys():
            return 0
        else:
            result = data_dict['Puppet']/sum(data_dict.values())
            return result
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        return None


# Date lists
number_of_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# Two repositories (Mirantis& Wikimedia) are to be mined
current_url_mirantis = 'https://github.com/orgs/Mirantis/repositories'
current_url_wikimedia = 'https://github.com/orgs/wikimedia/repositories'
mirantis_repositories = []
wikimedia_repositories = []

# Repo link storage
mirantis_path = './LOG6307E/replication/mirantis_repos.txt'
wikimedia_path = './LOG6307E/replication/wikimedia_repos.txt'

# Percentage storage
title = ['Repo_url', 'Puppet_percentage']
mirantis_percentage = './LOG6307E/mirantis_repos.csv'
wikimedia_percentage = './LOG6307E/wikimedia_repos.csv'

# Base for the repos
base_url = 'https://github.com'

# If the link file does not exist, get all the links(mirantis)
if not os.path.exists(mirantis_path):
    while True:
        url_lists, next_url = get_link(current_url_mirantis, base_url)
        mirantis_repositories.extend(url_lists)
        if next_url == None:
            break
        else:
            current_url_mirantis = next_url
    with open(r'%s'%mirantis_path, 'w') as fp:
        fp.write('\n'.join(mirantis_repositories))
# Else we load from file directly
else:
    with open(r'%s'%mirantis_path, 'r') as fp:
        for line in fp:
            mirantis_repositories.append(line.strip())

# Repos that satisfy the constraints
if not os.path.exists(mirantis_percentage):
    mirantis_puppet_repos = []
    for repo in mirantis_repositories:
        # Skip all the repos without puppet code
        percentage = lang_percentage(repo)
        if percentage < 0.11:
            continue
        else:
            mirantis_puppet_repos.append({'Repo_url':repo, 'Puppet_percentage':percentage})
    # Save a csv
    with open(mirantis_percentage, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=title)
        writer.writeheader()
        writer.writerows(mirantis_puppet_repos)
    # Update the repositories
    mirantis_repositories = [repo['Repo_url'] for repo in mirantis_puppet_repos]
else:
    mirantis_df = pd.DataFrame(pd.read_csv(mirantis_percentage))
    mirantis_repositories = list(mirantis_df['Repo_url'])
    

valid_repos = []
# Iterate through all the repositories
for repo in mirantis_repositories:
    # Whether the repo is valid
    flag = True
    if not os.path.exists('./LOG6307E/replication/repositories/Mirantis/%s'%repo.split('/')[-1]):
        Repo.clone_from(repo, './LOG6307E/replication/repositories/Mirantis/%s'%repo.split('/')[-1])
        
    r = Repo('./LOG6307E/replication/repositories/Mirantis/%s'%repo.split('/')[-1])
    
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
            break
    if flag:
        valid_repos.append(repo.split('/')[-1])
        print(repo)
print(len(valid_repos))
exit()


# Get all the links(wikimedia)
# If the link file does not exist, get all the links(wikimedia)
if not os.path.exists(wikimedia_path):
    while True:
        url_lists, next_url = get_link(current_url_wikimedia, base_url)
        wikimedia_repositories.extend(url_lists)
        if next_url == None:
            break
        else:
            current_url_wikimedia = next_url
    with open(r'%s'%wikimedia_path, 'w') as fp:
        fp.write('\n'.join(wikimedia_repositories))
# Else we load from file directly
else:
    with open(r'%s'%wikimedia_path, 'r') as fp:
        for line in fp:
            wikimedia_repositories.append(line.strip())
            
        
# Repos that satisfy the constraints
if not os.path.exists(wikimedia_percentage):
    wikimedia_puppet_repos = []
    for repo in wikimedia_puppet_repos:
        # Skip all the repos without puppet code
        percentage = lang_percentage(repo)
        if percentage < 0.11:
            continue
        else:
            wikimedia_puppet_repos.append({'Repo_url':repo, 'Puppet_percentage':percentage})
    # Save a csv
    with open(wikimedia_percentage, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=title)
        writer.writeheader()
        writer.writerows(wikimedia_puppet_repos)
    # Update the repositories
    wikimedia_repositories = [repo['Repo_url'] for repo in wikimedia_puppet_repos]
else:
    wikimedia_df = pd.DataFrame(pd.read_csv(wikimedia_percentage))
    wikimedia_repositories = list(wikimedia_df['Repo_url'])