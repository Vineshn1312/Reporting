"""CLI entry point for generating reports from JSON input.

This enables non-Python projects (Java, Kotlin, etc.) to produce JSON
test results and then invoke Reportly to generate the HTML report.

Usage:
    python -m reportly --input results.json --output ./reports --title "My Report"
    python -m reportly --input results.json --ai-key sk-... --open
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from reportly.ai_analyzer import AIFailureAnalyzer
from reportly.models import AIAnalysis, TestStatus

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def _format_duration(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = int(minutes // 60)
    mins = minutes % 60
    return f"{hours}h {mins}m {secs:.0f}s"


def _enrich_with_ai(data: dict, api_key: str, model: str, base_url: str | None) -> dict:
    """Run AI analysis on failed tests in the raw data."""
    analyzer = AIFailureAnalyzer(api_key=api_key, model=model, base_url=base_url)

    ai_analyses = []
    failure_categories: dict[str, int] = {}

    for suite in data.get("suites", []):
        for test in suite.get("tests", []):
            status = test.get("status", "")
            if status not in ("failed", "broken"):
                continue

            from reportly.models import TestResult, Platform, PlatformType, TestStep, StepStatus

            tr = TestResult(
                name=test.get("name", ""),
                test_id=test.get("test_id", ""),
                suite_name=test.get("suite_name", ""),
                error_message=test.get("error_message", ""),
                stack_trace=test.get("stack_trace", ""),
                parameters=test.get("parameters", {}),
                status=TestStatus.FAILED if status == "failed" else TestStatus.BROKEN,
            )

            p = test.get("platform")
            if p:
                tr.platform = Platform(
                    platform_type=PlatformType(p.get("platform_type", "web")),
                    os_name=p.get("os_name", ""),
                    browser_name=p.get("browser_name", ""),
                    device_name=p.get("device_name", ""),
                )

            for s in test.get("steps", []):
                tr.add_step(
                    name=s.get("name", ""),
                    status=StepStatus(s.get("status", "info")),
                    error_message=s.get("error_message", ""),
                )

            analysis = analyzer.analyze(tr)
            analysis_dict = analysis.to_dict()
            test["ai_analysis"] = analysis_dict

            if analysis.failure_category:
                ai_analyses.append({
                    "test_name": test.get("name", ""),
                    "test_id": test.get("test_id", ""),
                    "analysis": analysis_dict,
                })
                cat = analysis.failure_category
                failure_categories[cat] = failure_categories.get(cat, 0) + 1

    data["ai_analyses"] = ai_analyses
    data["failure_categories"] = failure_categories
    return data


def _compute_summary(data: dict) -> dict:
    """Compute summary statistics if not already present."""
    if data.get("summary", {}).get("total", 0) > 0:
        return data

    all_tests = []
    for suite in data.get("suites", []):
        all_tests.extend(suite.get("tests", []))

    total = len(all_tests)
    passed = sum(1 for t in all_tests if t.get("status") == "passed")
    failed = sum(1 for t in all_tests if t.get("status") == "failed")
    skipped = sum(1 for t in all_tests if t.get("status") == "skipped")
    broken = sum(1 for t in all_tests if t.get("status") == "broken")
    blocked = sum(1 for t in all_tests if t.get("status") == "blocked")
    warning = sum(1 for t in all_tests if t.get("status") == "warning")
    pass_rate = (passed / total * 100) if total > 0 else 0
    total_duration = sum(t.get("duration_ms", 0) for t in all_tests)

    platform_stats: dict[str, dict] = {}
    category_stats: dict[str, dict] = {}
    all_tags: set[str] = set()

    for t in all_tests:
        p = t.get("platform")
        pkey = "Unknown"
        if p:
            pt = p.get("platform_type", "")
            if pt == "web":
                pkey = " ".join(filter(None, [p.get("browser_name"), p.get("browser_version"), p.get("os_name")])) or "Web"
            else:
                pkey = " ".join(filter(None, [p.get("device_name"), p.get("os_name"), p.get("os_version")])) or pt

        if pkey not in platform_stats:
            platform_stats[pkey] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        platform_stats[pkey]["total"] += 1
        st = t.get("status", "")
        if st == "passed":
            platform_stats[pkey]["passed"] += 1
        elif st in ("failed", "broken"):
            platform_stats[pkey]["failed"] += 1
        else:
            platform_stats[pkey]["skipped"] += 1

        cat = t.get("category") or "Uncategorized"
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "failed": 0}
        category_stats[cat]["total"] += 1
        if st == "passed":
            category_stats[cat]["passed"] += 1
        elif st in ("failed", "broken"):
            category_stats[cat]["failed"] += 1

        for tag in t.get("tags", []):
            all_tags.add(tag)

    data["summary"] = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "broken": broken,
        "blocked": blocked,
        "warning": warning,
        "pass_rate": round(pass_rate, 1),
        "total_duration_ms": total_duration,
        "total_duration_display": _format_duration(total_duration),
        "suite_count": len(data.get("suites", [])),
    }
    data["platform_stats"] = platform_stats
    data["category_stats"] = category_stats
    data.setdefault("all_tags", sorted(all_tags))
    data.setdefault("ai_analyses", [])
    data.setdefault("failure_categories", {})

    return data


def generate_from_json(
    input_path: str,
    output_dir: str = "./reports",
    filename: str = "report.html",
    title: str | None = None,
    description: str = "",
    theme: str = "dark",
    ai_api_key: str = "",
    ai_model: str = "gpt-4o-mini",
    ai_base_url: str | None = None,
    open_browser: bool = False,
) -> str:
    """Read a JSON results file and generate the HTML report."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if title:
        data["title"] = title
    data.setdefault("title", "Test Execution Report")
    data["description"] = description or data.get("description", "")
    data["theme"] = theme
    data["generated_at"] = datetime.now().isoformat()
    data["generated_at_display"] = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    data = _compute_summary(data)

    if ai_api_key:
        data = _enrich_with_ai(data, ai_api_key, ai_model, ai_base_url)
    elif not data.get("ai_analyses"):
        data = _enrich_with_ai(data, "", ai_model, None)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("report_template.html")
    html = template.render(data=data, data_json=json.dumps(data, default=str))

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    abs_path = os.path.abspath(filepath)

    if open_browser:
        try:
            webbrowser.open(f"file://{abs_path}")
        except Exception:
            pass

    return abs_path


