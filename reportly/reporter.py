"""Core reporter that generates the HTML report."""

from __future__ import annotations

import json
import logging
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

from reportly.ai_analyzer import AIFailureAnalyzer
from reportly.models import (
    AIAnalysis,
    Attachment,
    AttachmentType,
    EnvironmentInfo,
    Platform,
    PlatformType,
    StepStatus,
    TestResult,
    TestStatus,
    TestStep,
    TestSuite,
)
from reportly.screenshot import ScreenshotCapture


def safe_json_for_script(data: Any) -> str:
    """Serialize data as JSON that is safe to embed inside an HTML <script> tag.

    Escapes characters that could close the script tag or break JS parsing,
    e.g. a test name containing "</script>".
    """
    return (
        json.dumps(data, default=str)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


logger = logging.getLogger("reportly")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class ReportlyReporter:
    """Main class for building and generating test reports."""

    def __init__(
        self,
        title: str = "Test Execution Report",
        description: str = "",
        output_dir: str = "./reports",
        ai_api_key: Optional[str] = None,
        ai_model: str = "gpt-4o-mini",
        ai_base_url: Optional[str] = None,
        auto_screenshot: bool = True,
        open_browser: bool = True,
        theme: str = "dark",
    ):
        self.title = title
        self.description = description
        self.output_dir = output_dir
        self.auto_screenshot = auto_screenshot
        self.open_browser = open_browser
        self.theme = theme

        self._suites: list[TestSuite] = []
        self._current_suite: Optional[TestSuite] = None
        self._current_test: Optional[TestResult] = None
        self._drivers: dict[str, Any] = {}

        self.ai_analyzer = AIFailureAnalyzer(
            api_key=ai_api_key,
            model=ai_model,
            base_url=ai_base_url,
        )

        self._env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=True,
        )

    def start_suite(
        self,
        name: str,
        description: str = "",
        environment: Optional[EnvironmentInfo] = None,
        **metadata,
    ) -> TestSuite:
        suite = TestSuite(
            name=name,
            description=description,
            environment=environment,
            metadata=metadata,
        )
        self._suites.append(suite)
        self._current_suite = suite
        return suite

    def end_suite(self):
        if self._current_suite:
            self._current_suite.finish()
        self._current_suite = None

    def start_test(
        self,
        name: str,
        description: str = "",
        category: str = "",
        tags: Optional[list[str]] = None,
        priority: str = "",
        platform: Optional[Platform] = None,
        parameters: Optional[dict] = None,
        links: Optional[dict] = None,
        **metadata,
    ) -> TestResult:
        test = TestResult(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            priority=priority,
            platform=platform,
            parameters=parameters or {},
            links=links or {},
            metadata=metadata,
        )
        self._current_test = test
        if not self._current_suite:
            # Without a suite the test would be silently left out of the report.
            self.start_suite("Default Suite")
        self._current_suite.add_test(test)
        return test

    def end_test(
        self,
        status: TestStatus,
        error_message: str = "",
        stack_trace: str = "",
        driver: Any = None,
    ):
        if not self._current_test:
            return

        self._current_test.finish(status, error_message, stack_trace)

        if driver and self.auto_screenshot and status in (TestStatus.FAILED, TestStatus.BROKEN):
            attachment = ScreenshotCapture.capture(driver, "failure_screenshot")
            if attachment:
                self._current_test.attachments.append(attachment)

        if status in (TestStatus.FAILED, TestStatus.BROKEN):
            analysis = self.ai_analyzer.analyze(self._current_test)
            self._current_test.ai_analysis = analysis

        self._current_test = None

    def log_step(
        self,
        name: str,
        status: StepStatus = StepStatus.PASSED,
        description: str = "",
        duration_ms: float = 0,
        error_message: str = "",
        driver: Any = None,
        screenshot: bool = False,
    ) -> Optional[TestStep]:
        if not self._current_test:
            return None

        step = self._current_test.add_step(
            name=name,
            status=status,
            description=description,
            duration_ms=duration_ms,
            error_message=error_message,
        )

        if driver and screenshot:
            attachment = ScreenshotCapture.capture(driver, f"step_{name}")
            if attachment:
                step.attachments.append(attachment)

        return step

    def attach_screenshot(self, driver: Any, name: str = "screenshot") -> Optional[Attachment]:
        attachment = ScreenshotCapture.capture(driver, name)
        if attachment and self._current_test:
            self._current_test.attachments.append(attachment)
        return attachment

    def attach_screenshot_base64(self, b64_data: str, name: str = "screenshot") -> Attachment:
        attachment = ScreenshotCapture.from_base64(b64_data, name)
        if self._current_test:
            self._current_test.attachments.append(attachment)
        return attachment

    def attach_screenshot_file(self, filepath: str, name: Optional[str] = None) -> Optional[Attachment]:
        attachment = ScreenshotCapture.from_file(filepath, name)
        if attachment and self._current_test:
            self._current_test.attachments.append(attachment)
        return attachment

    def attach_log(self, name: str, content: str) -> Attachment:
        attachment = Attachment(name=name, attachment_type=AttachmentType.LOG, data=content)
        if self._current_test:
            self._current_test.attachments.append(attachment)
        return attachment

    def register_driver(self, name: str, driver: Any):
        self._drivers[name] = driver

    def detect_platform(self, driver: Any) -> Platform:
        """Auto-detect platform from a Selenium/Appium driver's capabilities."""
        try:
            caps = driver.capabilities
        except Exception:
            return Platform(platform_type=PlatformType.WEB)

        platform_name = (caps.get("platformName") or "").lower()
        if platform_name == "android":
            return Platform(
                platform_type=PlatformType.ANDROID,
                os_name="Android",
                os_version=caps.get("platformVersion", ""),
                device_name=caps.get("deviceName", ""),
                device_udid=caps.get("udid", ""),
                app_name=caps.get("appPackage", caps.get("app", "")),
                automation_name=caps.get("automationName", ""),
                screen_resolution=caps.get("deviceScreenSize", ""),
            )
        elif platform_name == "ios":
            return Platform(
                platform_type=PlatformType.IOS,
                os_name="iOS",
                os_version=caps.get("platformVersion", ""),
                device_name=caps.get("deviceName", ""),
                device_udid=caps.get("udid", ""),
                app_name=caps.get("bundleId", caps.get("app", "")),
                automation_name=caps.get("automationName", ""),
            )
        else:
            return Platform(
                platform_type=PlatformType.WEB,
                os_name=caps.get("platformName", ""),
                browser_name=caps.get("browserName", ""),
                browser_version=caps.get("browserVersion", ""),
                screen_resolution=f"{caps.get('screenResolution', '')}",
            )

    def _build_report_data(self) -> dict:
        all_tests = []
        for suite in self._suites:
            all_tests.extend(suite.tests)

        total = len(all_tests)
        passed = sum(1 for t in all_tests if t.status == TestStatus.PASSED)
        failed = sum(1 for t in all_tests if t.status == TestStatus.FAILED)
        skipped = sum(1 for t in all_tests if t.status == TestStatus.SKIPPED)
        broken = sum(1 for t in all_tests if t.status == TestStatus.BROKEN)
        blocked = sum(1 for t in all_tests if t.status == TestStatus.BLOCKED)
        warning = sum(1 for t in all_tests if t.status == TestStatus.WARNING)
        pass_rate = (passed / total * 100) if total > 0 else 0

        total_duration = sum(t.duration_ms for t in all_tests)

        platform_stats = {}
        for t in all_tests:
            key = t.platform.display_name if t.platform else "Unknown"
            if key not in platform_stats:
                platform_stats[key] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            platform_stats[key]["total"] += 1
            if t.status == TestStatus.PASSED:
                platform_stats[key]["passed"] += 1
            elif t.status in (TestStatus.FAILED, TestStatus.BROKEN):
                platform_stats[key]["failed"] += 1
            else:
                platform_stats[key]["skipped"] += 1

        category_stats = {}
        for t in all_tests:
            key = t.category or "Uncategorized"
            if key not in category_stats:
                category_stats[key] = {"total": 0, "passed": 0, "failed": 0}
            category_stats[key]["total"] += 1
            if t.status == TestStatus.PASSED:
                category_stats[key]["passed"] += 1
            elif t.status in (TestStatus.FAILED, TestStatus.BROKEN):
                category_stats[key]["failed"] += 1

        ai_analyses = []
        failure_categories = {}
        for t in all_tests:
            if t.ai_analysis and t.ai_analysis.failure_category:
                ai_analyses.append({
                    "test_name": t.name,
                    "test_id": t.test_id,
                    "analysis": t.ai_analysis.to_dict(),
                })
                cat = t.ai_analysis.failure_category
                failure_categories[cat] = failure_categories.get(cat, 0) + 1

        all_tags = set()
        for t in all_tests:
            all_tags.update(t.tags)

        return {
            "title": self.title,
            "description": self.description,
            "theme": self.theme,
            "generated_at": datetime.now().isoformat(),
            "generated_at_display": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "broken": broken,
                "blocked": blocked,
                "warning": warning,
                "pass_rate": round(pass_rate, 1),
                "total_duration_ms": total_duration,
                "total_duration_display": self._format_duration(total_duration),
                "suite_count": len(self._suites),
            },
            "platform_stats": platform_stats,
            "category_stats": category_stats,
            "failure_categories": failure_categories,
            "all_tags": sorted(all_tags),
            "ai_analyses": ai_analyses,
            "suites": [s.to_dict() for s in self._suites],
        }

    @staticmethod
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

    def generate(self, filename: str = "report.html") -> str:
        """Generate the HTML report and return the file path."""
        os.makedirs(self.output_dir, exist_ok=True)
        report_data = self._build_report_data()

        template = self._env.get_template("report_template.html")
        html_content = template.render(
            data=report_data,
            data_json=safe_json_for_script(report_data),
        )

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Report generated: %s", filepath)

        if self.open_browser:
            try:
                webbrowser.open(f"file://{os.path.abspath(filepath)}")
            except Exception:
                pass

        return os.path.abspath(filepath)

    def generate_json(self, filename: str = "report.json") -> str:
        """Export raw report data as JSON."""
        os.makedirs(self.output_dir, exist_ok=True)
        report_data = self._build_report_data()
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)
        return os.path.abspath(filepath)
