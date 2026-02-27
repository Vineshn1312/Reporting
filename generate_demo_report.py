"""
Generate a demo report with realistic mock data to showcase all Reportly features.
No Selenium/Appium drivers required — run this to see the report immediately.

Usage: python generate_demo_report.py
"""

import base64
import io
import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from reportly.models import (
    AIAnalysis,
    Attachment,
    AttachmentType,
    EnvironmentInfo,
    Platform,
    PlatformType,
    RetryInfo,
    StepStatus,
    TestResult,
    TestStatus,
    TestStep,
    TestSuite,
)
from reportly.reporter import ReportlyReporter


def generate_placeholder_screenshot(width=400, height=260, label="Screenshot", color=(40, 50, 80)):
    """Generate a simple placeholder PNG image."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((width - tw) / 2, (height - th) / 2), label, fill=(200, 200, 220), font=font)
        draw.rectangle([10, 10, width - 10, height - 10], outline=(70, 80, 120), width=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except ImportError:
        return _minimal_png_b64()


def _minimal_png_b64():
    """Tiny 1x1 red PNG as absolute fallback."""
    import struct, zlib
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b"\x00\xff\x00\x00")
    idat = chunk(b"IDAT", raw)
    iend = chunk(b"IEND", b"")
    return base64.b64encode(sig + ihdr + idat + iend).decode()


def main():
    reporter = ReportlyReporter(
        title="Reportly Demo - Multi-Platform Test Report",
        description="Comprehensive test execution report showcasing Selenium, Appium (Android & iOS) results with AI analysis",
        output_dir="./reports",
        open_browser=True,
        theme="dark",
    )

    base_time = datetime.now() - timedelta(minutes=15)

    # ===== SUITE 1: Web Tests (Selenium) =====
    env_web = EnvironmentInfo(
        name="Staging",
        url="https://staging.myapp.com",
        build_number="build-4521",
        build_url="https://ci.example.com/builds/4521",
        branch="release/2.5.0",
        commit_hash="a3f8c2d",
        ci_tool="GitHub Actions",
        runner="ubuntu-latest",
        triggered_by="merge to release branch",
    )

    suite_web = reporter.start_suite(
        name="Web Application - Chrome",
        description="End-to-end browser tests on Chrome",
        environment=env_web,
    )

    chrome_platform = Platform(
        platform_type=PlatformType.WEB,
        os_name="macOS",
        os_version="14.2",
        browser_name="Chrome",
        browser_version="121.0",
        screen_resolution="1920x1080",
    )

    firefox_platform = Platform(
        platform_type=PlatformType.WEB,
        os_name="Windows",
        os_version="11",
        browser_name="Firefox",
        browser_version="122.0",
        screen_resolution="1920x1080",
    )

    # Test 1: Login Success
    t = reporter.start_test(
        name="User Login with Valid Credentials",
        category="Authentication",
        tags=["login", "smoke", "p0", "regression"],
        priority="Critical",
        platform=chrome_platform,
        parameters={"username": "testuser@example.com", "env": "staging"},
        links={"jira": "AUTH-1234", "testcase": "TC-001"},
    )
    t.start_time = base_time

    reporter.log_step("Navigate to login page", StepStatus.PASSED, duration_ms=450, description="GET https://staging.myapp.com/login")
    reporter.log_step("Verify login form visible", StepStatus.PASSED, duration_ms=120)
    reporter.log_step("Enter email address", StepStatus.PASSED, duration_ms=200)
    reporter.log_step("Enter password", StepStatus.PASSED, duration_ms=180)
    step = reporter.log_step("Click Sign In button", StepStatus.PASSED, duration_ms=50)
    reporter.log_step("Wait for dashboard redirect", StepStatus.PASSED, duration_ms=1200, description="Waited for URL to contain /dashboard")
    reporter.log_step("Verify welcome message displayed", StepStatus.PASSED, duration_ms=80)

    screenshot_data = generate_placeholder_screenshot(400, 260, "Dashboard - Login Success", (25, 60, 40))
    reporter.attach_screenshot_base64(screenshot_data, "dashboard_after_login")

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=3.2)
    t.duration_ms = 3200
    reporter._current_test = None

    # Test 2: Search Products
    t = reporter.start_test(
        name="Product Search and Filter",
        category="Search",
        tags=["search", "regression"],
        priority="High",
        platform=chrome_platform,
        links={"jira": "SRCH-456"},
    )
    t.start_time = base_time + timedelta(seconds=4)

    reporter.log_step("Navigate to products page", StepStatus.PASSED, duration_ms=600)
    reporter.log_step("Enter search query 'wireless headphones'", StepStatus.PASSED, duration_ms=300)
    reporter.log_step("Apply price filter $50-$200", StepStatus.PASSED, duration_ms=200)
    reporter.log_step("Verify search results count > 0", StepStatus.PASSED, duration_ms=150)
    reporter.log_step("Verify filter badge displayed", StepStatus.PASSED, duration_ms=100)

    screenshot_data = generate_placeholder_screenshot(400, 260, "Search Results Page", (30, 45, 70))
    reporter.attach_screenshot_base64(screenshot_data, "search_results")

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=6)
    t.duration_ms = 2000
    reporter._current_test = None

    # Test 3: Checkout Flow - FAILED
    t = reporter.start_test(
        name="Complete Checkout with Credit Card",
        category="Checkout",
        tags=["checkout", "payment", "p0", "e2e"],
        priority="Critical",
        platform=chrome_platform,
        parameters={"payment_method": "credit_card", "card_type": "Visa"},
        links={"jira": "CHK-789"},
    )
    t.start_time = base_time + timedelta(seconds=7)

    reporter.log_step("Add item to cart", StepStatus.PASSED, duration_ms=800)
    reporter.log_step("Navigate to checkout", StepStatus.PASSED, duration_ms=500)
    reporter.log_step("Fill shipping address", StepStatus.PASSED, duration_ms=1200)
    reporter.log_step("Select shipping method", StepStatus.PASSED, duration_ms=300)
    reporter.log_step("Enter credit card details", StepStatus.PASSED, duration_ms=900)
    reporter.log_step(
        "Click Place Order button",
        StepStatus.FAILED,
        duration_ms=15000,
        error_message="TimeoutException: Element '#order-confirm-btn' not clickable after 15s",
    )

    screenshot_data = generate_placeholder_screenshot(400, 260, "Checkout - Timeout Error", (80, 30, 30))
    reporter.attach_screenshot_base64(screenshot_data, "checkout_failure")

    t.finish(
        TestStatus.FAILED,
        error_message="TimeoutException: Element '#order-confirm-btn' not clickable within 15 seconds. The button may be obscured by an overlay or not yet enabled.",
        stack_trace="""Traceback (most recent call last):
  File "tests/test_checkout.py", line 89, in test_complete_checkout
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#order-confirm-btn')))
  File "selenium/webdriver/support/wait.py", line 95, in until
    raise TimeoutException(message, screen, stacktrace)
