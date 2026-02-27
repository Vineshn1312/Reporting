package com.reportly.junit5;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.junit.jupiter.api.extension.*;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;

import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * JUnit 5 Extension that collects test results into Reportly-compatible JSON.
 *
 * <h3>Usage:</h3>
 * <pre>{@code
 * @ExtendWith(ReportlyExtension.class)
 * public class MyTests {
 *     // tests ...
 * }
 * }</pre>
 *
 * Or register globally via ServiceLoader / suite configuration.
 *
 * <h3>Configuration (system properties):</h3>
 * <ul>
 *   <li>{@code reportly.output.dir} — output directory (default: ./reports)</li>
 *   <li>{@code reportly.output.file} — JSON filename (default: junit-results.json)</li>
 *   <li>{@code reportly.title} — report title</li>
 *   <li>{@code reportly.description} — report description</li>
 *   <li>{@code reportly.env.name} — environment name (e.g. Staging)</li>
 *   <li>{@code reportly.env.url} — environment URL</li>
 *   <li>{@code reportly.env.build} — build number</li>
 *   <li>{@code reportly.env.branch} — branch name</li>
 *   <li>{@code reportly.env.ci} — CI tool name</li>
 *   <li>{@code reportly.auto.screenshot} — capture screenshot on failure (default: true)</li>
 *   <li>{@code reportly.auto.generate} — auto-run python reporter after tests (default: false)</li>
 * </ul>
 */
