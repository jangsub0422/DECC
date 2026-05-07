from typing import Optional

from .assay import check_interface, check_required_functions, check_syntax, transfer_artifact
from .connectors.base import HostConnector
from .contracts import DEFAULT_PROFILE
from .models import CodeArtifact


def run_protocol(
    connector: HostConnector,
    prompt: str,
    module_id: str = "module_001",
    profile: str = DEFAULT_PROFILE,
    run_name: str | None = None,
    max_retries: int = 3,
) -> Optional[str]:
    """Run generation, validation, and artifact transfer for one module."""
    sep = "=" * 60
    print(f"\n{sep}\n Pipeline Start | Host: {connector.connector_name}\n{sep}")
    print(f"[Profile] {profile}")
    if run_name:
        print(f"[Run] {run_name}")

    base_prompt = prompt
    current_prompt = base_prompt

    for attempt in range(1, max_retries + 1):
        print(f"\n[Batch {attempt}/{max_retries}] Cultivating...")

        raw_output = connector.cultivate(current_prompt)

        code = raw_output
        if "```" in code:
            code = "\n".join(
                [line for line in code.split("\n") if not line.strip().startswith("```")]
            ).strip()

        lane1_ok, lane1_err = check_syntax(code)
        if not lane1_ok:
            print(f"[Lane 1 FAIL] Inclusion Body: {lane1_err}")
            current_prompt = (
                base_prompt
                + "\n\n[SYSTEM FEEDBACK] Your previous code generated this SyntaxError:\n"
                + f"{lane1_err}\n"
                + "Please analyze the error and return corrected Python code only."
            )
            continue

        raw_payload = {
            "version": "1.0",
            "profile": profile,
            "run_name": run_name,
            "module_id": module_id,
            "payload": {"code": code, "source": connector.connector_name},
        }
        lane2_ok, lane2_err = check_interface(raw_payload)
        if not lane2_ok:
            print(f"[Lane 2 FAIL] Misfolding: {lane2_err}")
            continue

        lane2b_ok, lane2b_err = check_required_functions(code, profile, module_id)
        if not lane2b_ok:
            print(f"[Lane 2B FAIL] Contract drift: {lane2b_err}")
            current_prompt = (
                base_prompt
                + "\n\n[SYSTEM FEEDBACK] Your previous code failed the required module export contract:\n"
                + f"{lane2b_err}\n"
                + "Return corrected Python code with the required function names and exact parameter order."
            )
            continue

        artifact = CodeArtifact(**raw_payload)
        output_path = transfer_artifact(artifact)
        print(f"[Lane 3] Transfer complete: {output_path}")
        return output_path

    print("\n[Pipeline FAILED] All batches discarded.")
    return None
