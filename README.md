# Reportly

**Modern Multi-Platform Test Reporting for Selenium & Appium with AI-Powered Failure Analysis**

Reportly is a comprehensive, developer-friendly test reporting tool that generates stunning HTML reports for your Selenium and Appium test suites. It supports web, Android, and iOS platforms with built-in AI-powered failure analysis, screenshot capture, and a modern dark-themed UI.

---

## Features

### Core Reporting
- **Multi-Platform Support** — Selenium (Web), Appium (Android & iOS), Desktop, API
- **Beautiful HTML Reports** — Modern dark/light themed UI with glassmorphism design
- **Single-File Reports** — Self-contained HTML with embedded CSS/JS (no external dependencies)
- **JSON Export** — Raw report data exportable as JSON for CI/CD integration

### Dashboard & Visualization
- **Interactive Dashboard** — Real-time pass/fail/skip statistics at a glance
- **Donut Charts** — Visual distribution of test results
- **Pass Rate Ring** — Animated circular progress for pass percentage
- **Platform Breakdown Bars** — Stacked bars showing results per platform/browser
- **Failure Category Chart** — AI-detected failure type distribution

### Test Results
- **Filterable Test Table** — Search by name, error message, or tag
- **Multi-Filter Support** — Filter by status, platform, category, and suite simultaneously
- **Expandable Test Details** — Click any test to see steps, errors, screenshots, and AI analysis
- **Step-by-Step Logging** — Detailed test execution steps with individual status
- **Duration Tracking** — Per-test and per-step timing
- **Tags & Categories** — Organize tests with labels and categories
- **Priority Levels** — Mark test priority (Critical, High, Medium, Low)
- **Test Parameters** — Display parameterized test data
- **External Links** — Link to Jira tickets, test case management tools

### AI-Powered Failure Analysis
- **Automatic Analysis** — Failed tests are analyzed using OpenAI GPT models
- **Failure Categorization** — Element Not Found, Timeout, Assertion Failure, Network Error, App Crash, Authentication, Configuration Error, etc.
- **Root Cause Detection** — Clear explanation of why the test failed
- **Actionable Suggestions** — Concrete fix recommendations
- **Confidence Scoring** — AI confidence level for each analysis
- **Similar Failure Patterns** — Related failure signatures
- **Rule-Based Fallback** — Works without API key using keyword-based analysis
- **Dedicated AI Tab** — Summary cards and detailed analysis per failure

### Screenshot Management
- **Auto-Capture on Failure** — Screenshots automatically taken when tests fail
- **Manual Capture** — Attach screenshots at any point during execution
- **Step-Level Screenshots** — Attach screenshots to individual test steps
- **Full Page Screenshots** — Capture entire scrollable pages (Selenium 4+)
- **Element Screenshots** — Capture specific UI elements
- **Multi-Context Capture** — Appium NATIVE/WEBVIEW context screenshots
- **Screenshot Gallery** — Dedicated tab with grid view of all screenshots
- **Lightbox Viewer** — Click any screenshot for full-size overlay view
- **Base64 Embedded** — Screenshots embedded directly in HTML (no external files)
- **File Import** — Attach screenshots from disk files

### Platform & Environment
- **Auto Platform Detection** — Detect browser/device info from driver capabilities
- **Environment Info** — Display build number, branch, commit, CI tool, URL
- **Cross-Browser Results** — Compare pass rates across Chrome, Firefox, Safari, etc.
- **Cross-Device Results** — Compare Android vs iOS results
- **Dedicated Platforms Tab** — Per-platform pass rate cards and comparison bars

### Timeline & Execution Flow
- **Execution Timeline** — Chronological view of all test executions
- **Visual Status Markers** — Color-coded timeline with pass/fail indicators
- **Duration Display** — Time taken for each test in the timeline

### UI/UX
- **Dark/Light Theme Toggle** — Switch between dark and light mode
- **Responsive Design** — Works on desktop, tablet, and mobile screens
- **Sticky Header** — Navigation always accessible while scrolling
- **Print Support** — Clean print layout with `Ctrl+P`
- **Tab Navigation** — Dashboard, Results, AI Analysis, Screenshots, Timeline, Environment, Platforms
- **Animated Charts** — Smooth transitions and data visualization
- **Keyboard Shortcuts** — Escape to close lightbox

