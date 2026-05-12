import getpass
import json
import os
import re
import subprocess
from pathlib import Path

from google import genai
from google.genai import types

from code_pipeline.contracts import DEFAULT_OLLAMA_MODEL, DEFAULT_PROFILE, build_contract_instruction
from code_pipeline.host_config import (
    HOST_DEFAULT_MODELS as PROVIDER_HOST_DEFAULT_MODELS,
    HOST_MODEL_OPTIONS as PROVIDER_HOST_MODEL_OPTIONS,
    get_model_options,
)
from code_pipeline.plasmid_paths import create_named_run_dirs, get_plasmid_root, set_active_run_name
from profiles import ARCHITECTURE_PROFILES, ArchitectureProfile


OUTPUT_DIR = get_plasmid_root()

HOST_CODE_TO_PROVIDER = {
    "1": "gemini",
    "2": "openai",
    "3": "claude",
    "4": "ollama",
}

HOST_DEFAULT_MODELS = {
    code: PROVIDER_HOST_DEFAULT_MODELS[provider]
    for code, provider in HOST_CODE_TO_PROVIDER.items()
}

HOST_MODEL_OPTIONS = {
    code: PROVIDER_HOST_MODEL_OPTIONS.get(provider, [])
    for code, provider in HOST_CODE_TO_PROVIDER.items()
}


def get_architect_model_options(host_code: str, api_key: str | None = None) -> tuple[list[str], str]:
    provider = HOST_CODE_TO_PROVIDER.get(host_code, "ollama")
    return get_model_options(provider, api_key)

SYSTEM_INSTRUCTION = """
You are a Software Architect.

Break down the user's request into independent Python modules.

Each module must have only one clear responsibility.

Never create overlapping modules with the same responsibility.

Avoid duplicate storage modules, duplicate input modules, duplicate UI modules,
duplicate business logic modules, and duplicate entry modules.

When a familiar application pattern appears, prefer a clean architecture with distinct
loader/storage, input/controller, renderer/visualizer, service/transformer, and entry modules.

For CLI CRUD applications, avoid legacy duplicate module IDs such as:
storage_manager, input_handler, ui_render, task_operations, main_loop.

""" + build_contract_instruction() + """

You MUST output a valid JSON array of objects.

Do not include markdown.

Do not include explanation text.

Return JSON only.

Each object must strictly follow this structure:

{
  "module_id": "unique_name_for_function",
  "prompt": "Specific instruction for a junior dev to write this code. Must include required inputs/outputs.",
  "max_retries_tertiary": 3
}
"""

REFINER_SYSTEM_INSTRUCTION = """
You are a request refiner for an AI software architect pipeline.

Your job is to normalize a user's program request into a clearer implementation-oriented prompt.

Rules:
- Preserve the user's original intent.
- If the request is already sufficiently detailed, keep it mostly unchanged.
- Do not remove explicit requirements.
- Do not add unnecessary features.
- Only clarify ambiguity, fill obvious operational gaps, and normalize the structure.
- Prefer practical details such as likely input/output expectations, runtime style, and user interaction mode when they are strongly implied.
- Keep the result implementation-oriented and suitable for downstream module decomposition.

You MUST return one valid JSON object only.
Do not include markdown.
Do not include explanation text outside JSON.

Return exactly this structure:

{
  "refined_request": "Normalized implementation-oriented request text.",
  "refinement_mode": "preserved",
  "notes": ["Short note about what was preserved or clarified."]
}

Valid refinement_mode values:
- preserved
- light
- expanded
"""


def get_secret(env_names: list[str], prompt_text: str) -> str:
    for env_name in env_names:
        value = os.environ.get(env_name)
        if value:
            return value

    return getpass.getpass(prompt_text)


def parse_json_array(text: str) -> list:
    cleaned = text.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]")

        if start == -1 or end == -1 or end <= start:
            raise ValueError("Could not find a JSON array in the model output.")

        return json.loads(cleaned[start:end + 1])


def parse_json_object(text: str) -> dict:
    cleaned = text.strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError("Could not find a JSON object in the model output.")

        result = json.loads(cleaned[start:end + 1])

    if not isinstance(result, dict):
        raise ValueError("Refiner output must be a JSON object.")

    return result


def build_user_content(user_prompt: str) -> str:
    return f"""
User Request:
{user_prompt}

Please decompose this request following the system rules.
"""


def build_refiner_user_content(user_prompt: str) -> str:
    return f"""
User Request:
{user_prompt}

Normalize this request for downstream software module decomposition.
"""


