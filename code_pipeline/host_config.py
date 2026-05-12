import os


DEFAULT_HOST = "ollama"

HOST_DISPLAY_NAMES = {
    "gemini": "Gemini API",
    "openai": "OpenAI API",
    "claude": "Claude API",
    "ollama": "Ollama Local",
}

HOST_DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-5-mini",
    "claude": "claude-sonnet-4-20250514",
    "ollama": "qwen2.5-coder:7b",
}

HOST_MODEL_OPTIONS = {
    "gemini": [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-pro-preview",
    ],
    "openai": [
        "gpt-5-mini",
        "gpt-5.1",
        "gpt-5",
        "gpt-5-nano",
    ],
    "claude": [
        "claude-sonnet-4-20250514",
        "claude-opus-4-1-20250805",
        "claude-3-5-haiku-latest",
    ],
    "ollama": [],
}

HOST_API_KEY_ENV_NAMES = {
    "gemini": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    "openai": ("OPENAI_API_KEY",),
    "claude": ("ANTHROPIC_API_KEY",),
}


def get_api_key_from_environment(host_name: str) -> str | None:
    for env_name in HOST_API_KEY_ENV_NAMES.get(host_name, ()):
        value = os.environ.get(env_name)
        if value:
            return value
    return None


def get_default_model(host_name: str) -> str:
    return HOST_DEFAULT_MODELS.get(host_name, HOST_DEFAULT_MODELS[DEFAULT_HOST])


def get_fallback_model_options(host_name: str) -> list[str]:
    options = HOST_MODEL_OPTIONS.get(host_name, [])
    if options:
        return list(options)

    default_model = HOST_DEFAULT_MODELS.get(host_name)
    return [default_model] if default_model else []


def _normalize_model_name(name: str) -> str:
    if "/" in name:
        return name.rsplit("/", 1)[-1]
    return name


def _sort_models(model_names: set[str], preferred: str) -> list[str]:
    ordered = sorted(model_names)
    if preferred in ordered:
        ordered.remove(preferred)
        ordered.insert(0, preferred)
    return ordered


def _list_gemini_models(api_key: str | None) -> list[str]:
    if not api_key:
        return []

    from google import genai

    client = genai.Client(api_key=api_key)
    model_names: set[str] = set()

    for model in client.models.list():
        raw_name = getattr(model, "name", "")
        if not raw_name:
            continue

        supported_methods = (
            getattr(model, "supported_generation_methods", None)
            or getattr(model, "supported_actions", None)
            or []
        )
        if supported_methods and "generateContent" not in supported_methods:
            continue

        model_name = _normalize_model_name(raw_name)
        if model_name.startswith("gemini-"):
            model_names.add(model_name)

    return _sort_models(model_names, HOST_DEFAULT_MODELS["gemini"])


def _list_openai_models(api_key: str | None) -> list[str]:
    if not api_key:
        return []

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.models.list()
    model_names: set[str] = set()

    excluded_fragments = (
        "audio",
        "embedding",
        "image",
        "moderation",
        "realtime",
        "search",
        "tts",
        "transcribe",
        "whisper",
    )

    for model in getattr(response, "data", []):
        model_id = getattr(model, "id", "")
        if not model_id:
            continue
        if any(fragment in model_id for fragment in excluded_fragments):
            continue
        if model_id.startswith(("gpt-", "o")):
            model_names.add(model_id)

    return _sort_models(model_names, HOST_DEFAULT_MODELS["openai"])


def _list_claude_models(api_key: str | None) -> list[str]:
    if not api_key:
        return []

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    if not hasattr(client, "models"):
        return []

    response = client.models.list(limit=100)
    model_names: set[str] = set()

    for model in getattr(response, "data", []):
        model_id = getattr(model, "id", "")
        if model_id.startswith("claude-"):
            model_names.add(model_id)

    return _sort_models(model_names, HOST_DEFAULT_MODELS["claude"])


def list_provider_models(host_name: str, api_key: str | None = None) -> tuple[list[str], str | None]:
    """Return live provider model names when possible, otherwise an error message."""
    resolved_api_key = api_key or get_api_key_from_environment(host_name)
    try:
        if host_name == "gemini":
            return _list_gemini_models(resolved_api_key), None
        if host_name == "openai":
            return _list_openai_models(resolved_api_key), None
        if host_name == "claude":
            return _list_claude_models(resolved_api_key), None
    except Exception as exc:  # noqa: BLE001 - model discovery should degrade to fallback.
        return [], f"{type(exc).__name__}: {exc}"

    return [], None


def get_model_options(host_name: str, api_key: str | None = None) -> tuple[list[str], str]:
    live_models, error = list_provider_models(host_name, api_key)
    if live_models:
        return live_models, "provider"

    fallback_models = get_fallback_model_options(host_name)
    if error:
        return fallback_models, f"fallback: {error}"
    return fallback_models, "fallback"
