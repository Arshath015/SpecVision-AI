"""Reproducible evaluation runner.

Runs the ACTUAL application pipeline (app.services.pipeline.run_analysis)
against every labeled case in evaluation/data/cases.json and computes the
metrics required by the project brief: extraction accuracy, inventory
top-1/top-3 hit rate, CV mean absolute error, review precision/recall, and
operational metrics (latency, recovery/fallback counts, cost).

Usage (from the evaluation/ directory or anywhere, paths are resolved
relative to this file):

    python evaluation/runner/run_evaluation.py --mode offline
    python evaluation/runner/run_evaluation.py --mode live

--mode offline (default): every case runs with APP_MODE=offline, so the
  deterministic rule-based extractor is used -- no network call, no API
  key required, fully reproducible.
--mode live: every case (except the two that simulate provider failures)
  runs with APP_MODE=live against the REAL configured Groq model. This
  requires GROQ_API_KEY to be set. Results are labeled as genuine live
  metrics, never presented as if they were the offline run.

Cases with "simulate_llm_failure" set always run through a monkeypatched
provider (no real network call either way) specifically to exercise the
retry/fallback/safe-degradation mechanism; they are excluded from
extraction-accuracy aggregates and reported under operational/recovery
metrics instead, since their point is to test recovery, not raw model
accuracy.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from unittest.mock import patch

EVAL_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = EVAL_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import os  # noqa: E402

os.chdir(BACKEND_DIR)  # so pydantic-settings resolves backend/.env consistently

from app.core.config import get_settings  # noqa: E402
from app.services.llm.base import LLMProviderError  # noqa: E402
from app.services.llm.groq_provider import GroqProvider  # noqa: E402
from app.services.pipeline import run_analysis  # noqa: E402

CASES_PATH = EVAL_DIR / "data" / "cases.json"
IMAGES_DIR = EVAL_DIR / "images"
RESULTS_DIR = EVAL_DIR / "results"

CATEGORICAL_FIELDS = [
    ("metal_type", lambda s: s.metal_type.value),
    ("metal_purity", lambda s: s.metal_purity.value),
    ("metal_color", lambda s: s.metal_color.value),
    ("design_category", lambda s: s.design_category.value),
    ("setting_type", lambda s: s.setting_type.value),
    ("center_stone_type", lambda s: s.center_stone.gemstone_type.value),
    ("center_stone_shape", lambda s: s.center_stone.shape.value),
]
NUMERIC_FIELDS = [
    ("center_stone_carat", lambda s: s.center_stone.carat.value, 0.15, "relative"),
    ("side_stone_count_total", lambda s: s.side_stones.count_total.value, 1, "absolute"),
    ("band_width_mm", lambda s: s.dimensions.band_width_mm.value, 0.3, "absolute"),
    ("ring_size_us", lambda s: s.dimensions.ring_size_us.value, 0.5, "absolute"),
]


def _enum_str(v):
    return v.value if hasattr(v, "value") else v


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]


def _numeric_match(pred, gold, tolerance, kind) -> bool:
    if kind == "relative":
        tol = max(tolerance * gold, 0.1) if gold else 0.1
    else:
        tol = tolerance
    return abs(pred - gold) <= tol


MALFORMED_JSON = "{ not valid json"
VALID_MINIMAL_JSON = '{"metal_type": "gold"}'


def _run_case(case: dict, mode: str) -> dict:
    image_bytes = None
    if case.get("image"):
        image_bytes = (IMAGES_DIR / case["image"]).read_bytes()

    simulate = case.get("simulate_llm_failure")
    start = time.perf_counter()
    error = None
    response = None

    try:
        if simulate:
            with patch.dict(os.environ, {"APP_MODE": "live", "GROQ_API_KEY": "eval-dummy-key"}):
                get_settings.cache_clear()
                if simulate == "malformed_then_recover":
                    sequence = iter([MALFORMED_JSON, VALID_MINIMAL_JSON])
                elif simulate == "total_failure":
                    sequence = iter([LLMProviderError("simulated timeout")] * 10)
                else:
                    raise ValueError(f"Unknown simulate_llm_failure: {simulate}")

                def fake_generate_json(self, system_prompt, user_prompt, model):
                    item = next(sequence)
                    if isinstance(item, Exception):
                        raise item
                    return item

                with patch.object(GroqProvider, "generate_json", fake_generate_json):
                    response = run_analysis(case["brief"], image_bytes, request_id=f"eval-{case['case_id']}")
            get_settings.cache_clear()
        else:
            with patch.dict(os.environ, {"APP_MODE": mode}):
                get_settings.cache_clear()
                response = run_analysis(case["brief"], image_bytes, request_id=f"eval-{case['case_id']}")
            get_settings.cache_clear()
    except Exception as exc:  # pragma: no cover - the pipeline is designed not to raise
        error = f"{exc.__class__.__name__}: {exc}"

    elapsed_ms = (time.perf_counter() - start) * 1000
    return {"case": case, "response": response, "error": error, "wall_latency_ms": elapsed_ms}


def _score_extraction(results: list[dict]) -> dict:
    categorical_stats = {name: {"correct": 0, "wrong": 0, "total_known": 0,
                                  "unknown_correct": 0, "unknown_fabricated": 0, "total_unknown": 0}
                          for name, _ in CATEGORICAL_FIELDS}
    numeric_stats = {name: {"correct": 0, "wrong": 0, "total_known": 0,
                              "unknown_correct": 0, "unknown_fabricated": 0, "total_unknown": 0}
                      for name, *_ in NUMERIC_FIELDS}

    for r in results:
        if r["error"] or r["response"] is None or r["case"].get("simulate_llm_failure"):
            continue
        spec = r["response"].specification
        gold = r["case"]["gold_standard"]

        for name, getter in CATEGORICAL_FIELDS:
            gold_val = gold.get(name)
            pred_val = _enum_str(getter(spec))
            stats = categorical_stats[name]
            if gold_val is None:
                stats["total_unknown"] += 1
                if pred_val is None:
                    stats["unknown_correct"] += 1
                else:
                    stats["unknown_fabricated"] += 1
            else:
                stats["total_known"] += 1
                if pred_val == gold_val:
                    stats["correct"] += 1
                else:
                    stats["wrong"] += 1

        for name, getter, tol, kind in NUMERIC_FIELDS:
            gold_val = gold.get(name)
            pred_val = getter(spec)
            stats = numeric_stats[name]
            if gold_val is None:
                stats["total_unknown"] += 1
                if pred_val is None:
                    stats["unknown_correct"] += 1
                else:
                    stats["unknown_fabricated"] += 1
            else:
                stats["total_known"] += 1
                if pred_val is not None and _numeric_match(pred_val, gold_val, tol, kind):
                    stats["correct"] += 1
                else:
                    stats["wrong"] += 1

    def summarize(stats_dict):
        out = {}
        for name, s in stats_dict.items():
            known_acc = s["correct"] / s["total_known"] if s["total_known"] else None
            unknown_rate = s["unknown_correct"] / s["total_unknown"] if s["total_unknown"] else None
            out[name] = {
                "known_field_accuracy": round(known_acc, 3) if known_acc is not None else None,
                "known_field_n": s["total_known"],
                "unknown_correctly_abstained_rate": round(unknown_rate, 3) if unknown_rate is not None else None,
                "unknown_field_n": s["total_unknown"],
                "fabricated_when_should_be_unknown": s["unknown_fabricated"],
            }
        return out

    return {"categorical": summarize(categorical_stats), "numeric": summarize(numeric_stats)}


def _score_matching(results: list[dict]) -> dict:
    top1_hits = top1_total = 0
    top3_hits = top3_total = 0
    no_match_correct = no_match_total = 0

    for r in results:
        if r["error"] or r["response"] is None or r["case"].get("simulate_llm_failure"):
            continue
        case = r["case"]
        match = r["response"].inventory_match
        candidate_ids = [c.product_id for c in match.candidates]

        expected_ids = case.get("expected_inventory_product_ids")
        if expected_ids:
            top1_total += 1
            if candidate_ids and candidate_ids[0] in expected_ids:
                top1_hits += 1
            top3_total += 1
            if any(cid in expected_ids for cid in candidate_ids[:3]):
                top3_hits += 1

        if case.get("expected_no_reliable_match"):
            no_match_total += 1
            if not match.reliable_match_found:
                no_match_correct += 1

    return {
        "top1_hit_rate": round(top1_hits / top1_total, 3) if top1_total else None,
        "top1_n": top1_total,
        "top3_hit_rate": round(top3_hits / top3_total, 3) if top3_total else None,
        "top3_n": top3_total,
        "no_reliable_match_handling_accuracy": round(no_match_correct / no_match_total, 3) if no_match_total else None,
        "no_reliable_match_n": no_match_total,
        "hit_definition": "A hit means the catalog product_id appears at the given rank cutoff among result.inventory_match.candidates, ranked by the deterministic weighted matcher.",
    }


def _score_cv(results: list[dict]) -> dict:
    errors = []
    unavailable = 0
    evaluated = 0
    for r in results:
        if r["error"] or r["response"] is None:
            continue
        case = r["case"]
        ref = case.get("reference_visible_stone_count")
        if ref is None:
            continue
        cv = r["response"].cv_estimate
        if not cv.available or cv.estimated_visible_count is None:
            unavailable += 1
            continue
        evaluated += 1
        errors.append(abs(cv.estimated_visible_count - ref))

    return {
        "mae": round(statistics.mean(errors), 2) if errors else None,
        "evaluated_images": evaluated,
        "unavailable_images_excluded_from_mae": unavailable,
        "note": "MAE is computed only over cases with a human-labeled reference_visible_stone_count and an available CV result. Images where CV correctly reported 'unavailable' are excluded from MAE (that is a successful honest-failure, not an error to average in) and counted separately.",
    }


def _score_review(results: list[dict]) -> dict:
    tp = fp = fn = tn = 0
    fp_cases, fn_cases = [], []
    for r in results:
        if r["error"] or r["response"] is None:
            continue
        case = r["case"]
        expected = case["expected_review"]
        actual = r["response"].confidence_summary.overall_status != "auto_approved"
        if expected and actual:
            tp += 1
        elif not expected and actual:
            fp += 1
            fp_cases.append(case["case_id"])
        elif expected and not actual:
            fn += 1
            fn_cases.append(case["case_id"])
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    flag_rate_n = tp + fp + fn + tn
    flag_rate = (tp + fp) / flag_rate_n if flag_rate_n else None

    return {
        "review_flag_rate": round(flag_rate, 3) if flag_rate is not None else None,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn,
        "false_positive_cases": fp_cases,
        "false_negative_cases": fn_cases,
    }


def _score_operational(results: list[dict]) -> dict:
    successful = sum(1 for r in results if not r["error"])
    failed = sum(1 for r in results if r["error"])
    latencies = [r["response"].processing_metadata.total_latency_ms for r in results if r["response"]]
    method_counts: dict[str, int] = {}
    recovery_event_count = 0
    total_cost = 0.0
    live_calls = 0
    for r in results:
        if not r["response"]:
            continue
        meta = r["response"].processing_metadata
        method_counts[meta.extraction_method.value] = method_counts.get(meta.extraction_method.value, 0) + 1
        recovery_event_count += len(meta.recovery_events)
        if meta.estimated_llm_cost_usd is not None:
            total_cost += meta.estimated_llm_cost_usd
            live_calls += 1

    return {
        "successful_cases": successful,
        "failed_cases": failed,
        "mean_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
        "median_latency_ms": round(statistics.median(latencies), 2) if latencies else None,
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 2) if latencies else None,
        "extraction_method_counts": method_counts,
        "total_recovery_events": recovery_event_count,
        "live_model_calls": live_calls,
        "estimated_total_llm_cost_usd": round(total_cost, 4),
    }


def run(mode: str) -> dict:
    cases = load_cases()
    results = [_run_case(c, mode) for c in cases]

    report = {
        "run_mode": mode,
        "is_genuine_live_run": mode == "live",
        "case_count": len(cases),
        "extraction": _score_extraction(results),
        "inventory_matching": _score_matching(results),
        "computer_vision": _score_cv(results),
        "review_behavior": _score_review(results),
        "operational": _score_operational(results),
        "per_case": [
            {
                "case_id": r["case"]["case_id"],
                "error": r["error"],
                "overall_status": r["response"].confidence_summary.overall_status if r["response"] else None,
                "extraction_method": r["response"].processing_metadata.extraction_method.value if r["response"] else None,
                "cv_available": r["response"].cv_estimate.available if r["response"] else None,
                "cv_count": r["response"].cv_estimate.estimated_visible_count if r["response"] else None,
                "selected_product_id": (r["response"].inventory_match.selected.product_id
                                          if r["response"] and r["response"].inventory_match.selected else None),
                "total_latency_ms": r["response"].processing_metadata.total_latency_ms if r["response"] else None,
                "review_flags": [f.code for f in r["response"].confidence_summary.review_flags] if r["response"] else [],
                "recovery_events": (
                    [{"action": e.action, "detail": e.detail} for e in r["response"].processing_metadata.recovery_events]
                    if r["response"] else []
                ),
            }
            for r in results
        ],
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="Run the SpecVision AI evaluation harness.")
    parser.add_argument("--mode", choices=["offline", "live"], default="offline")
    args = parser.parse_args()

    if args.mode == "live" and not os.environ.get("GROQ_API_KEY"):
        # Settings may still load the key from backend/.env; only hard-fail if truly absent.
        get_settings.cache_clear()
        if not get_settings().groq_api_key:
            print("ERROR: --mode live requires GROQ_API_KEY (env var or backend/.env).", file=sys.stderr)
            sys.exit(1)
        get_settings.cache_clear()

    report = run(args.mode)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"evaluation_{args.mode}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary_path = RESULTS_DIR / f"evaluation_{args.mode}_summary.md"
    summary_path.write_text(render_markdown_summary(report), encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"Wrote {summary_path}")
    print(render_markdown_summary(report))


def render_markdown_summary(report: dict) -> str:
    ex = report["extraction"]
    inv = report["inventory_matching"]
    cv = report["computer_vision"]
    rev = report["review_behavior"]
    op = report["operational"]

    lines = [
        f"# Evaluation summary -- mode: {report['run_mode']} "
        f"({'GENUINE live LLM run' if report['is_genuine_live_run'] else 'offline deterministic run, no network'})",
        "",
        f"Cases: {report['case_count']}  |  Successful: {op['successful_cases']}  |  Failed: {op['failed_cases']}",
        "",
        "## Extraction -- categorical fields (accuracy on cases with a known gold value)",
        "| Field | Accuracy | N | Unknown-abstain rate | Unknown N | Fabricated |",
        "|---|---|---|---|---|---|",
    ]
    for name, s in ex["categorical"].items():
        lines.append(f"| {name} | {s['known_field_accuracy']} | {s['known_field_n']} | "
                      f"{s['unknown_correctly_abstained_rate']} | {s['unknown_field_n']} | {s['fabricated_when_should_be_unknown']} |")

    lines += ["", "## Extraction -- numeric fields (tolerance-based)",
              "| Field | Accuracy | N | Unknown-abstain rate | Unknown N | Fabricated |",
              "|---|---|---|---|---|---|"]
    for name, s in ex["numeric"].items():
        lines.append(f"| {name} | {s['known_field_accuracy']} | {s['known_field_n']} | "
                      f"{s['unknown_correctly_abstained_rate']} | {s['unknown_field_n']} | {s['fabricated_when_should_be_unknown']} |")

    lines += [
        "",
        "## Inventory matching",
        f"- Top-1 hit rate: {inv['top1_hit_rate']} (n={inv['top1_n']})",
        f"- Top-3 hit rate: {inv['top3_hit_rate']} (n={inv['top3_n']})",
        f"- No-reliable-match handling accuracy: {inv['no_reliable_match_handling_accuracy']} (n={inv['no_reliable_match_n']})",
        "",
        "## Computer vision",
        f"- MAE (visible stone count): {cv['mae']} over {cv['evaluated_images']} image(s)",
        f"- Unavailable (excluded from MAE): {cv['unavailable_images_excluded_from_mae']}",
        "",
        "## Review behavior",
        f"- Flag rate: {rev['review_flag_rate']}  Precision: {rev['precision']}  Recall: {rev['recall']}",
        f"- TP={rev['true_positive']} FP={rev['false_positive']} FN={rev['false_negative']} TN={rev['true_negative']}",
        f"- False positive cases: {rev['false_positive_cases']}",
        f"- False negative cases: {rev['false_negative_cases']}",
        "",
        "## Operational",
        f"- Mean latency: {op['mean_latency_ms']}ms  Median: {op['median_latency_ms']}ms  P95: {op['p95_latency_ms']}ms",
        f"- Extraction method distribution: {op['extraction_method_counts']}",
        f"- Total recovery events: {op['total_recovery_events']}",
        f"- Live model calls: {op['live_model_calls']}  Estimated cost: ${op['estimated_total_llm_cost_usd']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
