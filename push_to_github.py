import os
import sys
import getpass
from git import Repo
import git

git.refresh(r"C:\Program Files\Git\bin\git.exe")
from git.exc import GitCommandError

def push_to_github():
    # Get the current directory
    repo_path = os.path.dirname(os.path.abspath(__file__))
    
    # Get GitHub username
    username = input("Enter your GitHub username: ")
    
    # Get repository name (default to folder name)
    folder_name = os.path.basename(repo_path)
    repo_name = input(f"Enter repository name (default: {folder_name}): ") or folder_name
    
    # Get GitHub personal access token
    token = getpass.getpass("Enter your GitHub personal access token: ")
    
    # Initialize repository if not already initialized
    try:
        repo = Repo(repo_path)
        print("Git repository already initialized.")
    except:
        print("Initializing Git repository...")
        repo = Repo.init(repo_path)
    
    # Add all files
    print("Adding files to repository...")
    repo.git.add('.')
    
    # Commit changes
    print("Committing changes...")
    try:
        repo.git.commit('-m', 'Initial commit with database fixes')
    except GitCommandError as e:
        if 'nothing to commit' in str(e):
            print("No changes to commit.")
        else:
            print(f"Error during commit: {e}")
            sys.exit(1)
    
    # Create remote URL with token authentication
    remote_url = f'https://{username}:{token}@github.com/{username}/book-look.git'
    
    # Add remote if it doesn't exist
    try:
        origin = repo.remote('origin')
        print("Remote 'origin' already exists. Updating URL...")
        repo.git.remote('set-url', 'origin', remote_url)
    except ValueError:
        print("Adding remote 'origin'...")
        origin = repo.create_remote('origin', remote_url)
    
    # Push to GitHub
    print("Pushing to GitHub...")
    try:
        origin.push('master:main')
        print(f"\nSuccess! Repository pushed to: https://github.com/{username}/{repo_name}")
    except GitCommandError as e:
        print(f"Error during push: {e}")
        sys.exit(1)

if __name__ == "__main__":
    push_to_github()