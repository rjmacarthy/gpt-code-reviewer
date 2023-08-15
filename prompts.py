from helpers import fetch_repository_data, get_diff, count_tokens


def get_system_prompt() -> str:
    return """
    You are a highly skilled software engineer specializing in code reviews. 
    Your task is to review code changes in a unidiff format.
    Ensure your feedback is constructive and professional.
    """


def get_diff_prompt(code: str) -> str:
    return f"""
    As a highly skilled software engineer, review the following code:

    ```
    {code}
    ```

    Present it in markdown format, and refrain from mentioning:
    - Adding comments or documentation
    - Adding dependencies or related pull requests

    """


def get_review_prompt(repository, pull_request):
    response = fetch_repository_data(repository, pull_request)

    tokens_without_diff = count_tokens(get_diff_prompt(""))

    prompt = get_diff_prompt(get_diff(response.text, tokens_without_diff))

    return prompt
