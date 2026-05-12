import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from code_pipeline.contracts import DEFAULT_OLLAMA_MODEL
from code_pipeline.host_config import DEFAULT_HOST, HOST_DEFAULT_MODELS
from code_pipeline.plasmid_paths import get_active_run_dir, get_output_run_dir

PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_ROOT / "main.py"


def classify_result(return_code: int, combined_output: str) -> str:
    if return_code == 0 and "[FINAL SUCCESS]" in combined_output:
        return "success"
    if "[Lane 1 FAIL]" in combined_output:
        return "syntax_failed"
    if "[Lane 2 FAIL]" in combined_output:
        return "artifact_interface_failed"
    if "[Lane 2B FAIL]" in combined_output:
        return "module_contract_failed"
    if "[FINAL FAILURE]" in combined_output:
        return "generation_failed"
    if return_code != 0:
        return "process_failed"
    return "unknown"


def extract_log_summary(text: str, max_lines: int = 12) -> list[str]:
    interesting_markers = (
        "[ERROR]",
        "[WARN]",
        "[Lane",
        "[Pipeline FAILED]",
        "[FINAL FAILURE]",
        "Traceback",
        "Error:",
        "Exception:",
    )
    lines = [line for line in text.splitlines() if any(marker in line for marker in interesting_markers)]
    if not lines:
        lines = text.splitlines()[-max_lines:]
    return lines[-max_lines:]


def load_module_id(plasmid_path: Path) -> str:
    try:
        data = json.loads(plasmid_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return plasmid_path.stem.replace("plasmid_", "", 1)
    module_id = data.get("module_id")
    return module_id if isinstance(module_id, str) and module_id else plasmid_path.stem


def write_batch_reports(output_dir: Path, report: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "batch_report.json"
    md_path = output_dir / "batch_report.md"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# DECC Batch Report",
        "",
        f"- Run: `{report['run_name']}`",
        f"- Host: `{report['host']}`",
        f"- Model: `{report['model']}`",
        f"- Started: `{report['started_at']}`",
        f"- Finished: `{report['finished_at']}`",
        f"- Success: `{report['success_count']}`",
        f"- Failed: `{report['failure_count']}`",
        "",
        "## Modules",
        "",
    ]

    for item in report["modules"]:
        lines.extend(
            [
                f"### {item['module_id']}",
                "",
                f"- Plasmid: `{item['plasmid_file']}`",
                f"- Status: `{item['status']}`",
                f"- Return code: `{item['return_code']}`",
                f"- Duration: `{item['duration_seconds']}` seconds",
                "",
            ]
        )
        if item["summary"]:
            lines.append("Summary:")
            lines.append("")
            lines.extend(f"- {line}" for line in item["summary"])
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run every plasmid in the batch directory.")
    parser.add_argument(
        "--host",
        choices=["ollama", "gemini", "openai", "claude"],
        default=DEFAULT_HOST,
        help=f"Generation host to run for every plasmid (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name to run for every plasmid with the selected generation host.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Override retry count for every plasmid in this batch.",
    )
    return parser


def run_all_plasmids(host_name: str, model_name: str | None, max_retries_override: int | None) -> bool:
    plasmid_dir = get_active_run_dir(PROJECT_ROOT)
    output_dir = get_output_run_dir(PROJECT_ROOT)
    resolved_model = model_name or HOST_DEFAULT_MODELS.get(host_name, DEFAULT_OLLAMA_MODEL)

    if not plasmid_dir.exists():
        print("[ERROR] plasmids_batch directory was not found.")
        return False

    plasmids = sorted(path for path in plasmid_dir.iterdir() if path.suffix == ".json")
    if not plasmids:
        print("[ERROR] No plasmid JSON files were found.")
        return False

    print("=" * 60)
    print(f"[Batch Start] {len(plasmids)} plasmids | host={host_name} | model={resolved_model}")
    print(f"[Active Run] {plasmid_dir}")
    print(f"[Output Run] {output_dir}")
    print("[Notice] Generated Python modules are AI-assisted outputs and should be validated before real use.")
    print("=" * 60)

    started_at = datetime.now(timezone.utc)
    module_results: list[dict] = []

    for index, plasmid_path in enumerate(plasmids, start=1):
        print("\n" + "=" * 60)
        print(f"[{index}/{len(plasmids)}] Injecting {plasmid_path.name}")
        print("=" * 60)

        module_id = load_module_id(plasmid_path)
        command = [
            sys.executable,
            str(MAIN_SCRIPT),
            str(plasmid_path),
            "--host",
            host_name,
            "--model",
            resolved_model,
        ]
        if max_retries_override is not None:
            command.extend(["--max-retries", str(max_retries_override)])

        started = time.monotonic()
        result = subprocess.run(
            command,
            check=False,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        duration_seconds = round(time.monotonic() - started, 2)
        combined_output = result.stdout
        if result.stderr:
            combined_output += "\n[stderr]\n" + result.stderr

        print(combined_output)

        status = classify_result(result.returncode, combined_output)
        module_results.append(
            {
                "module_id": module_id,
                "plasmid_file": plasmid_path.name,
                "status": status,
                "return_code": result.returncode,
                "duration_seconds": duration_seconds,
                "summary": extract_log_summary(combined_output),
            }
        )

    success_count = sum(1 for item in module_results if item["status"] == "success")
    failure_count = len(module_results) - success_count
    finished_at = datetime.now(timezone.utc)
    report = {
        "run_name": output_dir.name,
        "host": host_name,
        "model": resolved_model,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "success_count": success_count,
        "failure_count": failure_count,
        "modules": module_results,
    }
    write_batch_reports(output_dir, report)

    print("\n[Batch Complete] All plasmids finished.")
    print(f"[Batch Report] {output_dir / 'batch_report.json'}")
    print(f"[Batch Summary] success={success_count} failed={failure_count}")
    return failure_count == 0


if __name__ == "__main__":
    args = build_parser().parse_args()
    batch_ok = run_all_plasmids(args.host, args.model, args.max_retries)
    raise SystemExit(0 if batch_ok else 1)