def normalize_refiner_output(user_prompt: str, raw_output: dict) -> tuple[str, str, list[str]]:
    refined_request = raw_output.get("refined_request", user_prompt)
    refinement_mode = raw_output.get("refinement_mode", "preserved")
    notes = raw_output.get("notes", [])

    if not isinstance(refined_request, str) or not refined_request.strip():
        refined_request = user_prompt

    if refinement_mode not in {"preserved", "light", "expanded"}:
        refinement_mode = "preserved"

    if not isinstance(notes, list):
        notes = []

    normalized_notes = [str(note).strip() for note in notes if str(note).strip()]
    return refined_request.strip(), refinement_mode, normalized_notes


def normalize_module_id(module_id: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", module_id.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def validate_blueprints(dna_list: list[dict]) -> list[dict]:
    if not isinstance(dna_list, list):
        raise ValueError("Architect output must be a JSON array.")

    validated: list[dict] = []
    seen_module_ids: set[str] = set()

    for index, dna in enumerate(dna_list, start=1):
        if not isinstance(dna, dict):
            raise ValueError(f"Blueprint #{index} is not a JSON object.")

        raw_module_id = dna.get("module_id")
        prompt = dna.get("prompt")
        max_retries = dna.get("max_retries_tertiary", 3)

        if not isinstance(raw_module_id, str) or not raw_module_id.strip():
            raise ValueError(f"Blueprint #{index} has an invalid module_id.")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"Blueprint '{raw_module_id}' has an invalid prompt.")
        if not isinstance(max_retries, int):
            raise ValueError(f"Blueprint '{raw_module_id}' has an invalid retry count.")

        module_id = normalize_module_id(raw_module_id)
        if not module_id:
            raise ValueError(f"Blueprint #{index} has an empty normalized module_id.")
        if module_id in seen_module_ids:
            raise ValueError(f"Duplicate module_id detected after normalization: {module_id}")

        seen_module_ids.add(module_id)
        validated.append(
            {
                "module_id": module_id,
                "prompt": prompt.strip(),
                "max_retries_tertiary": max_retries,
            }
        )

    return validated


def score_profile(user_prompt: str, validated_blueprints: list[dict], profile: ArchitectureProfile) -> int:
    lowered_prompt = user_prompt.lower()
    score = sum(1 for keyword in profile["keywords"] if keyword in lowered_prompt)

    canonical_modules = set(profile["canonical_modules"])
    aliases = profile["aliases"]

    for blueprint in validated_blueprints:
        module_id = blueprint["module_id"]
        if module_id in canonical_modules:
            score += 2
        elif module_id in aliases:
            score += 1

    return score


def detect_architecture_profile(
    user_prompt: str,
    validated_blueprints: list[dict],
) -> ArchitectureProfile | None:
    best_profile: ArchitectureProfile | None = None
    best_score = 0

    for profile in ARCHITECTURE_PROFILES.values():
        score = score_profile(user_prompt, validated_blueprints, profile)
        if score > best_score:
            best_profile = profile
            best_score = score

    return best_profile


def normalize_blueprints_with_profile(
    validated_blueprints: list[dict],
    profile: ArchitectureProfile,
) -> tuple[list[dict], list[str]]:
    canonical_modules = profile["canonical_modules"]
    aliases = profile["aliases"]
    blueprint_prompts = profile["blueprint_prompts"]

    normalized_by_module_id: dict[str, dict] = {}
    notes: list[str] = []

    for blueprint in validated_blueprints:
        raw_module_id = blueprint["module_id"]
        canonical_module_id = aliases.get(raw_module_id, raw_module_id)

        if canonical_module_id not in canonical_modules:
            notes.append(f"Dropped non-canonical {profile['name']} module: {raw_module_id}")
            continue

        if canonical_module_id in normalized_by_module_id:
            notes.append(
                f"Removed duplicate {profile['name']} module '{raw_module_id}' in favor of '{canonical_module_id}'"
            )
            continue

        if canonical_module_id != raw_module_id:
            notes.append(f"Renamed module '{raw_module_id}' to canonical '{canonical_module_id}'")

        normalized_by_module_id[canonical_module_id] = {
            "module_id": canonical_module_id,
            "prompt": blueprint_prompts[canonical_module_id],
            "max_retries_tertiary": blueprint.get("max_retries_tertiary", 3),
        }

    normalized_blueprints: list[dict] = []
    for module_id in canonical_modules:
        if module_id not in normalized_by_module_id:
            notes.append(f"Added missing canonical {profile['name']} module: {module_id}")
            normalized_by_module_id[module_id] = {
                "module_id": module_id,
                "prompt": blueprint_prompts[module_id],
                "max_retries_tertiary": 3,
            }

        normalized_blueprints.append(normalized_by_module_id[module_id])

    return normalized_blueprints, notes


