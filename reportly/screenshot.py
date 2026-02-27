"""Screenshot capture utilities for Selenium and Appium drivers."""

from __future__ import annotations

import base64
import io
import logging
from datetime import datetime
from typing import Any, Optional

from reportly.models import Attachment, AttachmentType

logger = logging.getLogger("reportly.screenshot")


class ScreenshotCapture:
    """Captures screenshots from Selenium WebDriver and Appium driver instances."""

    @staticmethod
    def capture(driver: Any, name: Optional[str] = None) -> Optional[Attachment]:
        if driver is None:
            logger.warning("Driver is None, cannot capture screenshot")
            return None

        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            b64_data = driver.get_screenshot_as_base64()
            return Attachment(
                name=name,
                attachment_type=AttachmentType.SCREENSHOT,
                data=b64_data,
                mime_type="image/png",
            )
        except Exception as e:
            logger.error("Failed to capture screenshot: %s", e)
            return None

    @staticmethod
    def capture_element(driver: Any, element: Any, name: Optional[str] = None) -> Optional[Attachment]:
        """Capture a screenshot of a specific element."""
        if driver is None or element is None:
            return None

        if name is None:
            name = f"element_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            b64_data = element.screenshot_as_base64
            return Attachment(
                name=name,
                attachment_type=AttachmentType.SCREENSHOT,
                data=b64_data,
                mime_type="image/png",
            )
        except Exception:
            return ScreenshotCapture.capture(driver, name)

    @staticmethod
    def capture_full_page(driver: Any, name: Optional[str] = None) -> Optional[Attachment]:
        """Capture full-page screenshot (Selenium 4+ / CDP-based)."""
        if driver is None:
            return None

        if name is None:
            name = f"fullpage_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        try:
            if hasattr(driver, "get_full_page_screenshot_as_base64"):
                b64_data = driver.get_full_page_screenshot_as_base64()
            else:
                original_size = driver.get_window_size()
                total_height = driver.execute_script("return document.body.scrollHeight")
                total_width = driver.execute_script("return document.body.scrollWidth")
                driver.set_window_size(total_width, total_height)
                b64_data = driver.get_screenshot_as_base64()
                driver.set_window_size(original_size["width"], original_size["height"])

            return Attachment(
                name=name,
                attachment_type=AttachmentType.SCREENSHOT,
                data=b64_data,
                mime_type="image/png",
            )
        except Exception as e:
            logger.error("Full page screenshot failed, falling back to viewport: %s", e)
            return ScreenshotCapture.capture(driver, name)

    @staticmethod
    def from_base64(b64_data: str, name: Optional[str] = None) -> Attachment:
        """Create an attachment from existing base64 data."""
        if name is None:
            name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        return Attachment(
            name=name,
            attachment_type=AttachmentType.SCREENSHOT,
            data=b64_data,
            mime_type="image/png",
        )

    @staticmethod
    def from_file(filepath: str, name: Optional[str] = None) -> Optional[Attachment]:
        """Create an attachment from an image file on disk."""
        if name is None:
            name = filepath.split("/")[-1].split("\\")[-1]
        try:
            with open(filepath, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            mime = "image/png"
            if filepath.lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            elif filepath.lower().endswith(".gif"):
                mime = "image/gif"
            elif filepath.lower().endswith(".webp"):
                mime = "image/webp"
            return Attachment(
                name=name,
                attachment_type=AttachmentType.SCREENSHOT,
                data=b64_data,
                mime_type=mime,
            )
        except Exception as e:
            logger.error("Failed to read screenshot from file: %s", e)
            return None

    @staticmethod
    def capture_appium_contexts(driver: Any) -> dict:
        """Capture screenshots from all available Appium contexts (NATIVE/WEBVIEW)."""
        results = {}
        try:
            contexts = driver.contexts
            current = driver.context
            for ctx in contexts:
                driver.switch_to.context(ctx)
                attachment = ScreenshotCapture.capture(driver, name=f"context_{ctx}")
                if attachment:
                    results[ctx] = attachment
            driver.switch_to.context(current)
        except Exception as e:
            logger.error("Failed multi-context capture: %s", e)
        return results
