"""AI-powered failure analysis for test results."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from reportly.models import AIAnalysis, TestResult, TestStatus

logger = logging.getLogger("reportly.ai_analyzer")

SYSTEM_PROMPT = """You are an expert QA engineer analyzing automated test failures.
Given a failed test's details (name, error message, stack trace, test steps, platform info),
provide a structured analysis in JSON format with these fields:

{
  "failure_category": "One of: Element Not Found, Timeout, Assertion Failure, Network Error, App Crash, Authentication, Data Issue, Environment Issue, Flaky Test, Configuration Error, Permission Denied, Unknown",
  "root_cause": "A clear 1-2 sentence explanation of WHY this test failed",
  "suggestion": "A concrete, actionable recommendation to fix or investigate this failure",
  "confidence": 0.85,
  "similar_failures": ["List of common patterns that match this failure type"]
}

Be concise and technical. Focus on actionable insights."""


_SENSITIVE_KEY = re.compile(r"pass(word|wd)?|secret|token|api[_-]?key|auth|credential|cookie|(^|[_-])pin($|[_-])", re.I)


def _redact(params: dict) -> dict:
    """Hide values like passwords/tokens before sending test data to a third-party AI API."""
    return {k: ("***" if _SENSITIVE_KEY.search(str(k)) else v) for k, v in params.items()}


def _build_user_prompt(test: TestResult) -> str:
    parts = [f"Test Name: {test.name}"]
    if test.suite_name:
        parts.append(f"Suite: {test.suite_name}")
    if test.platform:
        parts.append(f"Platform: {test.platform.display_name}")
    parts.append(f"Status: {test.status.value}")
    if test.error_message:
        parts.append(f"Error Message: {test.error_message}")
    if test.stack_trace:
        trace = test.stack_trace
        if len(trace) > 2000:
            trace = trace[:1000] + "\n... (truncated) ...\n" + trace[-1000:]
        parts.append(f"Stack Trace:\n{trace}")
    if test.steps:
        failed_steps = [s for s in test.steps if s.status.value == "failed"]
        if failed_steps:
            step_info = []
            for s in failed_steps:
                step_info.append(f"  - {s.name}: {s.error_message}" if s.error_message else f"  - {s.name}")
            parts.append("Failed Steps:\n" + "\n".join(step_info))
    if test.parameters:
        parts.append(f"Parameters: {json.dumps(_redact(test.parameters), default=str)}")
    return "\n".join(parts)


class AIFailureAnalyzer:
    """Analyzes test failures using OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        temperature: float = 0.3,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = OpenAI(**kwargs)
            except ImportError:
                raise ImportError("Install openai package: pip install openai")
        return self._client

    def analyze(self, test: TestResult) -> AIAnalysis:
        """Analyze a single failed test."""
        if test.status not in (TestStatus.FAILED, TestStatus.BROKEN):
            return AIAnalysis()

        if not self.api_key:
            return self._fallback_analysis(test)

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(test)},
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            return AIAnalysis(
                failure_category=data.get("failure_category", "Unknown"),
                root_cause=data.get("root_cause", ""),
                suggestion=data.get("suggestion", ""),
                confidence=float(data.get("confidence", 0)),
                similar_failures=data.get("similar_failures", []),
                raw_response=raw,
            )
        except Exception as e:
            logger.error("AI analysis failed: %s", e)
            return self._fallback_analysis(test)

    def analyze_batch(self, tests: list[TestResult]) -> dict[str, AIAnalysis]:
        """Analyze multiple failed tests. Returns a map of test_id -> AIAnalysis."""
        failed = [t for t in tests if t.status in (TestStatus.FAILED, TestStatus.BROKEN)]
        return {t.test_id: self.analyze(t) for t in failed}

    @staticmethod
    def _fallback_analysis(test: TestResult) -> AIAnalysis:
        """Rule-based fallback when AI API is unavailable."""
        error = (test.error_message + " " + test.stack_trace).lower()
        category = "Unknown"
        root_cause = "Unable to determine root cause without AI analysis."
        suggestion = "Review the error message and stack trace manually."
        confidence = 0.4

        rules = [
            (
                ["nosuchelement", "element not found", "unable to locate"],
                "Element Not Found",
                "A UI element could not be found on the page/screen.",
                "Verify the locator strategy. The element may have changed or may not be loaded yet. Add explicit waits.",
                0.75,
            ),
            (
                ["timeout", "timed out", "timeoutexception"],
                "Timeout",
                "The operation exceeded the allowed time limit.",
                "Increase timeout duration or check if the app/page is responding slowly. Verify network conditions.",
                0.70,
            ),
            (
                ["assert", "expected", "actual", "not equal", "mismatch"],
                "Assertion Failure",
                "Test assertion did not match expected result.",
                "Verify expected values against current application state. Data or business logic may have changed.",
                0.70,
            ),
            (
                ["connection", "network", "unreachable", "econnrefused", "dns"],
                "Network Error",
                "A network connectivity issue was detected.",
                "Check network connectivity, server availability, and firewall rules.",
                0.65,
            ),
            (
                ["crash", "terminated", "killed", "segfault", "anr"],
                "App Crash",
                "The application crashed during test execution.",
                "Check application logs for crash details. This may indicate a critical bug in the application.",
                0.70,
            ),
            (
                ["login", "auth", "401", "403", "unauthorized", "forbidden", "credentials"],
                "Authentication",
                "An authentication or authorization error occurred.",
                "Verify test credentials are valid and the user has appropriate permissions.",
                0.65,
            ),
            (
                ["stale", "staleelement", "detached"],
                "Element Not Found",
                "A DOM element became stale (page changed after element lookup).",
                "Re-locate the element after page transitions. Use explicit waits for DOM stability.",
                0.75,
            ),
            (
                ["permission", "denied", "not allowed"],
                "Permission Denied",
                "The operation was denied due to insufficient permissions.",
                "Check app permissions (camera, storage, location) and OS-level settings.",
                0.60,
            ),
        ]

        for keywords, cat, cause, sug, conf in rules:
            if any(kw in error for kw in keywords):
                category = cat
                root_cause = cause
                suggestion = sug
                confidence = conf
                break

        return AIAnalysis(
            failure_category=category,
            root_cause=root_cause,
            suggestion=suggestion,
            confidence=confidence,
            similar_failures=[],
        )
