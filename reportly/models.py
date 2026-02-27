"""Data models for test reporting."""

from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BROKEN = "broken"
    BLOCKED = "blocked"
    WARNING = "warning"


class StepStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INFO = "info"
    WARNING = "warning"


class PlatformType(Enum):
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"
    DESKTOP = "desktop"
    API = "api"


class AttachmentType(Enum):
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    LOG = "log"
    HTML = "html"
    JSON_DATA = "json"
    TEXT = "text"


@dataclass
class Attachment:
    name: str
    attachment_type: AttachmentType
    data: str  # base64-encoded for binary, plain text otherwise
    mime_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.mime_type:
            mime_map = {
                AttachmentType.SCREENSHOT: "image/png",
                AttachmentType.VIDEO: "video/mp4",
                AttachmentType.LOG: "text/plain",
                AttachmentType.HTML: "text/html",
                AttachmentType.JSON_DATA: "application/json",
                AttachmentType.TEXT: "text/plain",
            }
            self.mime_type = mime_map.get(self.attachment_type, "application/octet-stream")


@dataclass
class Platform:
    platform_type: PlatformType
    os_name: str = ""
    os_version: str = ""
    browser_name: str = ""
    browser_version: str = ""
    device_name: str = ""
    device_udid: str = ""
    app_name: str = ""
    app_version: str = ""
    automation_name: str = ""
    screen_resolution: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        parts = []
        if self.platform_type == PlatformType.WEB:
            if self.browser_name:
                parts.append(self.browser_name)
            if self.browser_version:
                parts.append(self.browser_version)
            if self.os_name:
                parts.append(f"on {self.os_name}")
        elif self.platform_type in (PlatformType.ANDROID, PlatformType.IOS):
            if self.device_name:
                parts.append(self.device_name)
            if self.os_name:
                parts.append(self.os_name)
            if self.os_version:
                parts.append(self.os_version)
        else:
            parts.append(self.platform_type.value)
            if self.os_name:
                parts.append(self.os_name)
        return " ".join(parts) if parts else self.platform_type.value

    def to_dict(self) -> dict:
        return {
            "platform_type": self.platform_type.value,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "browser_name": self.browser_name,
            "browser_version": self.browser_version,
            "device_name": self.device_name,
            "device_udid": self.device_udid,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "automation_name": self.automation_name,
            "screen_resolution": self.screen_resolution,
            "extra": self.extra,
        }


@dataclass
class TestStep:
    name: str
    status: StepStatus = StepStatus.INFO
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0
    attachments: list[Attachment] = field(default_factory=list)
    error_message: str = ""
    sub_steps: list[TestStep] = field(default_factory=list)

    def add_screenshot(self, name: str, data: str) -> Attachment:
        attachment = Attachment(
            name=name,
            attachment_type=AttachmentType.SCREENSHOT,
            data=data,
        )
        self.attachments.append(attachment)
        return attachment

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "attachments": [
                {
                    "name": a.name,
                    "type": a.attachment_type.value,
                    "data": a.data,
                    "mime_type": a.mime_type,
                }
                for a in self.attachments
            ],
            "sub_steps": [s.to_dict() for s in self.sub_steps],
        }


@dataclass
class AIAnalysis:
    failure_category: str = ""
    root_cause: str = ""
    suggestion: str = ""
    confidence: float = 0.0
    similar_failures: list[str] = field(default_factory=list)
    raw_response: str = ""

    def to_dict(self) -> dict:
        return {
            "failure_category": self.failure_category,
            "root_cause": self.root_cause,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "similar_failures": self.similar_failures,
        }


