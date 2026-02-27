"""
Example: Using Reportly with Selenium WebDriver tests.

This demonstrates how to integrate Reportly into your Selenium test suite.
Run with: python -m reportly.examples.selenium_example
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from reportly import (
    EnvironmentInfo,
    Platform,
    PlatformType,
    ReportlyReporter,
    StepStatus,
    TestStatus,
)


def run_selenium_tests():
    reporter = ReportlyReporter(
        title="Selenium Web Test Report",
        description="Automated browser tests for the web application",
        output_dir="./reports",
        # ai_api_key="sk-...",  # Set your OpenAI key for AI analysis
        open_browser=True,
    )

    env = EnvironmentInfo(
        name="Staging",
        url="https://staging.example.com",
        build_number="build-1234",
        branch="main",
        ci_tool="GitHub Actions",
    )

    suite = reporter.start_suite(
        name="Login Tests",
        description="End-to-end login flow tests",
        environment=env,
    )

    driver = webdriver.Chrome()

    try:
        # ----- Test 1: Successful Login -----
        platform = reporter.detect_platform(driver)
        test = reporter.start_test(
            name="Successful Login with Valid Credentials",
            category="Authentication",
            tags=["login", "smoke", "p0"],
            priority="High",
            platform=platform,
        )

        reporter.log_step("Navigate to login page", StepStatus.PASSED)
        driver.get("https://example.com/login")

        reporter.log_step("Enter username", StepStatus.PASSED)
        driver.find_element(By.ID, "username").send_keys("testuser")

        reporter.log_step("Enter password", StepStatus.PASSED)
        driver.find_element(By.ID, "password").send_keys("password123")

        reporter.attach_screenshot(driver, "before_login_click")

        reporter.log_step("Click login button", StepStatus.PASSED)
        driver.find_element(By.ID, "login-btn").click()

        WebDriverWait(driver, 10).until(EC.url_contains("/dashboard"))
        reporter.log_step("Verify dashboard loaded", StepStatus.PASSED)

        reporter.attach_screenshot(driver, "dashboard_loaded")

        reporter.end_test(TestStatus.PASSED, driver=driver)

        # ----- Test 2: Failed Login -----
        test = reporter.start_test(
            name="Login with Invalid Password",
            category="Authentication",
            tags=["login", "negative"],
            platform=platform,
        )

        reporter.log_step("Navigate to login page", StepStatus.PASSED)
        driver.get("https://example.com/login")

        reporter.log_step("Enter credentials", StepStatus.PASSED)
        reporter.log_step("Click login", StepStatus.PASSED)

        reporter.log_step(
            "Verify error message displayed",
            StepStatus.FAILED,
            error_message="Expected error message not found",
        )

        reporter.end_test(
            TestStatus.FAILED,
            error_message="AssertionError: Expected 'Invalid credentials' message not displayed",
            stack_trace="Traceback ...",
            driver=driver,  # auto-captures failure screenshot
        )

    finally:
        driver.quit()

    reporter.end_suite()
    report_path = reporter.generate("selenium_report.html")
    print(f"Report generated: {report_path}")


if __name__ == "__main__":
    run_selenium_tests()
