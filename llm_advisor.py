#!/usr/bin/env python3
"""CLI tool to filter, compare, and validate the open-source LLMs dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "models.json"
DOCS_DATA_PATH = ROOT_DIR / "docs" / "models.json"

REQUIRED_MODEL_FIELDS = {
    "id",
    "name",
    "organization",
    "family",
    "architecture",
    "total_params_b",
    "active_params_b",
    "context_window_k",
    "license",
    "license_tier",
    "open_data",
    "vram_q4_gb",
    "vram_fp16_gb",
    "modalities",
    "capabilities",
    "primary_use_cases",
    "runtimes",
    "ollama_tag",
    "huggingface_url",
    "repo_url",
    "summary",
}

REQUIRED_CAPABILITIES = {
    "reasoning",
    "coding",
    "tool_calling",
    "multilingual",
    "long_context",
    "local_friendly",
}

VALID_ARCHITECTURES = {"Dense", "MoE"}
VALID_LICENSE_TIERS = {
    "permissive-oss",
    "community-commercial",
    "non-commercial-research",
}


def load_dataset(path: Path = DATA_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_dataset(path: Path = DATA_PATH, docs_path: Path | None = DOCS_DATA_PATH) -> list[str]:
    errors: list[str] = []
    try:
        data = load_dataset(path)
    except Exception as exc:
        return [f"Failed to parse {path}: {exc}"]

    if not isinstance(data.get("models"), list) or not data["models"]:
        errors.append("Dataset must contain a non-empty 'models' list.")
        return errors

    seen_ids: set[str] = set()
    for idx, model in enumerate(data["models"]):
        label = model.get("id", f"index-{idx}")
        missing = REQUIRED_MODEL_FIELDS - set(model.keys())
        if missing:
            errors.append(f"{label}: missing fields {sorted(missing)}")

        model_id = model.get("id")
        if not isinstance(model_id, str) or not model_id:
            errors.append(f"{label}: invalid 'id'")
        elif model_id in seen_ids:
            errors.append(f"{label}: duplicate 'id'")
        else:
            seen_ids.add(model_id)

        if model.get("architecture") not in VALID_ARCHITECTURES:
            errors.append(f"{label}: invalid architecture '{model.get('architecture')}'")

        if model.get("license_tier") not in VALID_LICENSE_TIERS:
            errors.append(f"{label}: invalid license_tier '{model.get('license_tier')}'")

        total_p = model.get("total_params_b")
        active_p = model.get("active_params_b")
        if not isinstance(total_p, (int, float)) or total_p <= 0:
            errors.append(f"{label}: total_params_b must be positive")
        if not isinstance(active_p, (int, float)) or active_p <= 0 or (
            isinstance(total_p, (int, float)) and active_p > total_p
        ):
            errors.append(f"{label}: active_params_b must be positive and <= total_params_b")

        caps = model.get("capabilities")
        if not isinstance(caps, dict) or set(caps.keys()) != REQUIRED_CAPABILITIES:
            errors.append(f"{label}: capabilities keys must match {sorted(REQUIRED_CAPABILITIES)}")

        for url_field in ("huggingface_url", "repo_url"):
            val = model.get(url_field, "")
            if not isinstance(val, str) or not val.startswith("https://"):
                errors.append(f"{label}: {url_field} must start with https://")

    if docs_path is not None and docs_path.exists():
        if path.read_text(encoding="utf-8") != docs_path.read_text(encoding="utf-8"):
            errors.append("docs/models.json is out of sync with models.json")

    return errors


def filter_models(
    models: list[dict[str, Any]],
    *,
    max_vram: float | None = None,
    precision: str = "q4",
    license_tier: str | None = None,
    family: str | None = None,
    use_case: str | None = None,
    architecture: str | None = None,
    vision_only: bool = False,
    open_data_only: bool = False,
) -> list[dict[str, Any]]:
    vram_key = "vram_q4_gb" if precision == "q4" else "vram_fp16_gb"
    results: list[dict[str, Any]] = []
    for m in models:
        if max_vram is not None and m[vram_key] > max_vram:
            continue
        if license_tier and m["license_tier"] != license_tier:
            continue
        if family and m["family"].lower() != family.lower():
            continue
        if architecture and m["architecture"].lower() != architecture.lower():
            continue
        if vision_only and "vision" not in m["modalities"]:
            continue
        if open_data_only and not m["open_data"]:
            continue
        if use_case:
            uc = use_case.lower()
            caps = m["capabilities"]
            matches_uc = uc in [u.lower() for u in m["primary_use_cases"]] or bool(caps.get(uc))
            if not matches_uc:
                continue
        results.append(m)
    return results


def recommend_models(
    models: list[dict[str, Any]],
    *,
    vram: float,
    task: str,
    precision: str = "q4",
    permissive_only: bool = False,
    limit: int = 5,
) -> list[dict[str, Any]]:
    tier = "permissive-oss" if permissive_only else None
    candidates = filter_models(models, max_vram=vram, precision=precision, license_tier=tier)
    vram_key = "vram_q4_gb" if precision == "q4" else "vram_fp16_gb"
    task_l = task.lower()

    def score(m: dict[str, Any]) -> tuple[int, int, float, int]:
        in_primary = 1 if task_l in [u.lower() for u in m["primary_use_cases"]] else 0
        has_cap = 1 if m["capabilities"].get(task_l, False) else 0
        is_permissive = 1 if m["license_tier"] == "permissive-oss" else 0
        # Prefer models that match the task, have permissive licenses, and use available VRAM capacity well
        utilization = float(m[vram_key])
        return (in_primary * 2 + has_cap, is_permissive, utilization, int(m["context_window_k"]))

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked[:limit]


def format_context(context_k: int) -> str:
    if context_k >= 1000:
        millions = context_k / 1000
        return f"{int(millions)}M" if millions.is_integer() else f"{millions:.1f}M"
    return f"{context_k}K"


def format_params(model: dict[str, Any]) -> str:
    total = model["total_params_b"]
    active = model["active_params_b"]
    total_str = f"{int(total)}B" if float(total).is_integer() else f"{total}B"
    if model["architecture"] == "MoE":
        active_str = f"{int(active)}B" if float(active).is_integer() else f"{active}B"
        return f"{total_str} ({active_str} active)"
    return total_str


def print_table(models: list[dict[str, Any]], precision: str = "q4") -> None:
    if not models:
        print("No models matched the selected filters.")
        return

    vram_key = "vram_q4_gb" if precision == "q4" else "vram_fp16_gb"
    vram_label = "VRAM Q4" if precision == "q4" else "VRAM FP16"
    headers = ["ID", "Model", "Params", "Ctx", vram_label, "License"]
    rows = [
        [
            m["id"],
            m["name"],
            format_params(m),
            format_context(m["context_window_k"]),
            f"{m[vram_key]} GB",
            m["license"],
        ]
        for m in models
    ]
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * w for w in widths)
    print(line)
    print(sep)
    for r in rows:
        print(" | ".join(r[i].ljust(widths[i]) for i in range(len(headers))))


def print_comparison(models: list[dict[str, Any]], ids: list[str]) -> int:
    by_id = {m["id"]: m for m in models}
    selected = []
    for mid in ids:
        if mid not in by_id:
            print(f"Unknown model id: {mid}", file=sys.stderr)
            return 1
        selected.append(by_id[mid])

    fields = [
        ("Organization", lambda m: m["organization"]),
        ("Architecture", lambda m: m["architecture"]),
        ("Parameters", format_params),
        ("Context", lambda m: format_context(m["context_window_k"])),
        ("VRAM (Q4)", lambda m: f"{m['vram_q4_gb']} GB"),
        ("VRAM (FP16)", lambda m: f"{m['vram_fp16_gb']} GB"),
        ("License", lambda m: m["license"]),
        ("License Tier", lambda m: m["license_tier"]),
        ("Modalities", lambda m: ", ".join(m["modalities"])),
        ("Ollama Tag", lambda m: m["ollama_tag"] or "N/A"),
        ("Use Cases", lambda m: ", ".join(m["primary_use_cases"])),
    ]

    col_w = [16] + [max(24, len(m["name"]) + 2) for m in selected]
    header = "Field".ljust(col_w[0]) + " | " + " | ".join(
        m["name"].ljust(col_w[i + 1]) for i, m in enumerate(selected)
    )
    print(header)
    print("-+-".join("-" * w for w in col_w))
    for label, fn in fields:
        vals = [fn(m) for m in selected]
        print(
            label.ljust(col_w[0])
            + " | "
            + " | ".join(vals[i].ljust(col_w[i + 1]) for i in range(len(selected)))
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Filter, compare, and recommend open-source LLMs by VRAM, license, and task."
    )
    parser.add_argument("--validate", action="store_true", help="Validate models.json schema and docs sync.")
    parser.add_argument("--vram", type=float, help="Maximum available GPU VRAM in GB.")
    parser.add_argument(
        "--precision",
        choices=("q4", "fp16"),
        default="q4",
        help="Quantization precision for VRAM filtering (default: q4).",
    )
    parser.add_argument(
        "--license",
        dest="license_tier",
        choices=("permissive-oss", "community-commercial", "non-commercial-research"),
        help="Filter by license tier.",
    )
    parser.add_argument("--family", help="Filter by model family (e.g., Qwen, DeepSeek, Llama, Gemma).")
    parser.add_argument("--architecture", choices=("Dense", "MoE"), help="Filter by model architecture.")
    parser.add_argument("--use-case", help="Filter by task (coding, reasoning, local, rag, multimodal, agentic).")
    parser.add_argument("--vision", action="store_true", help="Show only vision-capable multimodal models.")
    parser.add_argument("--open-data", action="store_true", help="Show only models with open training data.")
    parser.add_argument("--compare", nargs="+", metavar="MODEL_ID", help="Compare 2 to 3 models side by side.")
    parser.add_argument("--recommend", action="store_true", help="Recommend top models for a VRAM budget and task.")
    parser.add_argument("--task", default="general", help="Task for --recommend (default: general).")
    parser.add_argument("--permissive-only", action="store_true", help="Restrict --recommend to Apache 2.0 / MIT.")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.validate:
        errors = validate_dataset()
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1
        data = load_dataset()
        print(f"OK: validated {len(data['models'])} models in models.json.")
        return 0

    data = load_dataset()
    models = data["models"]

    if args.compare:
        return print_comparison(models, args.compare[:3])

    if args.recommend:
        budget = args.vram if args.vram is not None else 24.0
        recs = recommend_models(
            models,
            vram=budget,
            task=args.task,
            precision=args.precision,
            permissive_only=args.permissive_only,
        )
        if args.as_json:
            print(json.dumps(recs, indent=2))
            return 0
        print(f"Top open-source LLMs for task '{args.task}' within {budget:g} GB VRAM ({args.precision.upper()}):\n")
        print_table(recs, precision=args.precision)
        for m in recs[:3]:
            if m["ollama_tag"]:
                print(f"  ollama run {m['ollama_tag']}")
        return 0

    filtered = filter_models(
        models,
        max_vram=args.vram,
        precision=args.precision,
        license_tier=args.license_tier,
        family=args.family,
        use_case=args.use_case,
        architecture=args.architecture,
        vision_only=args.vision,
        open_data_only=args.open_data,
    )
    if args.as_json:
        print(json.dumps(filtered, indent=2))
        return 0
    print_table(filtered, precision=args.precision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
