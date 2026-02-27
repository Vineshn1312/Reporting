"""
Example: Using Reportly with Appium for mobile test automation.

This demonstrates how to integrate Reportly into your Appium test suite
for both Android and iOS testing.
Run with: python -m reportly.examples.appium_example
"""

from appium import webdriver as appium_webdriver
from appium.options import UiAutomator2Options, XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy

from reportly import (
    EnvironmentInfo,
    Platform,
    PlatformType,
    ReportlyReporter,
    StepStatus,
    TestStatus,
)


def run_android_tests():
    reporter = ReportlyReporter(
        title="Mobile App Test Report",
        description="Cross-platform mobile automation tests",
        output_dir="./reports",
        open_browser=True,
    )

    env = EnvironmentInfo(
        name="QA",
        url="http://appium-server:4723",
        build_number="app-v2.1.0",
        branch="develop",
    )

    # ===== ANDROID SUITE =====
    suite = reporter.start_suite(
        name="Android - Login Module",
        description="Login tests on Android",
        environment=env,
    )

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Pixel 7"
    options.app = "/path/to/app.apk"
    options.automation_name = "UiAutomator2"

    driver = appium_webdriver.Remote("http://localhost:4723", options=options)

    try:
        platform = reporter.detect_platform(driver)

        # Test: App Launch
        test = reporter.start_test(
            name="App Launch and Splash Screen",
            category="Smoke",
            tags=["android", "launch", "p0"],
            priority="Critical",
            platform=platform,
        )

        reporter.log_step("Launch application", StepStatus.PASSED, duration_ms=2500)
        reporter.attach_screenshot(driver, "app_launched")

        reporter.log_step("Verify splash screen", StepStatus.PASSED, duration_ms=800)
        reporter.log_step("Wait for home screen", StepStatus.PASSED, duration_ms=3000)

        reporter.end_test(TestStatus.PASSED, driver=driver)

        # Test: Login Flow
        test = reporter.start_test(
            name="Login with Biometric Authentication",
            category="Authentication",
            tags=["android", "biometric", "login"],
            platform=platform,
        )

        reporter.log_step("Tap login button", StepStatus.PASSED, duration_ms=200)
        reporter.log_step("Enter email", StepStatus.PASSED, duration_ms=500)
        reporter.log_step(
            "Trigger biometric prompt",
            StepStatus.FAILED,
            error_message="BiometricPrompt not available on this device",
            duration_ms=100,
        )
        reporter.attach_screenshot(driver, "biometric_error")

        reporter.end_test(
            TestStatus.FAILED,
            error_message="BiometricPrompt not available on emulator",
            stack_trace="java.lang.SecurityException: ...",
            driver=driver,
        )

    finally:
        driver.quit()

    reporter.end_suite()

    # ===== iOS SUITE =====
    suite = reporter.start_suite(name="iOS - Login Module", description="Login tests on iOS")

    ios_options = XCUITestOptions()
    ios_options.platform_name = "iOS"
    ios_options.device_name = "iPhone 15 Pro"
    ios_options.app = "/path/to/app.ipa"

    ios_driver = appium_webdriver.Remote("http://localhost:4723", options=ios_options)

    try:
        ios_platform = reporter.detect_platform(ios_driver)

        test = reporter.start_test(
            name="App Launch on iOS",
            category="Smoke",
            tags=["ios", "launch"],
            platform=ios_platform,
        )

        reporter.log_step("Launch application", StepStatus.PASSED, duration_ms=1800)
        reporter.attach_screenshot(ios_driver, "ios_launched")
        reporter.end_test(TestStatus.PASSED, driver=ios_driver)

    finally:
        ios_driver.quit()

    reporter.end_suite()

    report_path = reporter.generate("appium_report.html")
    print(f"Report generated: {report_path}")


if __name__ == "__main__":
    run_android_tests()
