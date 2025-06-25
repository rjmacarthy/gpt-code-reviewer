import yaml
import os
import tiktoken
import requests
from rich.console import Console
from rich.markdown import Markdown


config = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))

repositories = config["repositories"]
MODEL_ENGINE = config["model_engine"]
MAX_LENGTH = 2500
user = config["user"]

console = Console()
encoding = tiktoken.encoding_for_model(MODEL_ENGINE)
github_repository_base_url = "https://api.github.com/repos"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def count_tokens(string: str) -> int:
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_diff(diff: str, num_template_tokens: int) -> str:
    if count_tokens(diff) > MAX_LENGTH - num_template_tokens:
        encoded_diff = encoding.encode(diff)
        truncated_diff = encoding.decode(
            encoded_diff[: MAX_LENGTH - num_template_tokens * 2]
        )
        return truncated_diff
    return diff


def print_options(repository: str, pull_request: str):
    console.print(
        Markdown(
            f"""You have chosen to review {repository} pull request {pull_request} 
                enter `r` to review the code, `q` to quit, `h` for help and `n` 
                to review a different pull request."""
        )
    )


def get_repo_and_pr() -> tuple:
    while True:
        console.print("Select a repository:")
        for index, repo in enumerate(repositories):
            console.print(f"{index + 1}. {repo}")

        try:
            selection = int(input("Enter the number of the repository: "))
            if 1 <= selection <= len(repositories):
                repository = repositories[selection - 1]
                break
        except ValueError:
            pass

        console.print(
            f"Invalid input. Please enter a number between 1 and {len(repositories)}"
        )

    pull_request = input("Enter the number of the pull request: ").strip()

    return repository, pull_request


def add_message(messages, message: str, role, pr: str, repository):
    messages.append({"role": role, "content": message})

    if not os.path.exists("./transcripts"):
        os.makedirs("./transcripts")

    with open(f"./transcripts/{pr}-{repository}.md", "a") as f:
        f.write(role + "\n" + message + "\n")


def fetch_repository_data(
    repository: str, pull_request: str, accept="application/vnd.github.v3.diff"
) -> requests.Response:
    url = f"{github_repository_base_url}/{user}/{repository}/pulls/{pull_request}"
    headers = {"Accept": accept, "Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, timeout=10)
    return response
