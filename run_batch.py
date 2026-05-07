import argparse
import subprocess
import sys
from pathlib import Path

from code_pipeline.contracts import DEFAULT_OLLAMA_MODEL
from code_pipeline.plasmid_paths import get_active_run_dir, get_output_run_dir

PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_ROOT / "main.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run every plasmid in the batch directory.")
    parser.add_argument(
        "--model",
        default=DEFAULT_OLLAMA_MODEL,
        help=f"Ollama model name to run for every plasmid (default: {DEFAULT_OLLAMA_MODEL})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Override retry count for every plasmid in this batch.",
    )
    return parser


def run_all_plasmids(model_name: str, max_retries_override: int | None) -> None:
    plasmid_dir = get_active_run_dir()
    output_dir = get_output_run_dir()

    if not plasmid_dir.exists():
        print("[ERROR] plasmids_batch directory was not found.")
        return

    plasmids = sorted(path for path in plasmid_dir.iterdir() if path.suffix == ".json")
    if not plasmids:
        print("[ERROR] No plasmid JSON files were found.")
        return

    print("=" * 60)
    print(f"[Batch Start] {len(plasmids)} plasmids | model={model_name}")
    print(f"[Active Run] {plasmid_dir}")
    print(f"[Output Run] {output_dir}")
    print("[Notice] Generated Python modules are AI-assisted outputs and should be validated before real use.")
    print("=" * 60)

    for index, plasmid_path in enumerate(plasmids, start=1):
        print("\n" + "=" * 60)
        print(f"[{index}/{len(plasmids)}] Injecting {plasmid_path.name}")
        print("=" * 60)

        command = [sys.executable, str(MAIN_SCRIPT), str(plasmid_path), "--model", model_name]
        if max_retries_override is not None:
            command.extend(["--max-retries", str(max_retries_override)])

        subprocess.run(command, check=False, cwd=str(PROJECT_ROOT))

    print("\n[Batch Complete] All plasmids finished.")


if __name__ == "__main__":
    args = build_parser().parse_args()
    run_all_plasmids(args.model, args.max_retries)
