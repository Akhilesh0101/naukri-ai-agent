"""Application-provider interface.

A provider knows how to submit an application for a job through an authorized
mechanism. Before a live provider is implemented, its capabilities and
authorization requirements must be verified. The default provider is a safe
manual-fallback that never claims a submission it did not make.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class SubmissionResult:
    # outcome: "submitted" | "needs_attention" | "failed" | "transient_error" | "unsupported"
    outcome: str
    confirmed: bool = False
    provider_status: str | None = None
    provider_reference: str | None = None
    manual_action_required: bool = False
    manual_url: str | None = None
    message: str | None = None
    response: dict[str, Any] = field(default_factory=dict)


class ApplicationProvider(Protocol):
    key: str
    name: str
    supports_auto_submit: bool

    def verify(self) -> tuple[bool, str]:
        """Return (available, message). Must be True before any live submit."""
        ...

    def prepare(self, job, profile) -> dict[str, Any]:
        """Build the application payload. Never invents answers."""
        ...

    def submit(self, job, profile, payload: dict[str, Any]) -> SubmissionResult:
        """Attempt submission. Only report success with reliable confirmation."""
        ...
