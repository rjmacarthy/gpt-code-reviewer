import os
import openai
import yaml

from rich.console import Console
from rich.markdown import Markdown


from prompts import get_system_prompt, get_review_prompt
from helpers import get_repo_and_pr, print_options, fetch_repository_data, add_message
from completion import get_completion

config = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
console = Console()
openai.api_key = os.getenv("OPENAI_API_KEY")


def chat():
    messages = []

    repository, pull_request = get_repo_and_pr()

    print_options(repository, pull_request)

    if not pull_request:
        get_repo_and_pr()

    add_message(messages, get_system_prompt(), "system", pull_request, repository)

    data = fetch_repository_data(
        repository, pull_request, "application/vnd.github.v3+json"
    )
    add_message(messages, data.json()["body"], "user", pull_request, repository)
    add_message(messages, data.json()["title"], "user", pull_request, repository)

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
            data_type = "application/vnd.github.v3+json"
            data = fetch_repository_data(repository, pull_request, data_type)
            add_message(messages, data.json()["body"], "user", pull_request, repository)
            add_message(
                messages, data.json()["title"], "user", pull_request, repository
            )
            print_options(repository, pull_request)
            continue

        if user_input == "r":
            add_message(
                messages,
                get_review_prompt(repository, pull_request),
                "user",
                pull_request,
                repository,
            )

        if user_input:
            console.print("Thinking...")
            add_message(messages, user_input, "user", pull_request, repository)

        completion = get_completion(messages)

        reply = completion["choices"][0]["message"]["content"]

        console.print(Markdown("🤖: "))
        console.print(Markdown(reply))
        add_message(messages, reply, "assistant", pull_request, repository)


if __name__ == "__main__":
    chat()