def select_architect_host() -> str:
    print("\nArchitect Host Select")
    print("1. Gemini API")
    print("2. OpenAI API")
    print("3. Claude API")
    print("4. Ollama Local")

    return input("Select host: ").strip()


def run_gemini_architect(user_prompt: str, model_name: str | None = None) -> list:
    api_key = get_secret(
        ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "Enter Gemini API Key: ",
    )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name or HOST_DEFAULT_MODELS["1"],
        contents=build_user_content(user_prompt),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
        ),
    )

    return parse_json_array(response.text)


def run_gemini_refiner(user_prompt: str, model_name: str | None = None) -> dict:
    api_key = get_secret(
        ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "Enter Gemini API Key: ",
    )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name or HOST_DEFAULT_MODELS["1"],
        contents=build_refiner_user_content(user_prompt),
        config=types.GenerateContentConfig(
            system_instruction=REFINER_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
        ),
    )

    return parse_json_object(response.text)


def run_openai_architect(user_prompt: str, model_name: str | None = None) -> list:
    from openai import OpenAI

    api_key = get_secret(
        ["OPENAI_API_KEY"],
        "Enter OpenAI API Key: ",
    )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model_name or HOST_DEFAULT_MODELS["2"],
        input=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": build_user_content(user_prompt)},
        ],
    )

    return parse_json_array(response.output_text)


def run_openai_refiner(user_prompt: str, model_name: str | None = None) -> dict:
    from openai import OpenAI

    api_key = get_secret(
        ["OPENAI_API_KEY"],
        "Enter OpenAI API Key: ",
    )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model_name or HOST_DEFAULT_MODELS["2"],
        input=[
            {"role": "system", "content": REFINER_SYSTEM_INSTRUCTION},
            {"role": "user", "content": build_refiner_user_content(user_prompt)},
        ],
    )

    return parse_json_object(response.output_text)


def run_claude_architect(user_prompt: str, model_name: str | None = None) -> list:
    import anthropic

    api_key = get_secret(
        ["ANTHROPIC_API_KEY"],
        "Enter Anthropic API Key: ",
    )

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model_name or HOST_DEFAULT_MODELS["3"],
        max_tokens=4000,
        system=SYSTEM_INSTRUCTION,
        messages=[{"role": "user", "content": build_user_content(user_prompt)}],
    )

    return parse_json_array(response.content[0].text)


def run_claude_refiner(user_prompt: str, model_name: str | None = None) -> dict:
    import anthropic

    api_key = get_secret(
        ["ANTHROPIC_API_KEY"],
        "Enter Anthropic API Key: ",
    )

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model_name or HOST_DEFAULT_MODELS["3"],
        max_tokens=2000,
        system=REFINER_SYSTEM_INSTRUCTION,
        messages=[{"role": "user", "content": build_refiner_user_content(user_prompt)}],
    )

    return parse_json_object(response.content[0].text)


