import argparse
import json
from pathlib import Path

from code_pipeline.connectors.local_cli import LocalCliConnector
from code_pipeline.contracts import DEFAULT_OLLAMA_MODEL, DEFAULT_PROFILE
from code_pipeline.protocol import run_protocol


def load_dna(file_path: str) -> dict:
    dna_path = Path(file_path)
    if not dna_path.exists():
        raise FileNotFoundError(f"[ERROR] DNA file '{file_path}' not found.")

    with dna_path.open("r", encoding="utf-8") as handle:
        dna_data = json.load(handle)

    required_keys = {"module_id", "prompt"}
    missing_keys = required_keys - set(dna_data)
    if missing_keys:
        missing_list = ", ".join(sorted(missing_keys))
        raise ValueError(f"[ERROR] DNA file is missing required keys: {missing_list}")

    if "profile" not in dna_data:
        dna_data["profile"] = DEFAULT_PROFILE
    if "run_name" not in dna_data:
        dna_data["run_name"] = None

    return dna_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DECC Pipeline Executor")
    parser.add_argument("dna_file", help="Path to the JSON DNA file")
    parser.add_argument(
        "--model",
        default=DEFAULT_OLLAMA_MODEL,
        help=f"Ollama model name to run (default: {DEFAULT_OLLAMA_MODEL})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Override the retry count defined in the DNA file.",
    )
    return parser


def execute_dna(dna_file: str, model_name: str, max_retries_override: int | None) -> str | None:
    print(f"\n[Injection] Loading genetic sequence from {dna_file}...")
    dna = load_dna(dna_file)

    connector = LocalCliConnector(
        command="ollama",
        base_args=["run", model_name],
    )
    max_retries = max_retries_override or dna.get("max_retries_tertiary", 3)

    print(f"\n>>> Single Phase Cultivation: {model_name}")
    print(f"[Profile] {dna['profile']}")
    if dna.get("run_name"):
        print(f"[Run] {dna['run_name']}")
    print(f"[Module] {dna['module_id']}")

    return run_protocol(
        connector=connector,
        prompt=dna["prompt"],
        module_id=dna["module_id"],
        profile=dna["profile"],
        run_name=dna.get("run_name"),
        max_retries=max_retries,
    )


if __name__ == "__main__":
    args = build_parser().parse_args()
    result_path = execute_dna(args.dna_file, args.model, args.max_retries)

    if result_path:
        print(f"\n[FINAL SUCCESS] High-purity product ready: {result_path}")
    else:
        print("\n[FINAL FAILURE] The host failed to generate valid code after all retries.")