### Developer Experience
- **Simple API** — `start_suite → start_test → log_step → end_test → generate`
- **Context Managers** — Fluent method chaining
- **Retry Tracking** — Track test retry attempts and previous errors
- **Metadata Support** — Attach arbitrary key-value metadata to tests and suites
- **Extensible Models** — Dataclass-based models for easy customization

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Generate Demo Report

```bash
python generate_demo_report.py
```

This generates a sample report with realistic mock data showcasing all features.

### Basic Usage with Selenium

```python
from reportly import ReportlyReporter, StepStatus, TestStatus, Platform, PlatformType, EnvironmentInfo

reporter = ReportlyReporter(
    title="My Test Report",
    output_dir="./reports",
    ai_api_key="sk-...",  # Optional: enables AI analysis
)

# Start a test suite
suite = reporter.start_suite(
    name="Login Tests",
    environment=EnvironmentInfo(name="Staging", url="https://staging.example.com"),
)

# Start a test
test = reporter.start_test(
    name="User Login",
    category="Authentication",
    tags=["login", "smoke"],
    platform=reporter.detect_platform(driver),  # Auto-detect from driver
)

# Log steps
reporter.log_step("Navigate to login", StepStatus.PASSED)
reporter.log_step("Enter credentials", StepStatus.PASSED)
reporter.log_step("Click submit", StepStatus.PASSED)

# Capture screenshots
reporter.attach_screenshot(driver, "after_login")

# End test
reporter.end_test(TestStatus.PASSED, driver=driver)

# End suite and generate
reporter.end_suite()
report_path = reporter.generate("report.html")
```

### Basic Usage with Appium

```python
from reportly import ReportlyReporter, StepStatus, TestStatus

reporter = ReportlyReporter(title="Mobile Test Report")

suite = reporter.start_suite(name="Android Smoke Tests")

test = reporter.start_test(
    name="App Launch",
    category="Smoke",
    tags=["android", "launch"],
    platform=reporter.detect_platform(appium_driver),
)

reporter.log_step("Launch app", StepStatus.PASSED, duration_ms=2500)
reporter.log_step("Verify home screen", StepStatus.PASSED)
reporter.attach_screenshot(appium_driver, "home_screen")

reporter.end_test(TestStatus.PASSED, driver=appium_driver)
reporter.end_suite()
reporter.generate("mobile_report.html")
```

### Usage with Selenium (Java)

```java
import com.reportly.ReportlyReporter;
import com.reportly.models.*;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class SeleniumReportExample {

    public static void main(String[] args) {
        ReportlyReporter reporter = new ReportlyReporter.Builder()
            .title("Selenium Java Test Report")
            .outputDir("./reports")
            .aiApiKey("sk-...")  // Optional: enables AI analysis
            .build();

        // Start a test suite
        EnvironmentInfo env = new EnvironmentInfo.Builder()
            .name("Staging")
            .url("https://staging.example.com")
            .buildNumber("build-1234")
            .branch("main")
            .ciTool("Jenkins")
            .build();

        reporter.startSuite("Login Tests", "End-to-end login tests", env);

        WebDriver driver = new ChromeDriver();

        try {
            // Auto-detect platform from driver capabilities
            Platform platform = reporter.detectPlatform(driver);

            // Start a test
            reporter.startTest("User Login with Valid Credentials",
                TestConfig.builder()
                    .category("Authentication")
                    .tags(List.of("login", "smoke", "p0"))
                    .priority("Critical")
                    .platform(platform)
                    .parameter("username", "testuser@example.com")
                    .link("jira", "AUTH-1234")
                    .build()
            );

            // Log steps
            driver.get("https://staging.example.com/login");
            reporter.logStep("Navigate to login page", StepStatus.PASSED);

            driver.findElement(By.id("email")).sendKeys("testuser@example.com");
            reporter.logStep("Enter email address", StepStatus.PASSED);

            driver.findElement(By.id("password")).sendKeys("password123");
            reporter.logStep("Enter password", StepStatus.PASSED);

            // Capture screenshot before clicking login
            reporter.attachScreenshot(driver, "before_login");

            driver.findElement(By.id("login-btn")).click();
            reporter.logStep("Click login button", StepStatus.PASSED);

            new WebDriverWait(driver, Duration.ofSeconds(10))
                .until(ExpectedConditions.urlContains("/dashboard"));
            reporter.logStep("Verify dashboard loaded", StepStatus.PASSED);

            reporter.attachScreenshot(driver, "dashboard_loaded");

            // End test as passed
            reporter.endTest(TestStatus.PASSED, driver);

        } catch (Exception e) {
            // End test as failed — auto-captures screenshot on failure
            reporter.endTest(TestStatus.FAILED, driver, e.getMessage(), getStackTrace(e));
        } finally {
            driver.quit();
        }

        reporter.endSuite();
        String reportPath = reporter.generate("selenium_report.html");
        System.out.println("Report generated: " + reportPath);
    }
}
```

