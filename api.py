import uvicorn
from fastapi import FastAPI

from prompts import get_system_prompt, get_review_prompt
from helpers import add_message
from completion import get_completion

app = FastAPI()


@app.get("/api/v1/ping")
async def root():
    return "pong"


@app.get("/api/v1/review/{pull_request}/{repository}")
async def review(pull_request, repository):
    messages = []
    add_message(messages, get_system_prompt(), "system", pull_request, repository)
    add_message(
        messages,
        get_review_prompt(repository, pull_request),
        "user",
        pull_request,
        repository,
    )
    completion = get_completion(messages)
    return completion


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