selenium.common.exceptions.TimeoutException: Message: Element '#order-confirm-btn' not clickable after 15 seconds
Stacktrace:
    at Object.throwDecodedError (node:internal/deps/undici/undici:12618:13)
    at processResponse (node:internal/deps/undici/undici:10090:41)""",
    )
    t.ai_analysis = AIAnalysis(
        failure_category="Timeout",
        root_cause="The 'Place Order' button was not clickable within the 15-second timeout. This likely indicates the button is either obscured by a loading overlay, disabled due to incomplete form validation, or a JavaScript error prevented the button from becoming interactive.",
        suggestion="1. Check if a loading spinner/overlay is covering the button after entering card details. 2. Verify the payment processor callback completes successfully. 3. Add an explicit wait for any loading overlay to disappear before clicking. 4. Check browser console for JavaScript errors.",
        confidence=0.87,
        similar_failures=["Payment gateway timeout on staging environment", "Loading overlay blocking checkout actions", "Button disabled state not clearing after form validation"],
    )
    t.end_time = base_time + timedelta(seconds=25)
    t.duration_ms = 18700
    reporter._current_test = None

    # Test 4: Firefox - Registration
    t = reporter.start_test(
        name="New User Registration Flow",
        category="Authentication",
        tags=["registration", "cross-browser", "regression"],
        priority="High",
        platform=firefox_platform,
        links={"jira": "AUTH-567"},
    )
    t.start_time = base_time + timedelta(seconds=26)

    reporter.log_step("Navigate to registration page", StepStatus.PASSED, duration_ms=500)
    reporter.log_step("Fill registration form", StepStatus.PASSED, duration_ms=1500)
    reporter.log_step("Accept terms and conditions", StepStatus.PASSED, duration_ms=100)
    reporter.log_step("Click Register button", StepStatus.PASSED, duration_ms=300)
    reporter.log_step("Verify confirmation email sent", StepStatus.PASSED, duration_ms=2000)

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=31)
    t.duration_ms = 4400
    reporter._current_test = None

    # Test 5: Skipped test
    t = reporter.start_test(
        name="Social Login with Google OAuth",
        category="Authentication",
        tags=["oauth", "google", "skipped"],
        priority="Medium",
        platform=chrome_platform,
    )
    t.start_time = base_time + timedelta(seconds=32)
    reporter.log_step("Skip: Google OAuth not configured in staging", StepStatus.SKIPPED)
    t.finish(TestStatus.SKIPPED)
    t.end_time = base_time + timedelta(seconds=32, milliseconds=50)
    t.duration_ms = 50
    reporter._current_test = None

    reporter.end_suite()

    # ===== SUITE 2: Android Tests (Appium) =====
    env_android = EnvironmentInfo(
        name="QA",
        url="http://appium-hub:4723",
        build_number="app-v3.1.0-beta",
        branch="develop",
        ci_tool="Jenkins",
        custom={"appium_version": "2.4.1", "java_version": "17"},
    )

    suite_android = reporter.start_suite(
        name="Android - Core Features",
        description="Core feature tests on Android Pixel 7",
        environment=env_android,
    )

    android_platform = Platform(
        platform_type=PlatformType.ANDROID,
        os_name="Android",
        os_version="14",
        device_name="Pixel 7",
        device_udid="emulator-5554",
        app_name="com.myapp.staging",
        app_version="3.1.0-beta",
        automation_name="UiAutomator2",
        screen_resolution="1080x2400",
    )

    # Android Test 1: App Launch
    t = reporter.start_test(
        name="Application Cold Start",
        category="Performance",
        tags=["android", "launch", "performance", "p0"],
        priority="Critical",
        platform=android_platform,
    )
    t.start_time = base_time + timedelta(seconds=35)

    reporter.log_step("Install APK on device", StepStatus.PASSED, duration_ms=4500)
    reporter.log_step("Launch application", StepStatus.PASSED, duration_ms=2800, description="Cold start time measured")
    reporter.log_step("Verify splash screen displayed", StepStatus.PASSED, duration_ms=500)
    reporter.log_step("Wait for home screen", StepStatus.PASSED, duration_ms=1200)
    reporter.log_step("Verify bottom navigation visible", StepStatus.PASSED, duration_ms=200)

    screenshot_data = generate_placeholder_screenshot(280, 500, "Android Home Screen", (20, 35, 55))
    reporter.attach_screenshot_base64(screenshot_data, "android_home_screen")

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=44)
    t.duration_ms = 9200
    reporter._current_test = None

    # Android Test 2: Push Notification - BROKEN
    t = reporter.start_test(
        name="Push Notification Handling",
        category="Notifications",
        tags=["android", "push", "notification"],
        priority="High",
        platform=android_platform,
    )
    t.start_time = base_time + timedelta(seconds=45)

    reporter.log_step("Grant notification permission", StepStatus.PASSED, duration_ms=300)
    reporter.log_step("Trigger test notification via API", StepStatus.PASSED, duration_ms=800)
    reporter.log_step(
        "Wait for notification in shade",
        StepStatus.FAILED,
        duration_ms=10000,
        error_message="NoSuchElementException: Notification element not found in notification shade",
    )

    screenshot_data = generate_placeholder_screenshot(280, 500, "Notification Shade - Empty", (60, 25, 25))
    reporter.attach_screenshot_base64(screenshot_data, "notification_shade_empty")

    t.finish(
        TestStatus.BROKEN,
        error_message="NoSuchElementException: Unable to locate notification element in shade. The push notification may not have been delivered to the emulator.",
        stack_trace="""Traceback (most recent call last):
  File "tests/test_notifications.py", line 45, in test_push_notification
    notification = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Test Notification"]')
