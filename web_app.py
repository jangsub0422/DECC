"""
Streamlit wrapper for the DECC Pipeline Architect.

This file provides a multi-line web input UI for architect.py without changing
core pipeline logic. It generates plasmid JSON files through architect.prepare_blueprints()
and architect.create_plasmids().
"""

from __future__ import annotations

import builtins
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import architect
from code_pipeline import __version__
from code_pipeline.host_config import HOST_DEFAULT_MODELS as GENERATION_HOST_DEFAULT_MODELS
from code_pipeline.host_config import HOST_DISPLAY_NAMES as GENERATION_HOST_DISPLAY_NAMES
from code_pipeline.host_config import HOST_MODEL_OPTIONS as GENERATION_HOST_MODEL_OPTIONS
from code_pipeline.plasmid_paths import (
    get_active_run_dir,
    get_output_run_dir,
    get_plasmid_root,
    get_plasmid_runs_dir,
    get_output_runs_dir,
    set_active_run_dir,
)


architect.OUTPUT_DIR = get_plasmid_root(PROJECT_ROOT)

PLASMID_DIR = get_plasmid_root(PROJECT_ROOT)
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FINAL_APP = PROJECT_ROOT / "final_app.py"
RUN_BATCH_SCRIPT = PROJECT_ROOT / "run_batch.py"
INTEGRATION_SCRIPT = PROJECT_ROOT / "integration.py"

HOST_OPTIONS = {
    "Gemini API": "1",
    "OpenAI API": "2",
    "Claude API": "3",
    "Ollama Local": "4",
}
GENERATION_HOST_OPTIONS = {label: host_name for host_name, label in GENERATION_HOST_DISPLAY_NAMES.items()}


@contextmanager
def patched_input(response: str) -> Iterator[None]:
    """
    Temporarily replace input() so architect.run_ollama_architect() can receive
    a model name from the web UI instead of blocking on terminal input.
    """
    original_input = builtins.input
    builtins.input = lambda _prompt="": response
    try:
        yield
    finally:
        builtins.input = original_input


