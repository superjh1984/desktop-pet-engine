from __future__ import annotations

from typing import Any, Dict

from ..models import GenerationPlan, JobStatus, PetPackError
from .base import ProviderAdapter, first_value, normalized_state


class DashScopeWanAnimateAdapter(ProviderAdapter):
    def _headers(self, uses_oss: bool = False) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.credentials.authorization}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        if uses_oss:
            headers["X-DashScope-OssResourceResolve"] = "enable"
        return headers

    def submit(self, plan: GenerationPlan) -> JobStatus:
        image_url = str(plan.inputs["image_url"])
        video_url = str(plan.inputs["reference_video_url"])
        payload = {
            "model": plan.api_model,
            "input": {
                "image_url": image_url,
                "video_url": video_url,
                "watermark": bool(plan.options.get("watermark", False)),
            },
            "parameters": {
                "mode": str(plan.options.get("mode", "wan-std")),
            },
        }
        endpoint = (
            f"{self.credentials.base_url}"
            "/api/v1/services/aigc/image2video/video-synthesis"
        )
        response = self.http.request(
            "POST",
            endpoint,
            self._headers(
                uses_oss=image_url.startswith("oss://")
                or video_url.startswith("oss://")
            ),
            payload,
        )
        job_id = first_value(response, {"task_id", "taskId"})
        if not job_id:
            raise PetPackError("Alibaba Cloud response did not include a task ID")
        return _parse_status(response, job_id)

    def status(self, job_id: str) -> JobStatus:
        endpoint = f"{self.credentials.base_url}/api/v1/tasks/{job_id}"
        response = self.http.request("GET", endpoint, self._headers(), None)
        return _parse_status(response, job_id)


def _parse_status(response: Dict[str, Any], job_id: str) -> JobStatus:
    state = normalized_state(
        first_value(response, {"task_status", "taskStatus", "status"})
    )
    output_url = first_value(
        response, {"video_url", "videoUrl", "output_url", "outputUrl"}
    )
    error = first_value(
        response, {"message", "error_message", "errorMessage", "code"}
    )
    if state not in {"failed", "canceled"}:
        error = None
    return JobStatus(
        job_id=job_id,
        state=state,
        output_urls=[output_url] if output_url else [],
        output_extension=".mp4",
        error_message=error,
    )
