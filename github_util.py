import os
import subprocess
import shutil
import time
from ghapi.all import GhApi



github_token = os.environ.get("GITHUB_TOKEN")
if github_token is None:
    print("GITHUB_TOKEN is not set")
    exit(1)

def wrap_command(command):
    """
    wrap the command with subprocess.run
    """
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        raise e
    
def create_branch_and_pull_request(owner_name, repo_name, github_token, diff_file_path, title, new_branch_name):
    """
    use command line git to do the following:
    1, clone the repo
    2. create a new branch
    3. apply the diff_file_path
    4. create a new commit
    5. push the new branch
    6. create a pull request
    """
    try:
        shutil.rmtree(repo_name, ignore_errors=True)
        
        # clone the repo
        wrap_command(f"git clone https://{github_token}@github.com/{owner_name}/{repo_name}.git {repo_name}")
        os.chdir(repo_name)

        # create a new branch
        wrap_command(f"git checkout -b {new_branch_name}")
        # apply the diff_file_path
        wrap_command(f"git apply ../{diff_file_path}")
        # create a new commit
        wrap_command(f"git add .")
        wrap_command("git config user.email dev009527@gmail.com")
        wrap_command("git config user.name dev009527")
        wrap_command(f"git commit -m 'commit message'")
        # push the new branch
        wrap_command(f"git push origin {new_branch_name}")
        # create a pull request

        api = GhApi(token=github_token)
        api.pulls.create(owner=owner_name, repo=repo_name, title=title, head=new_branch_name, base="main",
                        body="Please review this pull request.", draft=False)
    finally:
        os.chdir("..")
        shutil.rmtree(repo_name)

if __name__ == "__main__":

    owner_name = "bd-iaas-us"
    repo_name = "AILint"
    import sys
    if len(sys.argv) != 2:
        print("Usage: python github_util.py <diff_file_path>")
        sys.exit(1)
    diff_file_path = sys.argv[1]
    title = "My first pull request title"
    new_branch_name = "new_branch_for_pr4"
    create_branch_and_pull_request(owner_name, repo_name, github_token, diff_file_path, title, new_branch_name)

    
