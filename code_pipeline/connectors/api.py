import getpass
import os

from .base import HostConnector


GENERATION_SYSTEM_INSTRUCTION = """
You are a Python code generator.

Return only valid Python source code.
Do not include markdown fences.
Do not include explanation text.
Respect the requested function names and parameter order exactly.
"""


def get_secret(env_names: list[str], prompt_text: str) -> str:
    for env_name in env_names:
        value = os.environ.get(env_name)
        if value:
            return value

    return getpass.getpass(prompt_text)


class GeminiConnector(HostConnector):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @property
    def connector_name(self) -> str:
        return f"GeminiConnector({self.model_name})"

    def cultivate(self, prompt: str) -> str:
        from google import genai
        from google.genai import types

        api_key = get_secret(
            ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
            "Enter Gemini API Key: ",
        )
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=GENERATION_SYSTEM_INSTRUCTION,
            ),
        )
        return response.text.strip()


class OpenAIConnector(HostConnector):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @property
    def connector_name(self) -> str:
        return f"OpenAIConnector({self.model_name})"

    def cultivate(self, prompt: str) -> str:
        from openai import OpenAI

        api_key = get_secret(
            ["OPENAI_API_KEY"],
            "Enter OpenAI API Key: ",
        )
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=self.model_name,
            input=[
                {"role": "system", "content": GENERATION_SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt},
            ],
        )
        return response.output_text.strip()


class ClaudeConnector(HostConnector):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @property
    def connector_name(self) -> str:
        return f"ClaudeConnector({self.model_name})"

    def cultivate(self, prompt: str) -> str:
        import anthropic

        api_key = get_secret(
            ["ANTHROPIC_API_KEY"],
            "Enter Anthropic API Key: ",
        )
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model_name,
            max_tokens=4000,
            system=GENERATION_SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
