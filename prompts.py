from helpers import fetch_repository_data, get_diff, count_tokens


def get_system_prompt() -> str:
    return """
    You are a highly skilled software engineer specializing in code review. Your task is to review code changes in a unidiff format, following these guidelines:

    1. Thoroughly review the code and provide clear, specific feedback for improvement using numbered lists.
    2. Consider readability, maintainability, and scalability.
    3. Explain any complex or hard-to-understand code sections.
    4. Suggest optimizations and assess time complexity and performance.
    5. Identify potential bugs and issues.

    Ensure your feedback is constructive and professional, avoiding harsh language or personal attacks. Your timely response is vital to the code review process.
    """


def get_diff_prompt(code: str) -> str:
    return f"""
    As a highly skilled software engineer, review the following code:

    ```
    {code}
    ```

    Provide feedback on:
    1. Code readability, maintainability, and scalability improvements.
    2. Best practices, including code organization and variable naming.
    3. Clarification of complex or hard-to-understand code sections.
    4. Optimization suggestions, considering time complexity and performance.
    5. Potential bugs and issues.
    6. If you have multiple comments format them as a numbered list.
    7. If you have suggestions to improve the code please always give an example along with your feedback.

    Present it in markdown format, and refrain from mentioning:
    - Adding comments or documentation
    - Adding dependencies or related pull requests

    """


def get_review_prompt(repository, pull_request):
    response = fetch_repository_data(repository, pull_request)

    tokens_without_diff = count_tokens(get_diff_prompt(""))

    prompt = get_diff_prompt(get_diff(response.text, tokens_without_diff))

    return prompt