public class ReportlyExtension implements
        BeforeAllCallback,
        AfterAllCallback,
        BeforeEachCallback,
        AfterEachCallback,
        TestWatcher {

    private static final ExtensionContext.Namespace NAMESPACE =
            ExtensionContext.Namespace.create(ReportlyExtension.class);

    private static final Map<String, SuiteData> suites = new ConcurrentHashMap<>();
    private static final Map<String, TestData> activeTests = new ConcurrentHashMap<>();
    private static final Map<String, Long> testStartTimes = new ConcurrentHashMap<>();
    private static boolean initialized = false;

    // ---- Lifecycle Hooks ----

    @Override
    public void beforeAll(ExtensionContext context) {
        String suiteName = context.getDisplayName();
        suites.computeIfAbsent(suiteName, k -> {
            SuiteData suite = new SuiteData();
            suite.name = k;
            suite.description = context.getTestClass().map(Class::getCanonicalName).orElse("");
            suite.start_time = Instant.now().toString();
            suite.environment = buildEnvironmentInfo();
            return suite;
        });
        initialized = true;
    }

    @Override
    public void afterAll(ExtensionContext context) {
        String suiteName = context.getDisplayName();
        SuiteData suite = suites.get(suiteName);
        if (suite != null) {
            suite.end_time = Instant.now().toString();
        }
        writeJsonOutput();
    }

    @Override
    public void beforeEach(ExtensionContext context) {
        String testId = context.getUniqueId();
        testStartTimes.put(testId, System.currentTimeMillis());

        TestData test = new TestData();
        test.test_id = UUID.randomUUID().toString().substring(0, 8);
        test.name = context.getDisplayName();
        test.suite_name = context.getParent()
                .map(ExtensionContext::getDisplayName).orElse("Default Suite");
        test.start_time = Instant.now().toString();
        test.tags = new ArrayList<>();
        test.steps = new ArrayList<>();
        test.attachments = new ArrayList<>();
        test.parameters = new HashMap<>();
        test.metadata = new HashMap<>();
        test.links = new HashMap<>();

        context.getTags().forEach(test.tags::add);

        activeTests.put(testId, test);
    }

    @Override
    public void afterEach(ExtensionContext context) {
        // handled by TestWatcher callbacks
    }

    // ---- TestWatcher Callbacks ----

    @Override
    public void testSuccessful(ExtensionContext context) {
        finalizeTest(context, "passed", null, null);
    }

    @Override
    public void testFailed(ExtensionContext context, Throwable cause) {
        String error = cause.getMessage() != null ? cause.getMessage() : cause.toString();
        String stackTrace = stackTraceToString(cause);

        captureFailureScreenshot(context);

        finalizeTest(context, "failed", error, stackTrace);
    }

    @Override
    public void testAborted(ExtensionContext context, Throwable cause) {
        String error = cause != null ? cause.getMessage() : "Test aborted";
        finalizeTest(context, "skipped", error, null);
    }

    @Override
    public void testDisabled(ExtensionContext context, Optional<String> reason) {
        String testId = context.getUniqueId();
        testStartTimes.putIfAbsent(testId, System.currentTimeMillis());

        TestData test = activeTests.computeIfAbsent(testId, k -> {
            TestData t = new TestData();
            t.test_id = UUID.randomUUID().toString().substring(0, 8);
            t.name = context.getDisplayName();
            t.suite_name = context.getParent()
                    .map(ExtensionContext::getDisplayName).orElse("Default Suite");
            t.start_time = Instant.now().toString();
            t.tags = new ArrayList<>();
            t.steps = new ArrayList<>();
            t.attachments = new ArrayList<>();
            t.parameters = new HashMap<>();
            t.metadata = new HashMap<>();
            t.links = new HashMap<>();
            return t;
        });

        finalizeTest(context, "skipped", reason.orElse("Disabled"), null);
    }

    // ---- Public API for manual step/screenshot logging ----

    /**
     * Log a test step from within a test method.
     * Retrieve the extension via {@code ExtensionContext} store or use static access.
     */
    public static void logStep(ExtensionContext context, String name, String status) {
        logStep(context, name, status, "", 0);
    }

    public static void logStep(ExtensionContext context, String name, String status,
                                String errorMessage, long durationMs) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test == null) return;

        StepData step = new StepData();
        step.name = name;
        step.status = status;
        step.error_message = errorMessage != null ? errorMessage : "";
        step.duration_ms = durationMs;
        step.timestamp = Instant.now().toString();
        step.attachments = new ArrayList<>();
        test.steps.add(step);
    }

    /**
     * Attach a Selenium/Appium screenshot to the current test.
     */
    public static void attachScreenshot(ExtensionContext context, WebDriver driver, String name) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test == null || driver == null) return;

        try {
            String base64 = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BASE64);
            AttachmentData attachment = new AttachmentData();
            attachment.name = name;
            attachment.type = "screenshot";
            attachment.data = base64;
            attachment.mime_type = "image/png";
            test.attachments.add(attachment);
        } catch (Exception e) {
            System.err.println("[Reportly] Screenshot capture failed: " + e.getMessage());
        }
    }

    /**
     * Attach a base64-encoded screenshot to the current test.
     */
    public static void attachScreenshotBase64(ExtensionContext context, String base64Data, String name) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test == null) return;

        AttachmentData attachment = new AttachmentData();
        attachment.name = name;
        attachment.type = "screenshot";
        attachment.data = base64Data;
        attachment.mime_type = "image/png";
        test.attachments.add(attachment);
    }

    /**
     * Set the platform info for the current test.
     */
    public static void setPlatform(ExtensionContext context, Map<String, String> platformInfo) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test == null) return;
        test.platform = platformInfo;
    }

    /**
     * Set category for the current test.
     */
    public static void setCategory(ExtensionContext context, String category) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test != null) test.category = category;
    }

    /**
     * Set priority for the current test.
     */
    public static void setPriority(ExtensionContext context, String priority) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test != null) test.priority = priority;
    }

    /**
     * Add a link (e.g. Jira, test case ID) to the current test.
     */
    public static void addLink(ExtensionContext context, String key, String value) {
        TestData test = activeTests.get(context.getUniqueId());
        if (test != null) test.links.put(key, value);
    }

    // ---- Internal Helpers ----

    private void finalizeTest(ExtensionContext context, String status,
                               String errorMessage, String stackTrace) {
        String testId = context.getUniqueId();
        TestData test = activeTests.remove(testId);
        if (test == null) return;

        long startMs = testStartTimes.getOrDefault(testId, System.currentTimeMillis());
        testStartTimes.remove(testId);

        test.status = status;
        test.error_message = errorMessage != null ? errorMessage : "";
        test.stack_trace = stackTrace != null ? stackTrace : "";
        test.end_time = Instant.now().toString();
        test.duration_ms = System.currentTimeMillis() - startMs;
        test.screenshot_count = (int) test.attachments.stream()
                .filter(a -> "screenshot".equals(a.type)).count();

        String suiteName = context.getParent()
                .map(ExtensionContext::getDisplayName).orElse("Default Suite");
        SuiteData suite = suites.computeIfAbsent(suiteName, k -> {
            SuiteData s = new SuiteData();
            s.name = k;
            s.start_time = Instant.now().toString();
            s.environment = buildEnvironmentInfo();
            return s;
        });
        suite.tests.add(test);
    }

    private void captureFailureScreenshot(ExtensionContext context) {
        if (!"true".equalsIgnoreCase(
                System.getProperty("reportly.auto.screenshot", "true"))) {
            return;
        }

        WebDriver driver = findDriverInTestInstance(context);
        if (driver != null) {
            attachScreenshot(context, driver, "failure_screenshot");
        }
    }

    private WebDriver findDriverInTestInstance(ExtensionContext context) {
        return context.getTestInstance().map(instance -> {
            for (Field field : instance.getClass().getDeclaredFields()) {
                if (WebDriver.class.isAssignableFrom(field.getType())) {
                    try {
                        field.setAccessible(true);
                        return (WebDriver) field.get(instance);
                    } catch (IllegalAccessException e) {
                        return null;
                    }
                }
            }
            return (WebDriver) null;
        }).orElse(null);
    }

    private static Map<String, String> buildEnvironmentInfo() {
        Map<String, String> env = new LinkedHashMap<>();
        putIfSet(env, "name", System.getProperty("reportly.env.name", ""));
        putIfSet(env, "url", System.getProperty("reportly.env.url", ""));
        putIfSet(env, "build_number", System.getProperty("reportly.env.build", ""));
        putIfSet(env, "branch", System.getProperty("reportly.env.branch", ""));
        putIfSet(env, "ci_tool", System.getProperty("reportly.env.ci", ""));
        putIfSet(env, "runner", System.getProperty("reportly.env.runner", ""));
        return env;
    }

    private static void putIfSet(Map<String, String> map, String key, String value) {
        if (value != null && !value.isEmpty()) {
            map.put(key, value);
        }
    }

    private void writeJsonOutput() {
        String outputDir = System.getProperty("reportly.output.dir", "./reports");
        String outputFile = System.getProperty("reportly.output.file", "junit-results.json");
        String title = System.getProperty("reportly.title", "JUnit Test Report");
        String description = System.getProperty("reportly.description", "");

        Map<String, Object> report = new LinkedHashMap<>();
        report.put("title", title);
        report.put("description", description);
        report.put("theme", "dark");
        report.put("suites", new ArrayList<>(suites.values()));

        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(report);

        try {
            Path dir = Path.of(outputDir);
            Files.createDirectories(dir);
            Path filePath = dir.resolve(outputFile);
            try (FileWriter writer = new FileWriter(filePath.toFile())) {
                writer.write(json);
            }
            System.out.println("[Reportly] JSON results written to: " + filePath.toAbsolutePath());

            if ("true".equalsIgnoreCase(System.getProperty("reportly.auto.generate", "false"))) {
                autoGenerateReport(filePath.toAbsolutePath().toString(), outputDir);
            }
        } catch (IOException e) {
            System.err.println("[Reportly] Failed to write JSON: " + e.getMessage());
        }
    }

    private void autoGenerateReport(String jsonPath, String outputDir) {
        try {
            String title = System.getProperty("reportly.title", "JUnit Test Report");
            ProcessBuilder pb = new ProcessBuilder(
                    "python", "-m", "reportly",
                    "--input", jsonPath,
                    "--output-dir", outputDir,
                    "--title", title,
                    "--open"
            );
            pb.inheritIO();
            Process process = pb.start();
            int exitCode = process.waitFor();
            if (exitCode == 0) {
                System.out.println("[Reportly] HTML report generated successfully.");
            } else {
                System.err.println("[Reportly] Report generation exited with code: " + exitCode);
            }
        } catch (Exception e) {
            System.err.println("[Reportly] Auto-generate failed: " + e.getMessage());
            System.err.println("[Reportly] Run manually: python -m reportly --input " + jsonPath + " --open");
        }
    }

    private static String stackTraceToString(Throwable t) {
        StringBuilder sb = new StringBuilder();
        for (StackTraceElement e : t.getStackTrace()) {
            sb.append("    at ").append(e.toString()).append("\n");
        }
        if (t.getCause() != null) {
            sb.append("Caused by: ").append(t.getCause().toString()).append("\n");
            for (StackTraceElement e : t.getCause().getStackTrace()) {
                sb.append("    at ").append(e.toString()).append("\n");
            }
        }
        return sb.toString();
    }

    // ---- Data Classes ----

    static class SuiteData {
        String name;
        String suite_id = UUID.randomUUID().toString().substring(0, 8);
        String description = "";
        String start_time;
        String end_time;
        Map<String, String> environment = new LinkedHashMap<>();
        List<TestData> tests = Collections.synchronizedList(new ArrayList<>());
    }

    static class TestData {
        String name;
        String test_id;
        String status;
        String suite_name;
        String description = "";
        String category = "";
        List<String> tags;
        String priority = "";
        Map<String, String> platform;
        String start_time;
        String end_time;
        long duration_ms;
        List<StepData> steps;
        String error_message = "";
        String stack_trace = "";
        List<AttachmentData> attachments;
        Map<String, Object> parameters;
        Map<String, Object> metadata;
        Map<String, String> links;
        int screenshot_count;
    }

    static class StepData {
        String name;
        String status;
        String description = "";
        String timestamp;
        long duration_ms;
        String error_message = "";
        List<AttachmentData> attachments;
    }

    static class AttachmentData {
        String name;
        String type;
        String data;
        String mime_type;
    }
}
