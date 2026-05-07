DEFAULT_HOST = "ollama"

HOST_DISPLAY_NAMES = {
    "gemini": "Gemini API",
    "openai": "OpenAI API",
    "claude": "Claude API",
    "ollama": "Ollama Local",
}

HOST_DEFAULT_MODELS = {
    "gemini": "gemini-3.1-flash-lite-preview",
    "openai": "gpt-5.1-mini",
    "claude": "claude-sonnet-4-5",
    "ollama": "qwen2.5-coder:7b",
}

HOST_MODEL_OPTIONS = {
    "gemini": [
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-flash",
        "gemini-3.1-pro",
    ],
    "openai": [
        "gpt-5.1-mini",
        "gpt-5.1",
        "gpt-5-mini",
    ],
    "claude": [
        "claude-sonnet-4-5",
        "claude-opus-4-1",
        "claude-haiku-4-5",
    ],
    "ollama": [],
}
