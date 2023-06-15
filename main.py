import os
import openai
import requests
import yaml
import tiktoken

from rich.console import Console
from rich.markdown import Markdown


from prompts import get_diff_prompt, get_system_prompt

config = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MAX_LENGTH = 2500
MODEL_ENGINE = config["model_engine"]

console = Console()
encoding = tiktoken.encoding_for_model(MODEL_ENGINE)
openai.api_key = os.getenv("OPENAI_API_KEY")
repositories = config["repositories"]
user = config["user"]


def count_tokens(string: str) -> int:
    num_tokens = len(encoding.encode(string))
    return num_tokens


def get_truncated_diff(diff: str, num_template_tokens: int) -> str:
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


def send_system_message(messages: list) -> openai.ChatCompletion:
    response = openai.ChatCompletion.create(model=MODEL_ENGINE, messages=messages)
    return response


def fetch_data(
    repository: str, pull_request: str, accept="application/vnd.github.v3.diff"
) -> requests.Response:
    url = f"https://api.github.com/repos/{user}/{repository}/pulls/{pull_request}"
    headers = {"Accept": accept, "Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, timeout=10)
    return response


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


def review():
    repository, pull_request = get_repo_and_pr()

    print_options(repository, pull_request)

    if not pull_request:
        get_repo_and_pr()

    messages = [{"role": "system", "content": get_system_prompt()}]

    if MODEL_ENGINE == "gpt4":
        send_system_message(messages)

    data = fetch_data(repository, pull_request, "application/vnd.github.v3+json")
    messages.append({"role": "user", "content": data.json()["body"]})
    messages.append({"role": "user", "content": data.json()["title"]})

    while True:
        user_input = input("👨: ")

        if user_input == "q":
            break

        if user_input == "h":
            console.print(
                Markdown(
                    "Enter `r` to review the code, `q` to quit and `n` to review a different pull request."
                )
            )
            continue

        if user_input == "n":
            messages = [{"role": "system", "content": get_system_prompt()}]
            repository, pull_request = get_repo_and_pr()
            data = fetch_data(
                repository, pull_request, "application/vnd.github.v3+json"
            )
            messages.append({"role": "user", "content": data.json()["body"]})
            messages.append({"role": "user", "content": data.json()["title"]})
            print_options(repository, pull_request)
            continue

        if user_input == "r":
            response = fetch_data(repository, pull_request)

            num_template_tokens = count_tokens(get_diff_prompt(""))

            prompt = get_diff_prompt(
                get_truncated_diff(response.text, num_template_tokens)
            )

            add_message(messages, prompt, "user", pull_request, repository)

        if user_input:
            console.print("Thinking...")
            add_message(messages, user_input, "user", pull_request, repository)

        completion = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=messages,
        )

        reply = completion["choices"][0]["message"]["content"]

        console.print(Markdown("🤖: "))
        console.print(Markdown(reply))
        add_message(messages, reply, "assistant", pull_request, repository)


if __name__ == "__main__":
    review()
