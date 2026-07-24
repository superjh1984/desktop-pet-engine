from __future__ import annotations

from typing import Dict
from uuid import uuid4

from ..models import GenerationPlan, JobStatus, PetPackError
from .base import ProviderAdapter, all_values, first_value


class DashScopeWanImageAdapter(ProviderAdapter):
    def _headers(self, uses_oss: bool = False) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.credentials.authorization}",
            "Content-Type": "application/json",
        }
        if uses_oss:
            headers["X-DashScope-OssResourceResolve"] = "enable"
        return headers

    def submit(self, plan: GenerationPlan) -> JobStatus:
        image_url = str(plan.inputs["image_url"])
        sequential = plan.capability in {"character-sheet", "sticker-set"}
        parameters = {
            "size": str(plan.options.get("size", "2K")),
            "n": int(plan.options.get("count", 4)),
            "watermark": bool(plan.options.get("watermark", False)),
            "enable_sequential": sequential,
        }
        if not sequential:
            parameters["thinking_mode"] = bool(
                plan.options.get("thinking_mode", True)
            )
        payload = {
            "model": plan.api_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_url},
                            {"text": str(plan.inputs["prompt"])},
                        ],
                    }
                ]
            },
            "parameters": parameters,
        }
        endpoint = (
            f"{self.credentials.base_url}"
            "/api/v1/services/aigc/multimodal-generation/generation"
        )
        response = self.http.request(
            "POST",
            endpoint,
            self._headers(uses_oss=image_url.startswith("oss://")),
            payload,
        )
        output_urls = all_values(response.get("output", {}), {"image"})
        if not output_urls:
            raise PetPackError(
                "Alibaba Cloud response did not include generated image URLs"
            )
        request_id = first_value(response, {"request_id", "requestId"})
        return JobStatus(
            job_id=request_id or f"local-{uuid4().hex}",
            state="succeeded",
            output_urls=output_urls,
            output_extension=".png",
        )

    def status(self, job_id: str) -> JobStatus:
        raise PetPackError(
            "Wan image generation is synchronous and has no status endpoint"
        )