@contextmanager
def temporary_host_environment(host_code: str, api_key: str) -> Iterator[None]:
    """
    Temporarily inject API credentials into the process environment so the
    existing architect.py get_secret() function can read them.
    """
    previous_values: dict[str, str | None] = {}
    cleaned_key = api_key.strip()
    env_updates: dict[str, str] = {}

    if cleaned_key:
        if host_code == "1":
            env_updates = {
                "GOOGLE_API_KEY": cleaned_key,
                "GEMINI_API_KEY": cleaned_key,
            }
        elif host_code == "2":
            env_updates = {
                "OPENAI_API_KEY": cleaned_key,
            }
        elif host_code == "3":
            env_updates = {
                "ANTHROPIC_API_KEY": cleaned_key,
            }

    for key, value in env_updates.items():
        previous_values[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        yield
    finally:
        for key in env_updates:
            previous_value = previous_values.get(key)
            if previous_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous_value


def generate_plasmids(
    user_prompt: str,
    host_code: str,
    api_key: str,
    selected_model: str,
    run_label: str,
) -> dict:
    """
    Run the Architect stage and persist plasmid JSON files.
    Returns a small summary used by the Streamlit UI.
    """
    with temporary_host_environment(host_code, api_key):
        if host_code == "4":
            with patched_input(selected_model.strip()):
                blueprints, notes, profile_name = architect.prepare_blueprints(
                    user_prompt,
                    host_code,
                    selected_model.strip(),
                )
        else:
            blueprints, notes, profile_name = architect.prepare_blueprints(
                user_prompt,
                host_code,
                selected_model.strip() or None,
            )

    run_dir = architect.create_plasmids(blueprints, profile_name, run_label.strip() or None)

    return {
        "profile": profile_name or "generic",
        "run_dir": str(run_dir),
        "module_count": len(blueprints),
        "modules": [blueprint["module_id"] for blueprint in blueprints],
        "notes": notes,
        "blueprints": blueprints,
    }


def read_plasmids() -> list[dict]:
    """
    Read current plasmid JSON files from plasmids_batch/ for display.
    """
    active_run_dir = get_active_run_dir(PROJECT_ROOT)
    if not active_run_dir.exists():
        return []

    plasmids: list[dict] = []
    for path in sorted(active_run_dir.glob("plasmid_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_file"] = str(path)
            plasmids.append(data)
        except json.JSONDecodeError:
            plasmids.append({"_file": str(path), "_error": "Invalid JSON"})
    return plasmids


def list_run_directories() -> list[Path]:
    runs_dir = get_plasmid_runs_dir(PROJECT_ROOT)
    if not runs_dir.exists():
        return []
    return sorted(path for path in runs_dir.iterdir() if path.is_dir())


def read_plasmids_from_run(run_dir: Path) -> list[dict]:
    if not run_dir.exists():
        return []

    plasmids: list[dict] = []
    for path in sorted(run_dir.glob("plasmid_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_file"] = str(path)
            plasmids.append(data)
        except json.JSONDecodeError:
            plasmids.append({"_file": str(path), "_error": "Invalid JSON"})
    return plasmids


def list_output_files(run_dir_name: str) -> list[Path]:
    output_run_dir = get_output_runs_dir(PROJECT_ROOT) / run_dir_name
    if not output_run_dir.exists():
        return []
    return sorted(path for path in output_run_dir.glob("*.py"))


def read_text_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def list_legacy_root_plasmids() -> list[Path]:
    if not PLASMID_DIR.exists():
        return []
    return sorted(PLASMID_DIR.glob("plasmid_*.json"))


def list_legacy_root_outputs() -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []
    return sorted(OUTPUT_DIR.glob("*.py"))


def clear_directory_files(paths: list[Path]) -> int:
    removed = 0
    for path in paths:
        if path.exists():
            path.unlink()
            removed += 1
    return removed


def clear_pycache_dirs(base_dir: Path) -> int:
    removed = 0
    for pycache_dir in base_dir.rglob("__pycache__"):
        for child in pycache_dir.iterdir():
            if child.is_file():
                child.unlink()
        pycache_dir.rmdir()
        removed += 1
    return removed


def run_command(command: list[str], extra_env: dict[str, str] | None = None) -> tuple[int, str]:
    """
    Run a pipeline command from the project root and return combined stdout/stderr.
    """
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    output = result.stdout
    if result.stderr:
        output += "\n[stderr]\n" + result.stderr
    return result.returncode, output


def render_architect_tab() -> None:
    """
    Render the main multi-line Architect form.
    """
    st.subheader("Architect")
    st.caption("Multi-line natural language input to profile-normalized plasmid JSON files")
    st.warning(
        "AI-generated blueprints may contain mistakes. Review plasmids before running batch generation."
    )

    with st.form("architect_form"):
        user_prompt = st.text_area(
            "Program specification",
            height=320,
            placeholder=(
                "Example:\n"
                "Create a CLI program that converts a CSV file into a JSON file.\n"
                "Ask for the input CSV path and output JSON path.\n"
                "Read rows as dictionaries and save the result as JSON."
            ),
        )
        run_label = st.text_input(
            "Run name / project name",
            placeholder="example: csv_to_json_converter",
            help="Used to group plasmids and generated Python files into the same named run bundle.",
        )

        selected_host_label = st.selectbox("Architect Host", list(HOST_OPTIONS.keys()))
        host_code = HOST_OPTIONS[selected_host_label]

        api_key = ""
        selected_model = ""
        if host_code in {"1", "2", "3"}:
            api_key = st.text_input("API key", type="password")
            model_options = architect.HOST_MODEL_OPTIONS.get(host_code, [])
            default_model = architect.HOST_DEFAULT_MODELS[host_code]
            if model_options:
                selected_model = st.selectbox(
                    "Model",
                    model_options,
                    index=model_options.index(default_model) if default_model in model_options else 0,
                    help="Update architect.HOST_MODEL_OPTIONS in architect.py when provider model choices change.",
                )
            else:
                selected_model = st.text_input("Model", value=default_model)
        else:
            selected_model = st.text_input(
                "Ollama model",
                value=architect.HOST_DEFAULT_MODELS["4"],
                help="Used only for Ollama Local.",
            )

        submitted = st.form_submit_button("Generate plasmids")

    if submitted:
        if not user_prompt.strip():
            st.error("Program specification is empty.")
            return

        if host_code in {"1", "2", "3"} and not api_key.strip():
            st.error("API key is required for the selected API host.")
            return

        with st.spinner("Running Architect stage..."):
            try:
                summary = generate_plasmids(user_prompt, host_code, api_key, selected_model, run_label)
            except Exception as exc:  # noqa: BLE001 - UI should show pipeline errors directly.
                st.error(f"Architect failed: {exc}")
                return

        st.success(f"Generated {summary['module_count']} plasmids.")
        st.write("Profile:", summary["profile"])
        st.write("Run directory:", summary["run_dir"])
        st.write("Modules:", ", ".join(summary["modules"]))

        if summary["notes"]:
            st.write("Normalization notes:")
            for note in summary["notes"]:
                st.write("-", note)

        with st.expander("Generated blueprint objects"):
            st.json(summary["blueprints"])


def render_plasmids_tab() -> None:
    """
    Show current plasmid JSON files so the user can review the actual contracts
    before running batch generation.
    """
    st.subheader("Current plasmids")
    st.caption("Check function names, prompts, and profile metadata before generation.")
    plasmids = read_plasmids()
    active_run_dir = get_active_run_dir(PROJECT_ROOT)

    st.caption(f"Active run: {active_run_dir}")

    if not plasmids:
        st.info("No plasmid JSON files found in plasmids_batch/.")
        return

    for plasmid in plasmids:
        st.markdown(f"### {plasmid.get('_file', 'unknown file')}")
        st.json(plasmid)


def render_runs_tab() -> None:
    """
    Show timestamped plasmid runs and allow switching the active run.
    """
    st.subheader("Plasmid runs")
    st.caption("Older runs are preserved for comparison. Confirm the active run before running batch or integration.")

    run_dirs = list_run_directories()
    active_run_dir = get_active_run_dir(PROJECT_ROOT)

    if not run_dirs:
        st.info("No timestamped plasmid runs found yet.")
        return

    run_options = [run_dir.name for run_dir in run_dirs]
    active_name = active_run_dir.name if active_run_dir.name in run_options else run_options[-1]

    selected_run_name = st.selectbox(
        "Select run",
        run_options,
        index=run_options.index(active_name),
    )
    selected_run_dir = next(run_dir for run_dir in run_dirs if run_dir.name == selected_run_name)

    col1, col2 = st.columns(2)
    with col1:
        st.write("Active run:", active_run_dir.name)
    with col2:
        if st.button("Set selected run active"):
            set_active_run_dir(selected_run_dir, PROJECT_ROOT)
            st.success(f"Active run updated to {selected_run_dir.name}")
            st.rerun()

    st.caption(str(selected_run_dir))

    plasmids = read_plasmids_from_run(selected_run_dir)
    if not plasmids:
        st.info("No plasmid JSON files found in the selected run.")
        return

    for plasmid in plasmids:
        st.markdown(f"### {plasmid.get('_file', 'unknown file')}")
        st.json(plasmid)

    output_files = list_output_files(selected_run_dir.name)
    st.markdown("### Output files")
    if not output_files:
        st.info("No generated Python files found for the selected run yet.")
    else:
        for output_file in output_files:
            st.write(str(output_file))

    final_app_snapshot = get_output_runs_dir(PROJECT_ROOT) / selected_run_dir.name / "final_app.py"
    st.markdown("### final_app snapshot")
    final_app_text = read_text_file(final_app_snapshot)
    if final_app_text is None:
        st.info("No final_app.py snapshot found for the selected run yet.")
    else:
        st.code(final_app_text, language="python")


def render_pipeline_tab() -> None:
    """
    Optional runner for run_batch.py and integration.py. These can take time
    because local LLM generation is executed through Ollama.
    """
    st.subheader("Pipeline runner")
    st.caption("Use this after reviewing plasmids. Commands are executed in the project root.")
    st.warning(
        "Generated Python files and integration results are AI-assisted outputs. Verify behavior before real use."
    )
    st.info("The recommended default path remains local Ollama. API-based module generation is available but may incur usage cost.")
    active_output_dir = get_output_run_dir(PROJECT_ROOT)
    st.write("Active output run:", str(active_output_dir))

    generation_host_label = st.selectbox("Generation Host", list(GENERATION_HOST_OPTIONS.keys()))
    generation_host = GENERATION_HOST_OPTIONS[generation_host_label]
    generation_api_key = ""

    if generation_host in {"gemini", "openai", "claude"}:
        generation_api_key = st.text_input("Generation API key", type="password")
        model_options = GENERATION_HOST_MODEL_OPTIONS.get(generation_host, [])
        default_model = GENERATION_HOST_DEFAULT_MODELS[generation_host]
        if model_options:
            generation_model = st.selectbox(
                "Generation Model",
                model_options,
                index=model_options.index(default_model) if default_model in model_options else 0,
            )
        else:
            generation_model = st.text_input("Generation Model", value=default_model)
    else:
        generation_model = st.text_input(
            "Ollama generation model",
            value=GENERATION_HOST_DEFAULT_MODELS["ollama"],
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        clear_outputs = st.button("Clear outputs/")
    with col2:
        run_batch = st.button("Run batch")
    with col3:
        run_integration = st.button("Run integration")

    if clear_outputs:
        if active_output_dir.exists():
            for path in active_output_dir.glob("*.py"):
                path.unlink()
            st.success("Deleted generated Python files in the active output run.")
        else:
            st.info("Active output run does not exist.")

    if run_batch:
        if generation_host in {"gemini", "openai", "claude"} and not generation_api_key.strip():
            st.error("Generation API key is required for the selected API host.")
            return

        extra_env: dict[str, str] | None = None
        if generation_host == "gemini":
            extra_env = {
                "GOOGLE_API_KEY": generation_api_key.strip(),
                "GEMINI_API_KEY": generation_api_key.strip(),
            }
        elif generation_host == "openai":
            extra_env = {"OPENAI_API_KEY": generation_api_key.strip()}
        elif generation_host == "claude":
            extra_env = {"ANTHROPIC_API_KEY": generation_api_key.strip()}

        with st.spinner("Running run_batch.py..."):
            code, output = run_command(
                [
                    sys.executable,
                    str(RUN_BATCH_SCRIPT),
                    "--host",
                    generation_host,
                    "--model",
                    generation_model,
                ],
                extra_env=extra_env,
            )
        st.code(output, language="text")
        if code == 0:
            st.success("run_batch.py finished.")
        else:
            st.error(f"run_batch.py exited with code {code}.")

    if run_integration:
        with st.spinner("Running integration..."):
            code, output = run_command([sys.executable, str(INTEGRATION_SCRIPT)])
        st.code(output, language="text")
        if code == 0:
            st.success("integration finished.")
        else:
            st.error(f"integration exited with code {code}.")

    if FINAL_APP.exists():
        with st.expander("final_app.py"):
            st.code(FINAL_APP.read_text(encoding="utf-8"), language="python")


def render_maintenance_tab() -> None:
    """
    Cleanup tools for stale root-level files and temporary caches.
    """
    st.subheader("Maintenance")
    st.caption("Cleanup tools remove stale local artifacts only. Run history folders are intended to be preserved unless you delete them manually.")

    legacy_plasmids = list_legacy_root_plasmids()
    legacy_outputs = list_legacy_root_outputs()

    st.write("Legacy root plasmids:", len(legacy_plasmids))
    st.write("Legacy root outputs:", len(legacy_outputs))

    col1, col2 = st.columns(2)
    with col1:
        clear_legacy = st.button("Clear legacy root files")
    with col2:
        clear_pycache = st.button("Clear __pycache__")

    if clear_legacy:
        removed_plasmids = clear_directory_files(legacy_plasmids)
        removed_outputs = clear_directory_files(legacy_outputs)
        st.success(
            f"Removed {removed_plasmids} legacy plasmid JSON files and {removed_outputs} legacy output Python files."
        )

    if clear_pycache:
        removed_dirs = clear_pycache_dirs(PROJECT_ROOT)
        st.success(f"Removed {removed_dirs} __pycache__ directories.")

    if legacy_plasmids:
        with st.expander("Legacy root plasmids"):
            for path in legacy_plasmids:
                st.write(str(path))

    if legacy_outputs:
        with st.expander("Legacy root outputs"):
            for path in legacy_outputs:
                st.write(str(path))


def main() -> None:
    """
    Streamlit entry point.
    """
    st.set_page_config(page_title="DECC Pipeline", layout="wide")
    st.title(f"DECC Pipeline Web Wrapper ({__version__})")
    st.caption(str(PROJECT_ROOT))
    st.info("Note: This wrapper drives an AI-assisted generation pipeline. Review generated outputs before production or sensitive use.")

    architect_tab, plasmids_tab, runs_tab, pipeline_tab, maintenance_tab = st.tabs(
        ["Architect", "Current Plasmids", "Runs", "Pipeline", "Maintenance"]
    )

    with architect_tab:
        render_architect_tab()
    with plasmids_tab:
        render_plasmids_tab()
    with runs_tab:
        render_runs_tab()
    with pipeline_tab:
        render_pipeline_tab()
    with maintenance_tab:
        render_maintenance_tab()


if __name__ == "__main__":
    main()
