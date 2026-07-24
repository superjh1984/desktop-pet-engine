from __future__ import annotations

import os
from dataclasses import dataclass

from .models import PetPackError, ProviderSpec


@dataclass(frozen=True)
class RuntimeCredentials:
    authorization: str
    base_url: str


def configured(provider: ProviderSpec) -> dict:
    return {
        "provider": provider.id,
        "credential_env": provider.credential_env,
        "credential_configured": bool(os.environ.get(provider.credential_env)),
        "base_url_env": provider.base_url_env,
        "base_url_configured": bool(
            os.environ.get(provider.base_url_env) or provider.default_base_url
        ),
    }


def resolve(provider: ProviderSpec) -> RuntimeCredentials:
    authorization = os.environ.get(provider.credential_env, "").strip()
    if not authorization:
        raise PetPackError(
            f"Set {provider.credential_env} in the environment before execution"
        )
    base_url = (
        os.environ.get(provider.base_url_env, "").strip()
        or provider.default_base_url.strip()
    )
    if not base_url:
        raise PetPackError(
            f"Set {provider.base_url_env} to the official API base URL for "
            f"your {provider.id} workspace"
        )
    if not base_url.startswith("https://"):
        raise PetPackError("Provider base URL must use HTTPS")
    return RuntimeCredentials(
        authorization=authorization,
        base_url=base_url.rstrip("/"),
    )
