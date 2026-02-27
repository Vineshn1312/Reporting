"""
Reportly - Modern Multi-Platform Test Reporting for Selenium & Appium
"""

__version__ = "1.0.0"

from reportly.models import (
    TestStep,
    TestResult,
    TestSuite,
    Platform,
    StepStatus,
    TestStatus,
    Attachment,
)
from reportly.reporter import ReportlyReporter
from reportly.screenshot import ScreenshotCapture
from reportly.ai_analyzer import AIFailureAnalyzer

__all__ = [
    "TestStep",
    "TestResult",
    "TestSuite",
    "Platform",
    "StepStatus",
    "TestStatus",
    "Attachment",
    "ReportlyReporter",
    "ScreenshotCapture",
    "AIFailureAnalyzer",
]