@dataclass
class RetryInfo:
    attempt: int = 1
    max_attempts: int = 1
    previous_errors: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    name: str
    status: TestStatus = TestStatus.PASSED
    test_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    suite_name: str = ""
    description: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    priority: str = ""
    platform: Optional[Platform] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0
    steps: list[TestStep] = field(default_factory=list)
    error_message: str = ""
    stack_trace: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    ai_analysis: Optional[AIAnalysis] = None
    retry_info: Optional[RetryInfo] = None
    parameters: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    links: dict = field(default_factory=dict)  # e.g. {"jira": "PROJ-123", "testcase": "TC-456"}

    def finish(self, status: TestStatus, error_message: str = "", stack_trace: str = ""):
        self.end_time = datetime.now()
        self.status = status
        self.error_message = error_message
        self.stack_trace = stack_trace
        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def add_step(self, name: str, status: StepStatus = StepStatus.INFO, **kwargs) -> TestStep:
        step = TestStep(name=name, status=status, **kwargs)
        self.steps.append(step)
        return step

    def add_screenshot(self, name: str, data: str) -> Attachment:
        attachment = Attachment(
            name=name,
            attachment_type=AttachmentType.SCREENSHOT,
            data=data,
        )
        self.attachments.append(attachment)
        return attachment

    @property
    def screenshot_count(self) -> int:
        count = len([a for a in self.attachments if a.attachment_type == AttachmentType.SCREENSHOT])
        for step in self.steps:
            count += len([a for a in step.attachments if a.attachment_type == AttachmentType.SCREENSHOT])
        return count

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "test_id": self.test_id,
            "status": self.status.value,
            "suite_name": self.suite_name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "priority": self.priority,
            "platform": self.platform.to_dict() if self.platform else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "steps": [s.to_dict() for s in self.steps],
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "attachments": [
                {
                    "name": a.name,
                    "type": a.attachment_type.value,
                    "data": a.data,
                    "mime_type": a.mime_type,
                }
                for a in self.attachments
            ],
            "ai_analysis": self.ai_analysis.to_dict() if self.ai_analysis else None,
            "retry_info": {
                "attempt": self.retry_info.attempt,
                "max_attempts": self.retry_info.max_attempts,
                "previous_errors": self.retry_info.previous_errors,
            }
            if self.retry_info
            else None,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "links": self.links,
            "screenshot_count": self.screenshot_count,
        }


@dataclass
class EnvironmentInfo:
    name: str = ""
    url: str = ""
    build_number: str = ""
    build_url: str = ""
    branch: str = ""
    commit_hash: str = ""
    ci_tool: str = ""
    runner: str = ""
    triggered_by: str = ""
    custom: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {
            "name": self.name,
            "url": self.url,
            "build_number": self.build_number,
            "build_url": self.build_url,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "ci_tool": self.ci_tool,
            "runner": self.runner,
            "triggered_by": self.triggered_by,
        }
        result.update(self.custom)
        return {k: v for k, v in result.items() if v}


@dataclass
class TestSuite:
    name: str
    suite_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    tests: list[TestResult] = field(default_factory=list)
    environment: Optional[EnvironmentInfo] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_test(self, test: TestResult):
        if not test.suite_name:
            test.suite_name = self.name
        self.tests.append(test)

    def finish(self):
        self.end_time = datetime.now()

    @property
    def total(self) -> int:
        return len(self.tests)

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.FAILED)

    @property
    def skipped(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.SKIPPED)

    @property
    def broken(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.BROKEN)

    @property
    def blocked(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.BLOCKED)

    @property
    def warning_count(self) -> int:
        return sum(1 for t in self.tests if t.status == TestStatus.WARNING)

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0

    @property
    def duration_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return sum(t.duration_ms for t in self.tests)

    @property
    def platforms(self) -> list[str]:
        seen = set()
        result = []
        for t in self.tests:
            if t.platform:
                key = t.platform.display_name
                if key not in seen:
                    seen.add(key)
                    result.append(key)
        return result

    @property
    def categories(self) -> list[str]:
        return list({t.category for t in self.tests if t.category})

    @property
    def all_tags(self) -> list[str]:
        tags = set()
        for t in self.tests:
            tags.update(t.tags)
        return sorted(tags)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "suite_id": self.suite_id,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "broken": self.broken,
            "blocked": self.blocked,
            "warning": self.warning_count,
            "pass_rate": round(self.pass_rate, 2),
            "platforms": self.platforms,
            "categories": self.categories,
            "tags": self.all_tags,
            "environment": self.environment.to_dict() if self.environment else {},
            "tests": [t.to_dict() for t in self.tests],
            "metadata": self.metadata,
        }