### Usage with Appium (Java)

```java
import com.reportly.ReportlyReporter;
import com.reportly.models.*;
import io.appium.java_client.android.AndroidDriver;
import io.appium.java_client.android.options.UiAutomator2Options;

public class AppiumReportExample {

    public static void main(String[] args) {
        ReportlyReporter reporter = new ReportlyReporter.Builder()
            .title("Mobile App Test Report")
            .outputDir("./reports")
            .build();

        // Android suite
        EnvironmentInfo env = new EnvironmentInfo.Builder()
            .name("QA")
            .url("http://appium-server:4723")
            .buildNumber("app-v2.1.0")
            .build();

        reporter.startSuite("Android - Login Module", "Login tests on Android", env);

        UiAutomator2Options options = new UiAutomator2Options()
            .setDeviceName("Pixel 7")
            .setApp("/path/to/app.apk");

        AndroidDriver driver = new AndroidDriver(
            new URL("http://localhost:4723"), options
        );

        try {
            Platform platform = reporter.detectPlatform(driver);

            // Test: App Launch
            reporter.startTest("Application Cold Start",
                TestConfig.builder()
                    .category("Smoke")
                    .tags(List.of("android", "launch", "p0"))
                    .priority("Critical")
                    .platform(platform)
                    .build()
            );

            reporter.logStep("Launch application", StepStatus.PASSED, 2500);
            reporter.attachScreenshot(driver, "app_launched");
            reporter.logStep("Verify home screen loaded", StepStatus.PASSED, 800);
            reporter.logStep("Verify bottom navigation visible", StepStatus.PASSED, 200);

            reporter.endTest(TestStatus.PASSED, driver);

            // Test: Login with biometric
            reporter.startTest("Login with Biometric Authentication",
                TestConfig.builder()
                    .category("Authentication")
                    .tags(List.of("android", "biometric", "login"))
                    .platform(platform)
                    .build()
            );

            reporter.logStep("Tap login button", StepStatus.PASSED, 200);
            reporter.logStep("Enter email", StepStatus.PASSED, 500);
            reporter.logStep("Trigger biometric prompt", StepStatus.FAILED, 100,
                "BiometricPrompt not available on emulator");

            reporter.attachScreenshot(driver, "biometric_error");
            reporter.endTest(TestStatus.FAILED, driver,
                "BiometricPrompt not available on emulator",
                "java.lang.SecurityException: ...");

        } finally {
            driver.quit();
        }

        reporter.endSuite();
        reporter.generate("appium_android_report.html");
    }
}
```

### Usage with Selenium (Kotlin)

