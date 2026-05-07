from pydantic import BaseModel

from .contracts import DEFAULT_PROFILE


class CodeArtifact(BaseModel):
    """Validated code artifact envelope exchanged across pipeline stages."""

    version: str = "1.0"
    profile: str = DEFAULT_PROFILE
    run_name: str | None = None
    module_id: str
    payload: dict
