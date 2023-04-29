import os
import openai
import requests
import yaml

from rich.console import Console
from rich.markdown import Markdown


from prompts import get_code_prompt, get_system_prompt


config = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
user = config["user"]
repositories = config["repositories"]
MODEL_ENGINE = "gpt-3.5-turbo"

console = Console()


def print_options(repository, pull_request):
    console.print(
        Markdown(
            f"""You have chosen to review {repository} pull request {pull_request} 
                enter 'r' to review the code, 'q' to quit, 'h' for help and 'n' 
                to review a different pull request"""
        )
    )


def send_system_message(messages):
    response = openai.ChatCompletion.create(model=MODEL_ENGINE, messages=messages)
    return response


def get_prompt(repository, pull_request, accept="application/vnd.github.v3.diff"):
    url = f"https://api.github.com/repos/{user}/{repository}/pulls/{pull_request}"
    headers = {"Accept": accept, "Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, timeout=10)
    return response


def get_repo_and_pr():
    console.print("Select a repository:")
    for index, repo in enumerate(repositories):
        print(f"{index + 1}. {repo}")
    selection = None
    while selection is None:
        try:
            selection = int(input("Enter the number of the repository: "))
            if selection < 1 or selection > len(repositories):
                raise ValueError
        except ValueError:
            print(
                "Invalid input. Please enter a number between 1 and", len(repositories)
            )
            selection = None

    repository = repositories[selection - 1]

    pull_request = input("Enter the number of the pull request: ")

    return repository, pull_request


def review():
    repository, pull_request = get_repo_and_pr()

    print_options(repository, pull_request)

    if not pull_request:
        get_repo_and_pr()

    messages = [{"role": "system", "content": get_system_prompt()}]

    print("Loading Skynet...")
    send_system_message(messages)
    print("Skynet loaded!")

    data = get_prompt(repository, pull_request, "application/vnd.github.v3+json")
    messages.append({"role": "user", "content": data.json()["body"]})
    messages.append({"role": "user", "content": data.json()["title"]})

    while True:
        user_input = input("👨: ")

        if user_input == "q":
            break

        if user_input == "h":
            console.print(
                Markdown(
                    "Enter `r` to review the code, `q` to quit and `n` to review a different pull request"
                )
            )
            continue

        if user_input == "n":
            messages = [{"role": "system", "content": get_system_prompt()}]
            repository, pull_request = get_repo_and_pr()
            data = get_prompt(
                repository, pull_request, "application/vnd.github.v3+json"
            )
            messages.append({"role": "user", "content": data.json()["body"]})
            messages.append({"role": "user", "content": data.json()["title"]})
            print_options(repository, pull_request)
            continue

        if user_input == "r":
            response = get_prompt(repository, pull_request)

            max_len = 4097
            code = response.text[: max_len - 600]

            prompt = get_code_prompt(code)

            messages.append({"role": "user", "content": prompt})

        if user_input:
            messages.append({"role": "user", "content": user_input})

        completion = openai.ChatCompletion.create(
            model=MODEL_ENGINE,
            messages=messages,
        )

        reply = completion["choices"][0]["message"]["content"]
        console.print(Markdown("🤖: "))
        console.print(Markdown(reply))
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    review()