```kotlin
import com.reportly.ReportlyReporter
import com.reportly.models.*
import org.openqa.selenium.By
import org.openqa.selenium.chrome.ChromeDriver
import org.openqa.selenium.support.ui.ExpectedConditions
import org.openqa.selenium.support.ui.WebDriverWait
import java.time.Duration

fun main() {
    val reporter = ReportlyReporter.Builder()
        .title("Selenium Kotlin Test Report")
        .outputDir("./reports")
        .aiApiKey("sk-...")
        .build()

    val env = EnvironmentInfo.Builder()
        .name("Staging")
        .url("https://staging.example.com")
        .buildNumber("build-5678")
        .branch("release/3.0")
        .ciTool("GitHub Actions")
        .build()

    reporter.startSuite("Web App - Chrome", "E2E tests on Chrome", env)

    val driver = ChromeDriver()

    try {
        val platform = reporter.detectPlatform(driver)

        // Test: Search feature
        reporter.startTest("Product Search and Filter",
            TestConfig.builder()
                .category("Search")
                .tags(listOf("search", "regression", "p1"))
                .priority("High")
                .platform(platform)
                .link("jira", "SRCH-456")
                .build()
        )

        driver.get("https://staging.example.com/products")
        reporter.logStep("Navigate to products page", StepStatus.PASSED)

        driver.findElement(By.id("search-input")).sendKeys("wireless headphones")
        reporter.logStep("Enter search query", StepStatus.PASSED)

        driver.findElement(By.cssSelector(".filter-price-range")).click()
        reporter.logStep("Apply price filter", StepStatus.PASSED)

        val results = driver.findElements(By.cssSelector(".product-card"))
        assert(results.isNotEmpty()) { "No search results found" }
        reporter.logStep("Verify results returned (${results.size} items)", StepStatus.PASSED)

        reporter.attachScreenshot(driver, "search_results")
        reporter.endTest(TestStatus.PASSED, driver)

        // Test: Checkout flow
        reporter.startTest("Complete Checkout Flow",
            TestConfig.builder()
                .category("Checkout")
                .tags(listOf("checkout", "e2e", "payment"))
                .priority("Critical")
                .platform(platform)
                .parameter("payment_method", "credit_card")
                .build()
        )

        reporter.logStep("Add item to cart", StepStatus.PASSED)
        reporter.logStep("Navigate to checkout", StepStatus.PASSED)
        reporter.logStep("Fill shipping address", StepStatus.PASSED)

        try {
            WebDriverWait(driver, Duration.ofSeconds(10))
                .until(ExpectedConditions.elementToBeClickable(By.id("place-order")))
            reporter.logStep("Click Place Order", StepStatus.PASSED)
            reporter.endTest(TestStatus.PASSED, driver)
        } catch (e: Exception) {
            reporter.logStep("Click Place Order", StepStatus.FAILED,
                errorMessage = e.message ?: "Unknown error")
            reporter.attachScreenshot(driver, "checkout_failure")
            reporter.endTest(TestStatus.FAILED, driver, e.message, e.stackTraceToString())
        }

    } finally {
        driver.quit()
    }

    reporter.endSuite()
    val reportPath = reporter.generate("kotlin_selenium_report.html")
    println("Report generated: $reportPath")
}
```

### Usage with Appium (Kotlin)

