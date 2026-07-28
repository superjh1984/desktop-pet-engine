from __future__ import annotations

from typing import Any, Dict, List

from ..models import GenerationPlan, JobStatus, PetPackError
from .base import ProviderAdapter, first_value, normalized_state


class ModelArkVideoAdapter(ProviderAdapter):
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.credentials.authorization}",
            "Content-Type": "application/json",
        }

    def submit(self, plan: GenerationPlan) -> JobStatus:
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": str(plan.inputs["prompt"])}
        ]
        if plan.inputs.get("image_url"):
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": str(plan.inputs["image_url"])},
                }
            )
        payload: Dict[str, Any] = {
            "model": plan.api_model,
            "content": content,
            "generate_audio": bool(plan.options.get("generate_audio", False)),
            "ratio": str(plan.options.get("ratio", "adaptive")),
        }
        endpoint = (
            f"{self.credentials.base_url}/api/v3/contents/generations/tasks"
        )
        response = self.http.request(
            "POST", endpoint, self._headers(), payload
        )
        job_id = first_value(response, {"id", "task_id", "taskId"})
        if not job_id:
            raise PetPackError("ModelArk response did not include a task ID")
        return _parse_status(response, job_id)

    def status(self, job_id: str) -> JobStatus:
        endpoint = (
            f"{self.credentials.base_url}/api/v3/contents/generations/tasks/"
            f"{job_id}"
        )
        response = self.http.request("GET", endpoint, self._headers(), None)
        return _parse_status(response, job_id)


def _parse_status(response: Dict[str, Any], job_id: str) -> JobStatus:
    state = normalized_state(
        first_value(response, {"status", "task_status", "taskStatus"})
    )
    output_url = first_value(
        response, {"video_url", "videoUrl", "file_url", "fileUrl"}
    )
    error = first_value(
        response, {"error_message", "errorMessage", "message", "code"}
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