selenium.common.exceptions.NoSuchElementException: Message: An element could not be located using the given search parameters.""",
    )
    t.ai_analysis = AIAnalysis(
        failure_category="Element Not Found",
        root_cause="Push notification was not delivered to the Android emulator. Emulators often have issues with Google Cloud Messaging/Firebase Cloud Messaging. The notification element could not be found because it never appeared.",
        suggestion="1. Verify Firebase/GCM is properly configured for the emulator. 2. Use a real device for push notification tests. 3. Consider using Android's NotificationListenerService to verify delivery. 4. Add a retry mechanism with longer wait time.",
        confidence=0.82,
        similar_failures=["FCM delivery failure on emulators", "Notification permission not granted", "Test notification service timeout"],
    )
    t.end_time = base_time + timedelta(seconds=56)
    t.duration_ms = 11100
    reporter._current_test = None

    # Android Test 3: Profile Update
    t = reporter.start_test(
        name="Update User Profile Photo",
        category="Profile",
        tags=["android", "profile", "upload"],
        priority="Medium",
        platform=android_platform,
    )
    t.start_time = base_time + timedelta(seconds=57)

    reporter.log_step("Navigate to profile screen", StepStatus.PASSED, duration_ms=600)
    reporter.log_step("Tap edit profile button", StepStatus.PASSED, duration_ms=200)
    reporter.log_step("Tap change photo", StepStatus.PASSED, duration_ms=150)
    reporter.log_step("Select photo from gallery", StepStatus.PASSED, duration_ms=1200)
    reporter.log_step("Crop and confirm", StepStatus.PASSED, duration_ms=800)
    reporter.log_step("Verify photo updated", StepStatus.PASSED, duration_ms=2000)

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=62)
    t.duration_ms = 4950
    reporter._current_test = None

    reporter.end_suite()

    # ===== SUITE 3: iOS Tests (Appium) =====
    suite_ios = reporter.start_suite(
        name="iOS - Core Features",
        description="Core feature tests on iPhone 15 Pro",
        environment=EnvironmentInfo(
            name="QA",
            url="http://appium-hub:4723",
            build_number="app-v3.1.0-beta",
            branch="develop",
            custom={"xcode_version": "15.2", "appium_version": "2.4.1"},
        ),
    )

    ios_platform = Platform(
        platform_type=PlatformType.IOS,
        os_name="iOS",
        os_version="17.2",
        device_name="iPhone 15 Pro",
        device_udid="00008110-XXXX",
        app_name="com.myapp.staging",
        app_version="3.1.0-beta",
        automation_name="XCUITest",
    )

    # iOS Test 1: App Launch
    t = reporter.start_test(
        name="Application Cold Start",
        category="Performance",
        tags=["ios", "launch", "performance"],
        priority="Critical",
        platform=ios_platform,
    )
    t.start_time = base_time + timedelta(seconds=65)

    reporter.log_step("Install IPA on simulator", StepStatus.PASSED, duration_ms=6000)
    reporter.log_step("Launch application", StepStatus.PASSED, duration_ms=2200)
    reporter.log_step("Verify onboarding screen", StepStatus.PASSED, duration_ms=400)
    reporter.log_step("Skip onboarding", StepStatus.PASSED, duration_ms=300)
    reporter.log_step("Verify home screen loaded", StepStatus.PASSED, duration_ms=500)

    screenshot_data = generate_placeholder_screenshot(280, 500, "iOS Home Screen", (15, 40, 60))
    reporter.attach_screenshot_base64(screenshot_data, "ios_home_screen")

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=75)
    t.duration_ms = 9400
    reporter._current_test = None

    # iOS Test 2: Face ID Login - FAILED
    t = reporter.start_test(
        name="Login with Face ID",
        category="Authentication",
        tags=["ios", "biometric", "faceid"],
        priority="High",
        platform=ios_platform,
        parameters={"biometric_type": "Face ID"},
    )
    t.start_time = base_time + timedelta(seconds=76)

    reporter.log_step("Navigate to login screen", StepStatus.PASSED, duration_ms=400)
    reporter.log_step("Tap 'Login with Face ID'", StepStatus.PASSED, duration_ms=200)
    reporter.log_step(
        "Authenticate with Face ID",
        StepStatus.FAILED,
        duration_ms=5000,
        error_message="Face ID enrollment not found on simulator",
    )

    screenshot_data = generate_placeholder_screenshot(280, 500, "Face ID Error", (70, 20, 20))
    reporter.attach_screenshot_base64(screenshot_data, "faceid_error")

    t.finish(
        TestStatus.FAILED,
        error_message="Face ID authentication failed: No enrolled biometrics found on simulator. LAError.biometryNotEnrolled",
        stack_trace="""Error Domain=com.apple.LocalAuthentication Code=-7
  "Biometry is not enrolled." UserInfo={NSLocalizedDescription=Biometry is not enrolled.}
  at BiometricManager.authenticate() (BiometricManager.swift:45)
  at LoginViewController.handleBiometricLogin() (LoginViewController.swift:102)""",
    )
    t.ai_analysis = AIAnalysis(
        failure_category="Configuration Error",
        root_cause="Face ID is not enrolled on the iOS simulator. Biometric authentication requires explicit enrollment setup on simulators before tests can use it.",
        suggestion="1. Enroll Face ID on simulator: Features > Face ID > Enrolled. 2. Use Appium's mobile:enrollBiometric command before the test. 3. Add a setup step that checks for biometric availability and skips gracefully.",
        confidence=0.92,
        similar_failures=["Biometric not available on simulator", "Touch ID enrollment missing", "LAError.biometryNotEnrolled on test devices"],
    )
    t.end_time = base_time + timedelta(seconds=82)
    t.duration_ms = 5600
    reporter._current_test = None

    # iOS Test 3: Deep Link Navigation
    t = reporter.start_test(
        name="Deep Link to Product Page",
        category="Navigation",
        tags=["ios", "deeplink", "navigation"],
        priority="Medium",
        platform=ios_platform,
    )
    t.start_time = base_time + timedelta(seconds=83)

    reporter.log_step("Open deep link: myapp://product/12345", StepStatus.PASSED, duration_ms=1500)
    reporter.log_step("Verify product page loaded", StepStatus.PASSED, duration_ms=800)
    reporter.log_step("Verify product title matches", StepStatus.PASSED, duration_ms=100)
    reporter.log_step("Verify Add to Cart button visible", StepStatus.PASSED, duration_ms=80)

    t.finish(TestStatus.PASSED)
    t.end_time = base_time + timedelta(seconds=86)
    t.duration_ms = 2480
    reporter._current_test = None

    # iOS Test 4: Blocked test
    t = reporter.start_test(
        name="Apple Pay Checkout",
        category="Checkout",
        tags=["ios", "applepay", "blocked"],
        priority="High",
        platform=ios_platform,
    )
    t.start_time = base_time + timedelta(seconds=87)
    reporter.log_step("Apple Pay not available in test environment", StepStatus.WARNING)
    t.finish(TestStatus.BLOCKED)
    t.end_time = base_time + timedelta(seconds=87, milliseconds=100)
    t.duration_ms = 100
    reporter._current_test = None

    reporter.end_suite()

    # Generate report
    report_path = reporter.generate("demo_report.html")
    json_path = reporter.generate_json("demo_report.json")

    print(f"\n{'='*60}")
    print(f"  Reportly Demo Report Generated!")
    print(f"{'='*60}")
    print(f"  HTML Report: {report_path}")
    print(f"  JSON Export: {json_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