```kotlin
import com.reportly.ReportlyReporter
import com.reportly.models.*
import io.appium.java_client.ios.IOSDriver
import io.appium.java_client.ios.options.XCUITestOptions
import java.net.URL

fun main() {
    val reporter = ReportlyReporter.Builder()
        .title("iOS Mobile Test Report")
        .outputDir("./reports")
        .build()

    reporter.startSuite("iOS - Core Features",
        description = "Core feature tests on iPhone 15 Pro",
        environment = EnvironmentInfo.Builder()
            .name("QA")
            .url("http://appium-hub:4723")
            .buildNumber("app-v3.1.0-beta")
            .build()
    )

    val options = XCUITestOptions().apply {
        setDeviceName("iPhone 15 Pro")
        setApp("/path/to/MyApp.ipa")
        setPlatformVersion("17.2")
    }

    val driver = IOSDriver(URL("http://localhost:4723"), options)

    try {
        val platform = reporter.detectPlatform(driver)

        // Test: App launch
        reporter.startTest("Application Cold Start on iOS",
            TestConfig.builder()
                .category("Performance")
                .tags(listOf("ios", "launch", "performance"))
                .priority("Critical")
                .platform(platform)
                .build()
        )

        reporter.logStep("Install IPA on simulator", StepStatus.PASSED, durationMs = 6000)
        reporter.logStep("Launch application", StepStatus.PASSED, durationMs = 2200)
        reporter.logStep("Verify onboarding screen", StepStatus.PASSED, durationMs = 400)
        reporter.logStep("Skip onboarding", StepStatus.PASSED, durationMs = 300)

        reporter.attachScreenshot(driver, "ios_home_screen")
        reporter.logStep("Verify home screen loaded", StepStatus.PASSED, durationMs = 500)

        reporter.endTest(TestStatus.PASSED, driver)

        // Test: Face ID login
        reporter.startTest("Login with Face ID",
            TestConfig.builder()
                .category("Authentication")
                .tags(listOf("ios", "biometric", "faceid"))
                .priority("High")
                .platform(platform)
                .parameter("biometric_type", "Face ID")
                .build()
        )

        reporter.logStep("Navigate to login screen", StepStatus.PASSED)
        reporter.logStep("Tap 'Login with Face ID'", StepStatus.PASSED)

        reporter.logStep("Authenticate with Face ID", StepStatus.FAILED,
            errorMessage = "Face ID enrollment not found on simulator")

        reporter.attachScreenshot(driver, "faceid_error")
        reporter.endTest(TestStatus.FAILED, driver,
            errorMessage = "LAError.biometryNotEnrolled: Biometry is not enrolled.",
            stackTrace = "Error Domain=com.apple.LocalAuthentication Code=-7 ...")

        // Test: Deep link navigation
        reporter.startTest("Deep Link to Product Page",
            TestConfig.builder()
                .category("Navigation")
                .tags(listOf("ios", "deeplink"))
                .platform(platform)
                .build()
        )

        reporter.logStep("Open deep link: myapp://product/12345", StepStatus.PASSED)
        reporter.logStep("Verify product page loaded", StepStatus.PASSED)
        reporter.logStep("Verify product title matches", StepStatus.PASSED)

        reporter.endTest(TestStatus.PASSED, driver)

    } finally {
        driver.quit()
    }

    reporter.endSuite()
    val reportPath = reporter.generate("kotlin_ios_report.html")
    println("Report generated: $reportPath")
}
```

---

## AI Failure Analysis Setup

### With OpenAI

```python
reporter = ReportlyReporter(
    title="Report",
    ai_api_key="sk-your-openai-key",
    ai_model="gpt-4o-mini",  # or gpt-4o, gpt-3.5-turbo
)
```

### With Local LLM (Ollama, LM Studio, etc.)

```python
reporter = ReportlyReporter(
    title="Report",
    ai_api_key="not-needed",
    ai_model="llama3",
    ai_base_url="http://localhost:11434/v1",
)
```

### Without API Key

When no API key is provided, Reportly uses a rule-based fallback analyzer that detects common failure patterns (element not found, timeouts, assertion failures, etc.) from error messages and stack traces.

---

## JUnit 5 Integration (Java / Kotlin)

Reportly provides a **JUnit 5 Extension** for Java and Kotlin projects. The extension automatically collects test results, captures screenshots on failures, and outputs a JSON file that Reportly's engine turns into the HTML report.

### How It Works

```
┌───────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   JUnit 5 Tests   │──────>│  junit-results   │──────>│  HTML Report     │
│   (Java/Kotlin)   │       │  .json           │       │  (Reportly)      │
│  + Extension      │       │                  │       │                  │
└───────────────────┘       └──────────────────┘       └──────────────────┘
    ReportlyExtension           JSON output             python -m reportly
    collects results            (automatic)             (one command)
```

### Step 1: Add the Extension to Your Project

Copy the `ReportlyExtension.java` file from `integrations/junit5/` into your project, or add the integration module.

**Gradle (build.gradle):**

```groovy
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testImplementation 'com.google.code.gson:gson:2.10.1'
    testImplementation 'org.seleniumhq.selenium:selenium-java:4.18.1'
    // Copy ReportlyExtension.java into your src/test/java/com/reportly/junit5/
}
```

**Maven (pom.xml):**

