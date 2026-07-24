from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .models import PetPackError


class JsonHttpClient:
    def request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=payload,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            raw_error = error.read().decode("utf-8", errors="replace")[:2000]
            raise PetPackError(
                f"Provider returned HTTP {error.code}: {raw_error}"
            ) from error
        except urllib.error.URLError as error:
            raise PetPackError(f"Provider request failed: {error.reason}") from error
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise PetPackError("Provider returned invalid JSON") from error
        if not isinstance(result, dict):
            raise PetPackError("Provider returned an unexpected JSON value")
        return result

    def download(self, url: str, output_path: Path) -> Path:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise PetPackError("Generated output URL must use HTTPS")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix(output_path.suffix + ".part")
        request = urllib.request.Request(
            url=url,
            headers={"User-Agent": "desktop-pet-engine/0.1"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                with temporary_path.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
            os.replace(temporary_path, output_path)
        except (OSError, urllib.error.URLError) as error:
            temporary_path.unlink(missing_ok=True)
            raise PetPackError(f"Cannot download generated output: {error}") from error
        return output_path