def run_ollama_architect(user_prompt: str, model_name: str | None = None) -> list:
    selected_model = model_name
    if not selected_model:
        selected_model = input(f"Enter Ollama model name [{DEFAULT_OLLAMA_MODEL}]: ").strip()
    if not selected_model:
        selected_model = DEFAULT_OLLAMA_MODEL

    full_prompt = f"""
{SYSTEM_INSTRUCTION}

{build_user_content(user_prompt)}
"""

    result = subprocess.run(
        ["ollama", "run", selected_model],
        input=full_prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return parse_json_array(result.stdout)


def run_ollama_refiner(user_prompt: str, model_name: str | None = None) -> dict:
    selected_model = model_name
    if not selected_model:
        selected_model = input(f"Enter Ollama model name [{DEFAULT_OLLAMA_MODEL}]: ").strip()
    if not selected_model:
        selected_model = DEFAULT_OLLAMA_MODEL

    full_prompt = f"""
{REFINER_SYSTEM_INSTRUCTION}

{build_refiner_user_content(user_prompt)}
"""

    result = subprocess.run(
        ["ollama", "run", selected_model],
        input=full_prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return parse_json_object(result.stdout)


def run_architect_with_host(user_prompt: str, host: str, model_name: str | None = None) -> list:
    if host == "1":
        return run_gemini_architect(user_prompt, model_name)
    if host == "2":
        return run_openai_architect(user_prompt, model_name)
    if host == "3":
        return run_claude_architect(user_prompt, model_name)
    if host == "4":
        return run_ollama_architect(user_prompt, model_name)

    raise ValueError("Invalid Architect Host selection.")


def run_refiner_with_host(user_prompt: str, host: str, model_name: str | None = None) -> dict:
    if host == "1":
        return run_gemini_refiner(user_prompt, model_name)
    if host == "2":
        return run_openai_refiner(user_prompt, model_name)
    if host == "3":
        return run_claude_refiner(user_prompt, model_name)
    if host == "4":
        return run_ollama_refiner(user_prompt, model_name)

    raise ValueError("Invalid Refiner Host selection.")


def refine_user_request(
    user_prompt: str,
    host: str,
    model_name: str | None = None,
) -> tuple[str, str, list[str]]:
    raw_output = run_refiner_with_host(user_prompt, host, model_name)
    return normalize_refiner_output(user_prompt, raw_output)


def prepare_blueprints(
    user_prompt: str,
    host: str,
    model_name: str | None = None,
) -> tuple[list[dict], list[str], str | None, str, str, list[str]]:
    refinement_notes: list[str] = []
    try:
        refined_request, refinement_mode, refinement_notes = refine_user_request(
            user_prompt,
            host,
            model_name,
        )
    except Exception as exc:
        refined_request = user_prompt.strip()
        refinement_mode = "preserved"
        refinement_notes = [f"Refiner fallback applied: {exc}"]

    raw_blueprints = run_architect_with_host(refined_request, host, model_name)
    validated_blueprints = validate_blueprints(raw_blueprints)
    profile = detect_architecture_profile(refined_request, validated_blueprints)

    if profile:
        normalized_blueprints, notes = normalize_blueprints_with_profile(validated_blueprints, profile)
        return (
            normalized_blueprints,
            notes,
            profile["name"],
            refined_request,
            refinement_mode,
            refinement_notes,
        )

    return validated_blueprints, [], None, refined_request, refinement_mode, refinement_notes


def create_plasmids(
    dna_list: list[dict],
    profile_name: str | None,
    original_request: str | None = None,
    refined_request: str | None = None,
    refinement_mode: str | None = None,
    refinement_notes: list[str] | None = None,
    run_label: str | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_name, run_dir, _output_run_dir = create_named_run_dirs(run_label, OUTPUT_DIR.parent)

    for dna in dna_list:
        dna_with_profile = dict(dna)
        dna_with_profile["profile"] = profile_name or DEFAULT_PROFILE
        dna_with_profile["run_name"] = run_name
        if original_request is not None:
            dna_with_profile["original_request"] = original_request
        if refined_request is not None:
            dna_with_profile["refined_request"] = refined_request
        if refinement_mode is not None:
            dna_with_profile["refinement_mode"] = refinement_mode
        if refinement_notes is not None:
            dna_with_profile["refinement_notes"] = refinement_notes
        module_id = dna_with_profile["module_id"]
        filename = run_dir / f"plasmid_{module_id}.json"

        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(dna_with_profile, handle, indent=2, ensure_ascii=False)

        print(f"[DNA Synthesized] Created blueprint: {filename}")

    set_active_run_name(run_name, OUTPUT_DIR.parent)
    print(f"[DNA Activated] Active plasmid run: {run_dir}")
    return run_dir


if __name__ == "__main__":
    print("=" * 60)
    print(" DECC Pipeline: System Architect")
    print("=" * 60)
    print("[Notice] Architect output is AI-generated. Review plasmid prompts and module IDs before batch execution.")

    user_idea = input("\nEnter the program idea you want to implement: ")
    host = select_architect_host()

    print("\n[Architect] Analyzing request and synthesizing plasmids...")

    try:
        dna_blueprints, notes, profile_name, refined_request, refinement_mode, refinement_notes = prepare_blueprints(
            user_idea,
            host,
        )
        print(f"\n[Architect] Successfully prepared {len(dna_blueprints)} modules.")
        print(f"[Architect] Refinement mode: {refinement_mode}")

        if profile_name:
            print(f"[Architect] Applied architecture profile: {profile_name}")

        if refined_request.strip() != user_idea.strip():
            print("[Architect] Refined request:")
            print(refined_request)

        if refinement_notes:
            print("[Architect] Refinement notes:")
            for note in refinement_notes:
                print(f" - {note}")

        if notes:
            print("[Architect] Normalization notes:")
            for note in notes:
                print(f" - {note}")

        run_label = input("Optional run name/project name: ").strip()
        create_plasmids(
            dna_blueprints,
            profile_name,
            original_request=user_idea,
            refined_request=refined_request,
            refinement_mode=refinement_mode,
            refinement_notes=refinement_notes,
            run_label=run_label or None,
        )
        print("\n[NEXT STEP] Run run_batch.py to generate code from the synthesized plasmids.")

    except Exception as e:
        print(f"\n[FAILURE] {e}")