```xml
<dependencies>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.2</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>2.10.1</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.seleniumhq.selenium</groupId>
        <artifactId>selenium-java</artifactId>
        <version>4.18.1</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### Step 2: Annotate Your Test Classes

**Java:**

```java
import com.reportly.junit5.ReportlyExtension;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

@ExtendWith(ReportlyExtension.class)
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class LoginTests {

    private WebDriver driver;

    @BeforeEach
    void setUp(TestInfo testInfo) {
        driver = new ChromeDriver();

        // Set platform info for reports
        ReportlyExtension.setPlatform(testInfo,
            Map.of("platform_type", "web",
                   "browser_name", "Chrome",
                   "os_name", System.getProperty("os.name")));

        ReportlyExtension.setCategory(testInfo, "Authentication");
        ReportlyExtension.setPriority(testInfo, "Critical");
        ReportlyExtension.addLink(testInfo, "jira", "AUTH-1234");
    }

    @AfterEach
    void tearDown() {
        if (driver != null) driver.quit();
    }

    @Test
    @Order(1)
    @Tag("smoke")
    @Tag("login")
    @DisplayName("Login with valid credentials")
    void testValidLogin(TestInfo testInfo) {
        driver.get("https://example.com/login");
        ReportlyExtension.logStep(testInfo, "Navigate to login page", "passed");

        // ... perform login ...
        ReportlyExtension.logStep(testInfo, "Enter credentials", "passed");
        ReportlyExtension.logStep(testInfo, "Click submit", "passed");

        ReportlyExtension.attachScreenshot(testInfo, driver, "after_login");

        ReportlyExtension.logStep(testInfo, "Verify dashboard loaded", "passed");
    }

    @Test
    @Order(2)
    @Tag("login")
    @Tag("negative")
    @DisplayName("Login with invalid password shows error")
    void testInvalidPassword(TestInfo testInfo) {
        driver.get("https://example.com/login");
        ReportlyExtension.logStep(testInfo, "Navigate to login page", "passed");
        ReportlyExtension.logStep(testInfo, "Enter invalid credentials", "passed");
        ReportlyExtension.logStep(testInfo, "Click submit", "passed");

        // If this assertion fails, screenshot is auto-captured
        Assertions.assertTrue(
            driver.getPageSource().contains("Invalid credentials"),
            "Error message should be displayed"
        );
    }
}
```

**Kotlin:**

```kotlin
import com.reportly.junit5.ReportlyExtension
import org.junit.jupiter.api.*
import org.junit.jupiter.api.extension.ExtendWith
import org.openqa.selenium.WebDriver
import org.openqa.selenium.chrome.ChromeDriver

@ExtendWith(ReportlyExtension::class)
@TestMethodOrder(MethodOrderer.OrderAnnotation::class)
class LoginTests {

    private lateinit var driver: WebDriver

    @BeforeEach
    fun setUp(testInfo: TestInfo) {
        driver = ChromeDriver()
        ReportlyExtension.setCategory(testInfo, "Authentication")
        ReportlyExtension.setPlatform(testInfo, mapOf(
            "platform_type" to "web",
            "browser_name" to "Chrome",
            "os_name" to System.getProperty("os.name")
        ))
    }

    @AfterEach
    fun tearDown() {
        driver.quit()
    }

