from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PetPackError(RuntimeError):
    """A user-facing configuration or provider error."""


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    credential_env: str
    base_url_env: str
    default_base_url: str
    docs_url: str


@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: str
    api_model: str
    adapter: str
    availability: str
    capabilities: List[str]
    required_inputs: List[str]
    docs_url: str
    cost_note: str

    @property
    def qualified_id(self) -> str:
        return f"{self.provider}/{self.id}"


@dataclass
class GenerationPlan:
    schema_version: int
    created_at: str
    provider: str
    model: str
    api_model: str
    capability: str
    adapter: str
    inputs: Dict[str, Any]
    options: Dict[str, Any]
    credential_env: str
    base_url_env: str
    docs_url: str
    cost_note: str

    @classmethod
    def create(
        cls,
        provider: ProviderSpec,
        model: ModelSpec,
        capability: str,
        inputs: Dict[str, Any],
        options: Dict[str, Any],
        api_model: Optional[str] = None,
    ) -> "GenerationPlan":
        return cls(
            schema_version=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            provider=provider.id,
            model=model.qualified_id,
            api_model=api_model or model.api_model,
            capability=capability,
            adapter=model.adapter,
            inputs=inputs,
            options=options,
            credential_env=provider.credential_env,
            base_url_env=provider.base_url_env,
            docs_url=model.docs_url,
            cost_note=model.cost_note,
        )

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "GenerationPlan":
        required = [
            "schema_version",
            "created_at",
            "provider",
            "model",
            "api_model",
            "capability",
            "adapter",
            "inputs",
            "options",
            "credential_env",
            "base_url_env",
            "docs_url",
            "cost_note",
        ]
        missing = sorted(set(required) - set(value))
        if missing:
            raise PetPackError(f"Plan is missing fields: {', '.join(missing)}")
        if value["schema_version"] != 1:
            raise PetPackError(
                f"Unsupported plan schema version: {value['schema_version']}"
            )
        if not isinstance(value["inputs"], dict) or not isinstance(
            value["options"], dict
        ):
            raise PetPackError("Plan inputs and options must be JSON objects")
        string_fields = [
            key
            for key in required
            if key not in {"schema_version", "inputs", "options"}
        ]
        if any(not isinstance(value[key], str) for key in string_fields):
            raise PetPackError("Plan metadata fields must be strings")
        return cls(**{key: value[key] for key in required})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobStatus:
    job_id: str
    state: str
    output_urls: List[str] = field(default_factory=list)
    output_extension: str = ".mp4"
    error_message: Optional[str] = None

    @property
    def terminal(self) -> bool:
        return self.state in {"succeeded", "failed", "canceled"}

    def public_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "has_output": bool(self.output_urls),
            "output_count": len(self.output_urls),
            "error_message": self.error_message,
        }
