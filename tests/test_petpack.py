import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from petpack.catalog import Catalog
from petpack.cli import main
from petpack.credentials import RuntimeCredentials, configured
from petpack.models import GenerationPlan, PetPackError
from petpack.planning import build_plan, validate_plan
from petpack.providers.dashscope_wan import DashScopeWanAnimateAdapter
from petpack.providers.dashscope_wan_image import DashScopeWanImageAdapter
from petpack.providers.modelark import ModelArkVideoAdapter


class FakeHttp:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        return self.responses.pop(0)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog.load_default()

    def test_capability_filter(self):
        models = self.catalog.list_models(capability="motion-transfer")
        self.assertEqual(
            [model.qualified_id for model in models],
            ["aliyun/wan2.2-animate-move"],
        )

    def test_ambiguous_model_name_requires_provider(self):
        with self.assertRaisesRegex(PetPackError, "ambiguous"):
            self.catalog.find_model("seedance-2.0")

    def test_plan_contains_env_reference_but_never_key(self):
        model = self.catalog.find_model("aliyun/wan2.2-animate-move")
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "secret-value"}):
            plan = build_plan(
                self.catalog,
                model,
                "motion-transfer",
                inputs={
                    "image_url": "https://example.test/character.png",
                    "reference_video_url": "https://example.test/action.mp4",
                },
                options={},
            )
        encoded = json.dumps(plan.to_dict())
        self.assertIn("DASHSCOPE_API_KEY", encoded)
        self.assertNotIn("secret-value", encoded)

    def test_catalog_only_plan_cannot_execute(self):
        model = self.catalog.find_model("openai/gpt-image-2")
        plan = build_plan(
            self.catalog,
            model,
            "sticker-set",
            inputs={
                "image_url": "https://example.test/character.png",
                "prompt": "Create a consistent sticker sheet",
            },
            options={},
        )
        with self.assertRaisesRegex(PetPackError, "catalog-only"):
            validate_plan(self.catalog, plan)

    def test_seedance_execution_requires_account_model_id(self):
        model = self.catalog.find_model("byteplus/seedance-2.0")
        plan = build_plan(
            self.catalog,
            model,
            "image-to-video",
            inputs={
                "image_url": "https://example.test/character.png",
                "prompt": "Wave once on a fixed camera",
            },
            options={},
        )
        with self.assertRaisesRegex(PetPackError, "--api-model"):
            validate_plan(self.catalog, plan)

    def test_plan_rejects_non_object_inputs(self):
        model = self.catalog.find_model("aliyun/wan2.2-animate-move")
        plan = build_plan(
            self.catalog,
            model,
            "motion-transfer",
            inputs={
                "image_url": "https://example.test/character.png",
                "reference_video_url": "https://example.test/action.mp4",
            },
            options={},
        ).to_dict()
        plan["inputs"] = ["not", "an", "object"]
        with self.assertRaisesRegex(PetPackError, "JSON objects"):
            GenerationPlan.from_dict(plan)

    def test_image_count_validation_is_user_facing(self):
        model = self.catalog.find_model("aliyun/wan2.7-image-pro")
        with self.assertRaisesRegex(PetPackError, "must be an integer"):
            build_plan(
                self.catalog,
                model,
                "sticker-set",
                inputs={
                    "image_url": "https://example.test/character.png",
                    "prompt": "Create expressions",
                },
                options={"count": "many"},
            )

    def test_fixed_api_model_cannot_be_overridden(self):
        model = self.catalog.find_model("aliyun/wan2.2-animate-move")
        with self.assertRaisesRegex(PetPackError, "fixed API model"):
            build_plan(
                self.catalog,
                model,
                "motion-transfer",
                inputs={
                    "image_url": "https://example.test/character.png",
                    "reference_video_url": "https://example.test/action.mp4",
                },
                options={},
                api_model="different-model",
            )

    def test_doctor_never_returns_key_value(self):
        provider = self.catalog.providers["byteplus"]
        with patch.dict(os.environ, {"ARK_API_KEY": "top-secret"}):
            result = configured(provider)
        self.assertTrue(result["credential_configured"])
        self.assertNotIn("top-secret", json.dumps(result))

    def test_submit_requires_explicit_execution_flag(self):
        error_output = StringIO()
        with redirect_stderr(error_output):
            result = main(["submit", "--plan", "not-read-without-execute.json"])
        self.assertEqual(result, 2)
        self.assertIn("--execute", error_output.getvalue())


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog.load_default()
        self.credentials = RuntimeCredentials(
            authorization="runtime-secret",
            base_url="https://api.example.test",
        )

    def test_dashscope_submission_shape_and_status(self):
        http = FakeHttp(
            [
                {
                    "output": {
                        "task_id": "wan-job-1",
                        "task_status": "PENDING",
                    }
                }
            ]
        )
        model = self.catalog.find_model("aliyun/wan2.2-animate-move")
        plan = build_plan(
            self.catalog,
            model,
            "motion-transfer",
            inputs={
                "image_url": "https://example.test/character.png",
                "reference_video_url": "https://example.test/action.mp4",
            },
            options={"mode": "wan-pro", "watermark": False},
        )
        status = DashScopeWanAnimateAdapter(
            self.credentials, http=http
        ).submit(plan)
        self.assertEqual(status.job_id, "wan-job-1")
        self.assertEqual(status.state, "queued")
        method, url, headers, body = http.calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/video-synthesis"))
        self.assertEqual(headers["Authorization"], "Bearer runtime-secret")
        self.assertEqual(body["parameters"]["mode"], "wan-pro")
        self.assertEqual(body["input"]["video_url"], "https://example.test/action.mp4")

    def test_modelark_submission_shape(self):
        http = FakeHttp([{"id": "seed-job-1", "status": "queued"}])
        model = self.catalog.find_model("byteplus/seedance-2.0")
        plan = build_plan(
            self.catalog,
            model,
            "image-to-video",
            inputs={
                "image_url": "https://example.test/character.png",
                "prompt": "Jump once",
            },
            options={"ratio": "adaptive", "generate_audio": False},
            api_model="account-endpoint-id",
        )
        status = ModelArkVideoAdapter(self.credentials, http=http).submit(plan)
        self.assertEqual(status.job_id, "seed-job-1")
        _method, _url, _headers, body = http.calls[0]
        self.assertEqual(body["model"], "account-endpoint-id")
        self.assertEqual(body["content"][0]["type"], "text")
        self.assertEqual(body["content"][1]["image_url"]["url"], "https://example.test/character.png")

    def test_wan_image_set_submission_and_private_results(self):
        http = FakeHttp(
            [
                {
                    "request_id": "image-request-1",
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {"image": "https://example.test/one.png"},
                                        {"image": "https://example.test/two.png"},
                                    ]
                                }
                            }
                        ]
                    },
                }
            ]
        )
        model = self.catalog.find_model("aliyun/wan2.7-image-pro")
        plan = build_plan(
            self.catalog,
            model,
            "sticker-set",
            inputs={
                "image_url": "https://example.test/character.png",
                "prompt": "Create four consistent expressions",
            },
            options={"count": 4, "size": "2K", "watermark": False},
        )
        status = DashScopeWanImageAdapter(
            self.credentials, http=http
        ).submit(plan)
        self.assertEqual(status.state, "succeeded")
        self.assertEqual(status.output_extension, ".png")
        self.assertEqual(len(status.output_urls), 2)
        self.assertNotIn("https://example.test/one.png", json.dumps(status.public_dict()))
        _method, url, _headers, body = http.calls[0]
        self.assertTrue(url.endswith("/multimodal-generation/generation"))
        self.assertTrue(body["parameters"]["enable_sequential"])
        self.assertEqual(body["parameters"]["n"], 4)
        self.assertEqual(
            body["input"]["messages"][0]["content"][0]["image"],
            "https://example.test/character.png",
        )

    def test_plan_round_trip(self):
        model = self.catalog.find_model("aliyun/wan2.2-animate-move")
        original = build_plan(
            self.catalog,
            model,
            "motion-transfer",
            inputs={
                "image_url": "https://example.test/a.png",
                "reference_video_url": "https://example.test/a.mp4",
            },
            options={},
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(original.to_dict()), encoding="utf-8")
            restored = GenerationPlan.from_dict(
                json.loads(path.read_text(encoding="utf-8"))
            )
        self.assertEqual(original.to_dict(), restored.to_dict())


if __name__ == "__main__":
    unittest.main()