    @Test
    @Order(1)
    @Tag("smoke")
    @DisplayName("Login with valid credentials")
    fun testValidLogin(testInfo: TestInfo) {
        driver.get("https://example.com/login")
        ReportlyExtension.logStep(testInfo, "Navigate to login page", "passed")

        // ... perform login ...
        ReportlyExtension.logStep(testInfo, "Enter credentials", "passed")
        ReportlyExtension.attachScreenshot(testInfo, driver, "login_form")
        ReportlyExtension.logStep(testInfo, "Click submit", "passed")
        ReportlyExtension.logStep(testInfo, "Verify dashboard loaded", "passed")
    }
}
```

### Step 3: Configure via System Properties

Pass these when running tests (Gradle example):

```groovy
test {
    useJUnitPlatform()

    systemProperty 'reportly.title', 'My Selenium Test Report'
    systemProperty 'reportly.description', 'Automated regression tests'
    systemProperty 'reportly.output.dir', './reports'
    systemProperty 'reportly.output.file', 'junit-results.json'
    systemProperty 'reportly.env.name', 'Staging'
    systemProperty 'reportly.env.url', 'https://staging.example.com'
    systemProperty 'reportly.env.build', System.getenv('BUILD_NUMBER') ?: 'local'
    systemProperty 'reportly.env.branch', System.getenv('GIT_BRANCH') ?: 'main'
    systemProperty 'reportly.env.ci', 'GitHub Actions'
    systemProperty 'reportly.auto.screenshot', 'true'
    systemProperty 'reportly.auto.generate', 'false'  // set true to auto-run python
}
```

Maven equivalent:

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <systemPropertyVariables>
            <reportly.title>My Selenium Test Report</reportly.title>
            <reportly.output.dir>./reports</reportly.output.dir>
            <reportly.env.name>Staging</reportly.env.name>
            <reportly.auto.screenshot>true</reportly.auto.screenshot>
        </systemPropertyVariables>
    </configuration>
</plugin>
```

### Step 4: Generate the HTML Report

After tests run, the extension writes `reports/junit-results.json`. Generate the report with:

```bash
python -m reportly --input reports/junit-results.json --title "My Report" --open
```

Or with AI analysis:

```bash
python -m reportly \
    --input reports/junit-results.json \
    --title "Regression Report" \
    --ai-key sk-your-openai-key \
    --open
```

### Full CI Pipeline Example (Gradle + GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Reportly
        run: pip install Jinja2 Pillow python-dateutil

      - name: Run tests
        run: ./gradlew test

      - name: Generate report
        if: always()
        run: |
          python -m reportly \
            --input reports/junit-results.json \
            --output-dir reports \
            --title "CI Test Report - Build ${{ github.run_number }}" \
            --ai-key ${{ secrets.OPENAI_API_KEY }}

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: reports/report.html
```

### CLI Reference

```
python -m reportly [options]

Required:
  -i, --input           Path to JSON results file

Optional:
  -o, --output-dir      Output directory (default: ./reports)
  -f, --filename        Output filename (default: report.html)
  -t, --title           Report title
  -d, --description     Report description
  --theme               dark | light (default: dark)
  --ai-key              OpenAI API key for AI failure analysis
  --ai-model            AI model name (default: gpt-4o-mini)
  --ai-base-url         Custom AI API base URL (e.g. Ollama)
  --open                Open report in browser after generation
```

---

## Project Structure

```
Reporting/
├── README.md
├── requirements.txt
├── setup.py
├── generate_demo_report.py              # Run to see demo report
├── reportly/
│   ├── __init__.py                       # Package exports
│   ├── models.py                         # Data models (TestResult, TestSuite, etc.)
│   ├── reporter.py                       # Core reporter class (Python API)
│   ├── cli.py                            # CLI for JSON → HTML report generation
│   ├── __main__.py                       # python -m reportly entry point
│   ├── screenshot.py                     # Screenshot capture utilities
│   ├── ai_analyzer.py                    # AI failure analysis engine
│   ├── templates/
│   │   └── report_template.html          # HTML report template
│   └── examples/
│       ├── selenium_example.py           # Selenium integration example
│       └── appium_example.py             # Appium integration example
├── integrations/
│   └── junit5/                           # JUnit 5 Extension for Java/Kotlin
│       ├── build.gradle
│       └── src/main/java/com/reportly/junit5/
│           └── ReportlyExtension.java    # Drop this into your Java project
└── reports/                              # Generated reports (auto-created)
```

---

## Report Tabs

| Tab | Description |
|-----|-------------|
| **Dashboard** | Summary stats, donut chart, pass rate ring, platform bars, failure categories |
| **Test Results** | Filterable/searchable table with expandable details, steps, errors, screenshots |
| **AI Analysis** | Failure category summary cards + detailed root cause analysis per failed test |
| **Screenshots** | Grid gallery of all captured screenshots with lightbox viewer |
| **Timeline** | Chronological execution flow with status markers |
| **Environment** | Build info, branch, CI tool, URLs, custom environment data |
| **Platforms** | Per-platform pass rate cards and comparison charts |
