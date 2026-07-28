from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional

from ..credentials import RuntimeCredentials
from ..http import JsonHttpClient
from ..models import GenerationPlan, JobStatus, PetPackError


def first_value(value: Any, keys: Iterable[str]) -> Optional[str]:
    key_set = set(keys)
    if isinstance(value, dict):
        for key, child in value.items():
            if key in key_set and isinstance(child, (str, int)):
                return str(child)
        for child in value.values():
            found = first_value(child, key_set)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = first_value(child, key_set)
            if found is not None:
                return found
    return None


def all_values(value: Any, keys: Iterable[str]) -> list[str]:
    key_set = set(keys)
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in key_set and isinstance(child, str):
                found.append(child)
            else:
                found.extend(all_values(child, key_set))
    elif isinstance(value, list):
        for child in value:
            found.extend(all_values(child, key_set))
    return found


def normalized_state(value: Optional[str]) -> str:
    state = (value or "unknown").strip().lower().replace("-", "_")
    if state in {"pending", "queued", "created", "submitted", "not_started"}:
        return "queued"
    if state in {"running", "processing", "in_progress", "generating"}:
        return "running"
    if state in {"success", "succeeded", "completed", "done"}:
        return "succeeded"
    if state in {"failed", "error"}:
        return "failed"
    if state in {"cancelled", "canceled"}:
        return "canceled"
    return state


class ProviderAdapter(ABC):
    def __init__(
        self, credentials: RuntimeCredentials, http: Optional[JsonHttpClient] = None
    ) -> None:
        self.credentials = credentials
        self.http = http or JsonHttpClient()

    @abstractmethod
    def submit(self, plan: GenerationPlan) -> JobStatus:
        raise NotImplementedError

    @abstractmethod
    def status(self, job_id: str) -> JobStatus:
        raise NotImplementedError


def adapter_for(
    name: str,
    credentials: RuntimeCredentials,
    http: Optional[JsonHttpClient] = None,
) -> ProviderAdapter:
    if name == "dashscope-wan-animate":
        from .dashscope_wan import DashScopeWanAnimateAdapter

        return DashScopeWanAnimateAdapter(credentials, http=http)
    if name == "dashscope-wan-image":
        from .dashscope_wan_image import DashScopeWanImageAdapter

        return DashScopeWanImageAdapter(credentials, http=http)
    if name == "modelark-video":
        from .modelark import ModelArkVideoAdapter

        return ModelArkVideoAdapter(credentials, http=http)
    raise PetPackError(f"No live provider adapter is available for {name}")
