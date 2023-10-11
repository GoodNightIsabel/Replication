import requests

# Replace with your own GitHub username and personal access token
username = 'GoodNightIsabel'
access_token = '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'

# API endpoint to list user's repositories
api_url = f'https://api.github.com/users/{username}/repos'

# Create headers with the access token
headers = {
    'Authorization': f'token {access_token}',
}

try:
    # Make the API request to get the user's repositories
    response = requests.get(api_url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        repositories = response.json()
        # Extract repository names
        repo_names = [repo['name'] for repo in repositories]
        # Print repository names
        for name in repo_names:
            print(name)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"An error occurred: {str(e)}")
