import openai
import os
import yaml

config = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL_ENGINE = config["model_engine"]


def get_completion(messages):
    return openai.ChatCompletion.create(
        model=MODEL_ENGINE,
        messages=messages,
    )
