from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .catalog import Catalog
from .models import GenerationPlan, ModelSpec, PetPackError


CAPABILITY_INPUTS = {
    "character-sheet": ["image_url", "prompt"],
    "sticker-set": ["image_url", "prompt"],
    "image-edit": ["image_url", "prompt"],
    "image-to-video": ["image_url", "prompt"],
    "text-to-video": ["prompt"],
    "motion-transfer": ["image_url", "reference_video_url"],
}


def _validate_remote_url(name: str, value: str, allow_oss: bool = False) -> None:
    parsed = urlparse(value)
    allowed = {"http", "https"}
    if allow_oss:
        allowed.add("oss")
    if parsed.scheme not in allowed or not parsed.netloc:
        schemes = "HTTP(S) or oss://" if allow_oss else "HTTP(S)"
        raise PetPackError(f"{name} must be a remotely accessible {schemes} URL")


def build_plan(
    catalog: Catalog,
    model: ModelSpec,
    capability: str,
    inputs: Dict[str, Any],
    options: Dict[str, Any],
    api_model: Optional[str] = None,
) -> GenerationPlan:
    if api_model and model.api_model and api_model != model.api_model:
        raise PetPackError(
            f"{model.qualified_id} uses fixed API model {model.api_model}"
        )
    if capability not in model.capabilities:
        supported = ", ".join(model.capabilities)
        raise PetPackError(
            f"{model.qualified_id} does not support {capability}; "
            f"supported: {supported}"
        )
    required = CAPABILITY_INPUTS.get(capability, model.required_inputs)
    missing = [name for name in required if not inputs.get(name)]
    if missing:
        raise PetPackError(
            f"{capability} requires: {', '.join(sorted(missing))}"
        )
    allow_oss = model.adapter.startswith("dashscope-wan-")
    for name in ("image_url", "reference_video_url"):
        if inputs.get(name):
            _validate_remote_url(name, str(inputs[name]), allow_oss=allow_oss)
    clean_inputs = {
        key: value
        for key, value in inputs.items()
        if value is not None and value != ""
    }
    clean_options = {
        key: value
        for key, value in options.items()
        if value is not None and value != ""
    }
    count = clean_options.get("count")
    if count is not None:
        try:
            parsed_count = int(count)
        except (TypeError, ValueError) as error:
            raise PetPackError("Image output count must be an integer") from error
        if not 1 <= parsed_count <= 12:
            raise PetPackError("Image output count must be between 1 and 12")
        clean_options["count"] = parsed_count
    return GenerationPlan.create(
        provider=catalog.provider_for(model),
        model=model,
        capability=capability,
        inputs=clean_inputs,
        options=clean_options,
        api_model=api_model,
    )


def validate_plan(catalog: Catalog, plan: GenerationPlan) -> ModelSpec:
    model = catalog.find_model(plan.model)
    provider = catalog.provider_for(model)
    expected = {
        "provider": provider.id,
        "adapter": model.adapter,
        "credential_env": provider.credential_env,
        "base_url_env": provider.base_url_env,
        "docs_url": model.docs_url,
        "cost_note": model.cost_note,
    }
    for field, value in expected.items():
        if getattr(plan, field) != value:
            raise PetPackError(
                f"Plan field {field} does not match the current catalog"
            )
    if model.api_model and plan.api_model != model.api_model:
        raise PetPackError(
            f"Plan API model does not match fixed model {model.api_model}"
        )
    build_plan(
        catalog=catalog,
        model=model,
        capability=plan.capability,
        inputs=plan.inputs,
        options=plan.options,
        api_model=plan.api_model,
    )
    if model.availability != "live":
        raise PetPackError(
            f"{model.qualified_id} is catalog-only; no reviewed live adapter "
            "is included"
        )
    if not plan.api_model:
        raise PetPackError(
            "This provider requires --api-model with the model or endpoint ID "
            "enabled for your account"
        )
    return model
