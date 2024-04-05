import run
import re
import os
from sweagent import AgentArguments, ModelArguments
from github_util import create_branch_and_pull_request
import sys



github_token = os.environ.get("GITHUB_TOKEN")
if github_token is None:
    print("GITHUB_TOKEN is not set")
    exit(1)

def extract_info_from_github_url(url):
    #match owner_name、repo_name 和 issue_number
    pattern = r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    
    if match:
        owner_name = match.group(1)
        repo_name = match.group(2)
        issue_number = match.group(3)
        return owner_name, repo_name, issue_number
    else:
        raise ValueError("Invalid github url")

def magic(html_url: str):
    #html_url example
    #https://github.com/bd-iaas-us/AILint/issues/10
    defaults = run.ScriptArguments(
        suffix="",
        environment=run.EnvironmentArguments(
            image_name="swe-agent",
            data_path=html_url,
            split="dev",
            verbose=True,
            install_environment=True,
        ),
        skip_existing=True,
        agent=AgentArguments(
            model=ModelArguments(
                model_name="gpt4",
                total_cost_limit=0.0,
                per_instance_cost_limit=2.0,
                temperature=0.2,
                top_p=0.95,
            ),
            config_file="config/default.yaml",
        ),
    )
    owner_name, repo_name, issue_number = extract_info_from_github_url(html_url)
    diff_file_path = f"{repo_name}-{issue_number}.diff"
    new_branch_name =f"ai-task-issue#{issue_number}"
    title = f"resolve issue#{issue_number} with dev009527"
    info = run.main(defaults)
    #if info has a submit, create a PR on github.
    if info['exit_status'] == 'submitted':
        with open(diff_file_path, "w") as f:
            f.write(info['submission'])
        create_branch_and_pull_request(owner_name, repo_name, 
                                       github_token, diff_file_path, title, new_branch_name)
        os.remove(diff_file_path)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python magic.py <github_url>")
        sys.exit(1)
    magic(sys.argv[1])
