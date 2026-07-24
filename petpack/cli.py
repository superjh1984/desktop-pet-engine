from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .catalog import Catalog
from .credentials import configured, resolve
from .http import JsonHttpClient
from .models import GenerationPlan, JobStatus, PetPackError
from .planning import CAPABILITY_INPUTS, build_plan, validate_plan
from .providers import adapter_for


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _load_plan(path: Path) -> GenerationPlan:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PetPackError(f"Cannot read plan {path}: {error}") from error
    if not isinstance(value, dict):
        raise PetPackError("Plan must be a JSON object")
    return GenerationPlan.from_dict(value)


def _write_plan(plan: GenerationPlan, output: str) -> None:
    content = _json(plan.to_dict()) + "\n"
    if output == "-":
        sys.stdout.write(content)
        return
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(
        _json(
            {
                "mode": "plan-only",
                "plan_path": str(path),
                "billing_started": False,
            }
        )
    )


def _provider_for_id(catalog: Catalog, provider_id: str):
    provider = catalog.providers.get(provider_id)
    if not provider:
        choices = ", ".join(sorted(catalog.providers))
        raise PetPackError(
            f"Unknown provider {provider_id}; choose one of: {choices}"
        )
    return provider


def _command_providers(args: argparse.Namespace, catalog: Catalog) -> int:
    models = catalog.list_models(
        capability=args.capability, availability=args.availability
    )
    if args.provider:
        _provider_for_id(catalog, args.provider)
        models = [model for model in models if model.provider == args.provider]
    values = [
        {
            "model": model.qualified_id,
            "availability": model.availability,
            "capabilities": model.capabilities,
            "credential_env": catalog.provider_for(model).credential_env,
            "docs_url": model.docs_url,
        }
        for model in models
    ]
    if args.json:
        print(_json(values))
    else:
        if not values:
            print("No matching models.")
            return 0
        print("MODEL\tSTATUS\tCAPABILITIES\tKEY ENV")
        for item in values:
            print(
                f"{item['model']}\t{item['availability']}\t"
                f"{','.join(item['capabilities'])}\t{item['credential_env']}"
            )
    return 0


def _command_doctor(args: argparse.Namespace, catalog: Catalog) -> int:
    if args.provider:
        providers = [_provider_for_id(catalog, args.provider)]
    else:
        providers = [
            catalog.providers[key] for key in sorted(catalog.providers)
        ]
    checks = [configured(provider) for provider in providers]
    print(_json(checks))
    return 0 if all(item["credential_configured"] for item in checks) else 2


def _command_plan(args: argparse.Namespace, catalog: Catalog) -> int:
    model = catalog.find_model(args.model, provider_id=args.provider)
    inputs = {
        "image_url": args.image_url,
        "reference_video_url": args.reference_video_url,
        "prompt": args.prompt,
    }
    if args.task == "motion-transfer":
        options = {
            "mode": args.mode,
            "watermark": args.watermark,
        }
    elif args.task in {"character-sheet", "sticker-set", "image-edit"}:
        options = {
            "size": args.size,
            "count": args.count,
            "thinking_mode": not args.no_thinking,
            "watermark": args.watermark,
        }
    else:
        options = {
            "generate_audio": args.generate_audio,
            "ratio": args.ratio,
        }
    plan = build_plan(
        catalog=catalog,
        model=model,
        capability=args.task,
        inputs=inputs,
        options=options,
        api_model=args.api_model,
    )
    _write_plan(plan, args.output)
    return 0


def _wait_for_job(
    adapter,
    status: JobStatus,
    interval: float,
    timeout: float,
) -> JobStatus:
    if interval <= 0:
        raise PetPackError("Polling interval must be greater than zero")
    if timeout <= 0:
        raise PetPackError("Polling timeout must be greater than zero")
    deadline = time.monotonic() + timeout
    current = status
    while not current.terminal:
        if time.monotonic() >= deadline:
            raise PetPackError(
                f"Timed out waiting for job {current.job_id}; query it later"
            )
        time.sleep(interval)
        current = adapter.status(current.job_id)
    return current


