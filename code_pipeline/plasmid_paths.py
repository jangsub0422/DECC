from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


PLASMID_ROOT_DIRNAME = "plasmids_batch"
OUTPUT_ROOT_DIRNAME = "outputs"
RUNS_DIRNAME = "runs"
ACTIVE_RUN_FILENAME = "ACTIVE_RUN.txt"


def sanitize_run_label(label: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", label.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "run"


def build_run_name(label: str | None = None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if label and label.strip():
        return f"{sanitize_run_label(label)}_{timestamp}"
    return timestamp


def get_plasmid_root(base_dir: Path | None = None) -> Path:
    root_base = base_dir or Path.cwd()
    return root_base / PLASMID_ROOT_DIRNAME


def get_output_root(base_dir: Path | None = None) -> Path:
    root_base = base_dir or Path.cwd()
    return root_base / OUTPUT_ROOT_DIRNAME


def get_plasmid_runs_dir(base_dir: Path | None = None) -> Path:
    return get_plasmid_root(base_dir) / RUNS_DIRNAME


def get_output_runs_dir(base_dir: Path | None = None) -> Path:
    return get_output_root(base_dir) / RUNS_DIRNAME


def get_active_run_file(base_dir: Path | None = None) -> Path:
    return get_plasmid_root(base_dir) / ACTIVE_RUN_FILENAME


def create_named_run_dirs(run_label: str | None = None, base_dir: Path | None = None) -> tuple[str, Path, Path]:
    run_name = build_run_name(run_label)

    plasmid_runs_dir = get_plasmid_runs_dir(base_dir)
    output_runs_dir = get_output_runs_dir(base_dir)
    plasmid_runs_dir.mkdir(parents=True, exist_ok=True)
    output_runs_dir.mkdir(parents=True, exist_ok=True)

    plasmid_run_dir = plasmid_runs_dir / run_name
    output_run_dir = output_runs_dir / run_name
    suffix = 1

    while plasmid_run_dir.exists() or output_run_dir.exists():
        candidate_name = f"{run_name}_{suffix:02d}"
        plasmid_run_dir = plasmid_runs_dir / candidate_name
        output_run_dir = output_runs_dir / candidate_name
        suffix += 1

    plasmid_run_dir.mkdir(parents=True, exist_ok=False)
    output_run_dir.mkdir(parents=True, exist_ok=False)
    return plasmid_run_dir.name, plasmid_run_dir, output_run_dir


def set_active_run_name(run_name: str, base_dir: Path | None = None) -> None:
    active_run_file = get_active_run_file(base_dir)
    active_run_file.parent.mkdir(parents=True, exist_ok=True)
    active_run_file.write_text(run_name, encoding="utf-8")


def set_active_run_dir(run_dir: Path, base_dir: Path | None = None) -> None:
    set_active_run_name(run_dir.name, base_dir)


def get_active_run_name(base_dir: Path | None = None) -> str | None:
    active_run_file = get_active_run_file(base_dir)
    if active_run_file.exists():
        run_name = active_run_file.read_text(encoding="utf-8").strip()
        if run_name:
            return run_name
    return None


def get_active_run_dir(base_dir: Path | None = None) -> Path:
    root_dir = get_plasmid_root(base_dir)
    run_name = get_active_run_name(base_dir)

    if run_name:
        candidate = get_plasmid_runs_dir(base_dir) / run_name
        if candidate.exists():
            return candidate

    runs_dir = get_plasmid_runs_dir(base_dir)
    if runs_dir.exists():
        run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir())
        if run_dirs:
            return run_dirs[-1]

    return root_dir


def get_output_run_dir(base_dir: Path | None = None) -> Path:
    root_dir = get_output_root(base_dir)
    run_name = get_active_run_name(base_dir)

    if run_name:
        candidate = get_output_runs_dir(base_dir) / run_name
        if candidate.exists():
            return candidate

    runs_dir = get_output_runs_dir(base_dir)
    if runs_dir.exists():
        run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir())
        if run_dirs:
            return run_dirs[-1]

    return root_dir