def main():
    parser = argparse.ArgumentParser(
        prog="reportly",
        description="Reportly — Generate HTML test reports from JSON results",
    )
    parser.add_argument("-i", "--input", required=True, help="Path to JSON results file")
    parser.add_argument("-o", "--output-dir", default="./reports", help="Output directory (default: ./reports)")
    parser.add_argument("-f", "--filename", default="report.html", help="Output filename (default: report.html)")
    parser.add_argument("-t", "--title", help="Report title")
    parser.add_argument("-d", "--description", default="", help="Report description")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="Theme (default: dark)")
    parser.add_argument("--ai-key", default="", help="OpenAI API key for AI failure analysis")
    parser.add_argument("--ai-model", default="gpt-4o-mini", help="AI model name")
    parser.add_argument("--ai-base-url", help="Custom AI API base URL (e.g. Ollama)")
    parser.add_argument("--open", action="store_true", help="Open report in browser after generation")

    args = parser.parse_args()

    path = generate_from_json(
        input_path=args.input,
        output_dir=args.output_dir,
        filename=args.filename,
        title=args.title,
        description=args.description,
        theme=args.theme,
        ai_api_key=args.ai_key,
        ai_model=args.ai_model,
        ai_base_url=args.ai_base_url,
        open_browser=args.open,
    )
    print(f"Report generated: {path}")


if __name__ == "__main__":
    main()
