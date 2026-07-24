from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import ModelSpec, PetPackError, ProviderSpec


class Catalog:
    def __init__(
        self, providers: Iterable[ProviderSpec], models: Iterable[ModelSpec]
    ) -> None:
        self.providers: Dict[str, ProviderSpec] = {
            provider.id: provider for provider in providers
        }
        self.models: Dict[str, ModelSpec] = {
            model.qualified_id: model for model in models
        }
        for model in self.models.values():
            if model.provider not in self.providers:
                raise PetPackError(
                    f"Model {model.qualified_id} refers to an unknown provider"
                )

    @classmethod
    def load(cls, path: Path) -> "Catalog":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PetPackError(f"Cannot read model catalog {path}: {error}") from error
        if data.get("schema_version") != 1:
            raise PetPackError("Unsupported model catalog schema version")
        try:
            providers = [ProviderSpec(**item) for item in data["providers"]]
            models = [ModelSpec(**item) for item in data["models"]]
        except (KeyError, TypeError) as error:
            raise PetPackError(f"Invalid model catalog: {error}") from error
        return cls(providers, models)

    @classmethod
    def load_default(cls) -> "Catalog":
        root = Path(__file__).resolve().parent.parent
        return cls.load(root / "config" / "model_providers.json")

    def list_models(
        self,
        capability: Optional[str] = None,
        availability: Optional[str] = None,
    ) -> List[ModelSpec]:
        models = list(self.models.values())
        if capability:
            models = [
                model for model in models if capability in model.capabilities
            ]
        if availability:
            models = [
                model for model in models if model.availability == availability
            ]
        return sorted(models, key=lambda model: model.qualified_id)

    def find_model(
        self, model_id: str, provider_id: Optional[str] = None
    ) -> ModelSpec:
        if "/" in model_id:
            model = self.models.get(model_id)
            if not model:
                raise PetPackError(f"Unknown model: {model_id}")
            return model
        matches = [
            model
            for model in self.models.values()
            if model.id == model_id
            and (provider_id is None or model.provider == provider_id)
        ]
        if not matches:
            suffix = f" for provider {provider_id}" if provider_id else ""
            raise PetPackError(f"Unknown model {model_id}{suffix}")
        if len(matches) > 1:
            choices = ", ".join(model.qualified_id for model in matches)
            raise PetPackError(
                f"Model name is ambiguous; use a qualified name: {choices}"
            )
        return matches[0]

    def provider_for(self, model: ModelSpec) -> ProviderSpec:
        return self.providers[model.provider]
