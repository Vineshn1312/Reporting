"""Regression tests for security and robustness fixes.

Run with: python -m unittest discover tests
"""

import json
import os
import re
import tempfile
import unittest

from reportly.ai_analyzer import _build_user_prompt, _redact
from reportly.cli import generate_from_json
from reportly.models import TestResult, TestStatus
from reportly.reporter import ReportlyReporter, safe_json_for_script
from reportly.screenshot import ScreenshotCapture


def _script_body(html: str) -> str:
    return html.split("const REPORT_DATA = ", 1)[1].split(";\n", 1)[0]


class SafeJsonTests(unittest.TestCase):
    def test_script_tag_cannot_be_closed(self):
        out = safe_json_for_script({"name": "</script><script>alert(1)</script>"})
        self.assertNotIn("<", out)
        self.assertNotIn(">", out)
        self.assertEqual(json.loads(out)["name"], "</script><script>alert(1)</script>")

    def test_line_separators_escaped(self):
        out = safe_json_for_script({"x": "a b c&"})
        self.assertNotIn(" ", out)
        self.assertNotIn(" ", out)
        self.assertEqual(json.loads(out)["x"], "a b c&")


class ReporterTests(unittest.TestCase):
    def test_malicious_test_name_is_not_raw_in_script(self):
        with tempfile.TemporaryDirectory() as d:
            r = ReportlyReporter(output_dir=d, open_browser=False)
            r.start_suite("S")
            r.start_test("</script><script>alert(1)</script>")
            r.end_test(TestStatus.PASSED)
            with open(r.generate("r.html"), encoding="utf-8") as f:
                html = f.read()
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("</script><script>alert(1)</script>", json.loads(_script_body(html))["suites"][0]["tests"][0]["name"])

    def test_test_without_suite_is_reported(self):
        r = ReportlyReporter(open_browser=False)
        r.start_test("orphan")
        r.end_test(TestStatus.PASSED)
        data = r._build_report_data()
        self.assertEqual(data["summary"]["total"], 1)


class CliTests(unittest.TestCase):
    def _run(self, data):
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "in.json")
            with open(inp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            with open(generate_from_json(inp, output_dir=d), encoding="utf-8") as f:
                return f.read()

    def test_java_style_input_does_not_crash(self):
        html = self._run({"suites": [{"name": "S", "tests": [{
            "name": "t", "status": "FAILED", "error_message": None, "stack_trace": None,
            "platform": {"platform_type": "Android", "device_name": "Pixel"},
            "steps": [{"name": "s", "status": "PASSED"}, {"name": "s2", "status": "weird"}],
        }]}]})
        data = json.loads(_script_body(html))
        self.assertEqual(data["summary"]["failed"], 1)
        self.assertEqual(data["suites"][0]["tests"][0]["status"], "failed")

    def test_suite_without_tests(self):
        self._run({"suites": [{"name": "S"}, None]})


class AiPromptTests(unittest.TestCase):
    def test_sensitive_parameters_redacted(self):
        self.assertEqual(
            _redact({"password": "p", "apiKey": "k", "user_pin": "1", "user": "bob", "spinner": "x"}),
            {"password": "***", "apiKey": "***", "user_pin": "***", "user": "bob", "spinner": "x"},
        )
        t = TestResult(name="t", status=TestStatus.FAILED, parameters={"password": "hunter2"})
        self.assertNotIn("hunter2", _build_user_prompt(t))


class _FakeSwitch:
    def __init__(self, driver):
        self.driver = driver

    def context(self, ctx):
        self.driver.context = ctx


class _FakeAppiumDriver:
    def __init__(self):
        self.contexts = ["NATIVE_APP", "WEBVIEW_1"]
        self.context = "NATIVE_APP"
        self.switch_to = _FakeSwitch(self)

    def get_screenshot_as_base64(self):
        if self.context == "WEBVIEW_1":
            raise RuntimeError("webview screenshot failed")
        return "AAAA"


class ScreenshotTests(unittest.TestCase):
    def test_appium_context_restored_after_error(self):
        driver = _FakeAppiumDriver()
        # Make the context switch itself fail on the webview.
        orig = driver.switch_to.context

        def switch(ctx):
            if ctx == "WEBVIEW_1":
                raise RuntimeError("no webview")
            orig(ctx)

        driver.switch_to.context = switch
        ScreenshotCapture.capture_appium_contexts(driver)
        self.assertEqual(driver.context, "NATIVE_APP")


class TemplateTests(unittest.TestCase):
    def test_no_unescaped_data_in_inline_handlers(self):
        path = os.path.join(os.path.dirname(__file__), "..", "reportly", "templates", "report_template.html")
        with open(path, encoding="utf-8") as f:
            tpl = f.read()
        # Screenshot data/names must never be interpolated into JS inside onclick attributes.
        self.assertIsNone(re.search(r"onclick=\"[^\"]*\$\{", tpl.replace("toggleDetail(${idx})", "")))


if __name__ == "__main__":
    unittest.main()