def _safe_job_name(provider: str, job_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", job_id).strip("-")
    return f"{provider}-{safe or 'output'}"


def _download_if_available(
    status: JobStatus,
    provider: str,
    output_dir: Path,
    http: JsonHttpClient,
) -> list[Path]:
    if status.state != "succeeded":
        return []
    if not status.output_urls:
        raise PetPackError("Job succeeded but the provider returned no output URLs")
    base_name = _safe_job_name(provider, status.job_id)
    paths = []
    for index, url in enumerate(status.output_urls, start=1):
        suffix = f"-{index:02d}" if len(status.output_urls) > 1 else ""
        path = output_dir / f"{base_name}{suffix}{status.output_extension}"
        paths.append(http.download(url, path))
    return paths


def _status_output(
    status: JobStatus, output_paths: Optional[list[Path]] = None
) -> str:
    value = status.public_dict()
    if output_paths:
        value["downloaded_to"] = [str(path) for path in output_paths]
    return _json(value)


def _command_submit(args: argparse.Namespace, catalog: Catalog) -> int:
    if not args.execute:
        raise PetPackError("Refusing billed call without --execute")
    if not args.accept_cost:
        raise PetPackError("Refusing billed call without --accept-cost")
    if not args.accept_rights:
        raise PetPackError("Refusing call without --accept-rights")
    plan = _load_plan(Path(args.plan).expanduser())
    model = validate_plan(catalog, plan)
    provider = catalog.provider_for(model)
    runtime = resolve(provider)
    http = JsonHttpClient()
    adapter = adapter_for(model.adapter, runtime, http=http)
    status = adapter.submit(plan)
    output_paths: list[Path] = []
    if args.wait:
        status = _wait_for_job(
            adapter, status, interval=args.interval, timeout=args.timeout
        )
    if status.state == "succeeded":
        output_paths = _download_if_available(
            status,
            provider=provider.id,
            output_dir=Path(args.output_dir).expanduser(),
            http=http,
        )
    print(_status_output(status, output_paths))
    return 0 if status.state not in {"failed", "canceled"} else 3


def _adapter_from_args(args: argparse.Namespace, catalog: Catalog):
    model = catalog.find_model(args.model, provider_id=args.provider)
    if model.availability != "live":
        raise PetPackError(f"{model.qualified_id} is catalog-only")
    provider = catalog.provider_for(model)
    runtime = resolve(provider)
    http = JsonHttpClient()
    return provider, adapter_for(model.adapter, runtime, http=http), http


def _command_status(args: argparse.Namespace, catalog: Catalog) -> int:
    _provider, adapter, _http = _adapter_from_args(args, catalog)
    status = adapter.status(args.job_id)
    print(_status_output(status))
    return 0 if status.state not in {"failed", "canceled"} else 3


def _command_wait(args: argparse.Namespace, catalog: Catalog) -> int:
    provider, adapter, http = _adapter_from_args(args, catalog)
    initial = adapter.status(args.job_id)
    status = _wait_for_job(
        adapter, initial, interval=args.interval, timeout=args.timeout
    )
    output_paths = _download_if_available(
        status,
        provider=provider.id,
        output_dir=Path(args.output_dir).expanduser(),
        http=http,
    )
    print(_status_output(status, output_paths))
    return 0 if status.state == "succeeded" else 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pet_pack.py",
        description=(
            "Plan and run bring-your-own-key model jobs for desktop-pet assets. "
            "Planning is always free; submit requires explicit billing and rights "
            "confirmations."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    providers = subparsers.add_parser(
        "providers", help="List models and capabilities"
    )
    providers.add_argument("--provider")
    providers.add_argument("--capability", choices=sorted(CAPABILITY_INPUTS))
    providers.add_argument("--availability", choices=["live", "catalog"])
    providers.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser(
        "doctor", help="Check environment references without showing keys"
    )
    doctor.add_argument("--provider")

    plan = subparsers.add_parser(
        "plan", help="Validate a request and create a no-charge plan"
    )
    plan.add_argument("--provider")
    plan.add_argument("--model", required=True)
    plan.add_argument("--api-model")
    plan.add_argument("--task", required=True, choices=sorted(CAPABILITY_INPUTS))
    plan.add_argument("--image-url")
    plan.add_argument("--reference-video-url")
    plan.add_argument("--prompt")
    plan.add_argument("--mode", choices=["wan-std", "wan-pro"], default="wan-std")
    plan.add_argument("--watermark", action="store_true")
    plan.add_argument("--generate-audio", action="store_true")
    plan.add_argument("--ratio", default="adaptive")
    plan.add_argument("--size", default="2K")
    plan.add_argument("--count", type=int, choices=range(1, 13), default=4)
    plan.add_argument("--no-thinking", action="store_true")
    plan.add_argument(
        "--output",
        default="-",
        help="Plan file path, or - for stdout (default: -)",
    )

    submit = subparsers.add_parser(
        "submit", help="Execute a saved plan after explicit confirmations"
    )
    submit.add_argument("--plan", required=True)
    submit.add_argument("--execute", action="store_true")
    submit.add_argument("--accept-cost", action="store_true")
    submit.add_argument("--accept-rights", action="store_true")
    submit.add_argument("--wait", action="store_true")
    submit.add_argument("--interval", type=float, default=10.0)
    submit.add_argument("--timeout", type=float, default=1800.0)
    submit.add_argument("--output-dir", default="pet-pack-output")

    for name, help_text in (
        ("status", "Query one asynchronous job"),
        ("wait", "Wait for a job and download its output"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--provider")
        command.add_argument("--model", required=True)
        command.add_argument("--job-id", required=True)
        if name == "wait":
            command.add_argument("--interval", type=float, default=10.0)
            command.add_argument("--timeout", type=float, default=1800.0)
            command.add_argument("--output-dir", default="pet-pack-output")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    catalog = Catalog.load_default()
    commands = {
        "providers": _command_providers,
        "doctor": _command_doctor,
        "plan": _command_plan,
        "submit": _command_submit,
        "status": _command_status,
        "wait": _command_wait,
    }
    try:
        return commands[args.command](args, catalog)
    except PetPackError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
