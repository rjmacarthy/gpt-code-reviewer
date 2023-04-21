import os
import openai
from rich.console import Console
from rich.markdown import Markdown
import requests
import yaml


config = yaml.safe_load(open("config.yaml"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
user = config["user"]
repositories = config["repositories"]
model_engine = "gpt-3.5-turbo"

console = Console()


def system_prompt():
    return """
    You are an awesome software engineer. You specialise in reviewing code.
    When you review the code only check the syntax and the logic. Do not refer to related pull requests.
    Do not mention any other dependencies or pull requests.
    Do not mention documentation or tests.
    """


def send_system_message(messages):
    response = openai.ChatCompletion.create(model=model_engine, messages=messages)
    return response


def get_prompt(repository, pull_request, accept="application/vnd.github.v3.diff"):
    url = f"https://api.github.com/repos/{user}/{repository}/pulls/{pull_request}"
    headers = {"Accept": accept, "Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response


def get_repo_and_pr():
    print("Select a repository:")
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

    console.print(
        Markdown(
            f"You have chosen to review {repository} pull request {pull_request} enter 'r' to review the code, 'q' to quit, 'h' for help and 'n' to review a different pull request"
        )
    )

    if not pull_request:
        get_repo_and_pr()

    messages = [{"role": "system", "content": system_prompt()}]

    print("Loading sky net...")
    send_system_message(messages)
    print("Sky net loaded!")

    data = get_prompt(repository, pull_request, "application/vnd.github.v3+json")
    messages.append({"role": "user", "content": data.json()["body"]})
    messages.append({"role": "user", "content": data.json()["title"]})

    while True:
        user_input = input("👨: ")

        if user_input == "q":
            break

        if user_input == "h":
            print(
                'Enter "r" to review the code, "q" to quit and "n" to review a different pull request'
            )

        if user_input == "n":
            messages = [{"role": "system", "content": system_prompt()}]
            repository, pull_request = get_repo_and_pr()
            data = get_prompt(
                repository, pull_request, "application/vnd.github.v3+json"
            )
            messages.append({"role": "user", "content": data.json()["body"]})
            messages.append({"role": "user", "content": data.json()["title"]})
            print(
                f"You have chosen to review {repository} pull request {pull_request} enter 'r' to review the code, 'q' to quit, 'h' for help and 'n' to review a different pull request"
            )
            continue

        if user_input == "r":
            response = get_prompt(repository, pull_request)

            max_len = 4097
            code = response.text[: max_len - 500]

            message = f"""
            Review the code: ```{code}```. check the syntax and the logic. Do not refer to related pull requests, tests or documentation.
            Recommend improvements to the code to make it cleaner and more maintainable.  Other things you can recommend are: naming conventions etc. {config["preferences"]}
            """

            messages.append({"role": "user", "content": message})

        if user_input:
            messages.append({"role": "user", "content": user_input})

        completion = openai.ChatCompletion.create(
            model=model_engine,
            messages=messages,
        )

        reply = completion["choices"][0]["message"]["content"]
        console.print(Markdown("🤖: "))
        console.print(Markdown(reply))
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    review()
