from bs4 import BeautifulSoup
import requests
import os
import csv
import pandas as pd
from datetime import datetime, date
from git import Repo, log
import subprocess
import json
import subprocess
import shutil
import time

# Function for getting the urls
def get_link(current_page, base_url):
    r = requests.get(current_page)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Get all the blocks
    lists = soup.findAll('a', class_="Link d-inline-block")
    url_lists = [base_url+list['href'] for list in lists]
    
    # Return the url list
    return url_lists
    
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

wikimedia_repositories = []

# Repo link storage
wikimedia_path = '../wikimedia_repos.txt'

# Percentage storage
title = ['Repo_url', 'Puppet_percentage']
wikimedia_percentage = '../wikimedia_repos.csv'

# Base for the repos
base_url = 'https://github.com'

# Get all the links(wikimedia)
# If the link file does not exist, get all the links(wikimedia)
if not os.path.exists(wikimedia_path):
    for index in range(1, 68):
        # Shuffle the login
        if index%10==0 and int(index/10)%2 == 1:
            # Log out
            command = f'gh auth logout'
            try:
                subprocess.run(command, shell=True, check=True)
                print("Logged out from the last account.")
            except subprocess.CalledProcessError as e:
                print(f"You have not logged in previouly")

            access_token = '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'
            # Command to run the 'gh auth login' command with the token as input
            command = f'echo "{access_token}" | gh auth login --with-token'
            # Run the command using subprocess
            try:
                subprocess.run(command, shell=True, check=True)
                print("GitHub authentication successful.")
            except subprocess.CalledProcessError as e:
                print(f"GitHub authentication failed with error code {e.returncode}.")
        elif index%10==0 and int(index/10)%2 == 0:
            # Log out
            command = f'gh auth logout'
            try:
                subprocess.run(command, shell=True, check=True)
                print("Logged out from the last account.")
            except subprocess.CalledProcessError as e:
                print(f"You have not logged in previouly")

            access_token = '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'
            # Command to run the 'gh auth login' command with the token as input
            command = f'echo "{access_token}" | gh auth login --with-token'
            # Run the command using subprocess
            try:
                subprocess.run(command, shell=True, check=True)
                print("GitHub authentication successful.")
            except subprocess.CalledProcessError as e:
                print(f"GitHub authentication failed with error code {e.returncode}.")

        print('Scraping page%d... Please be patient'%index)
        # Change the index
        current_url_wikimedia = 'https://github.com/orgs/wikimedia/repositories?page=%d'%index
        url_lists = get_link(current_url_wikimedia, base_url)
        wikimedia_repositories.extend(url_lists)
        # Good night...
        time.sleep(3)
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
    count = 1
    for repo in wikimedia_repositories:
        # Skip all the repos without puppet code
        percentage = lang_percentage(repo)
        if percentage < 0.11:
            continue
        else:
            print('%s satisfies the constraint!'%repo)
            wikimedia_puppet_repos.append({'Repo_url':repo, 'Puppet_percentage':percentage})
        # Have a rest bro
        if count % 20 == 0:
            time.sleep(3)
        if count % 100 == 0:
            print('Dealt with %d repositories...'%count)
            count += 1
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
    
valid_repos = []
# Iterate through all the repositories
for repo in wikimedia_repositories:
    # Whether the repo is valid
    flag = True
    if not os.path.exists('../repositories/Wikimedia/%s'%repo.split('/')[-1]):
        Repo.clone_from(repo, '../repositories/Wikimedia/%s'%repo.split('/')[-1])
        
    r = Repo('../repositories/Wikimedia/%s'%repo.split('/')[-1])
    
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
            shutil.rmtree('../repositories/Wikimedia/%s'%repo.split('/')[-1])
            print('%s has been removed! '%repo.split('/')[-1])
            break
    if flag:
        valid_repos.append(repo.split('/')[-1])
        print('%s has been appended! '%repo.split('/')[-1])