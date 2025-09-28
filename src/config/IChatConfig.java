package config;

/**
 * Configuration class for iChat application settings
 */
public class IChatConfig {

    // API Server Configuration (Docker containerized Python Flask API)
    public static final String DEFAULT_API_BASE_URL = "http://localhost:8080/api";
    public static final String DEFAULT_API_URL = DEFAULT_API_BASE_URL + "/chat";
    public static final String HEALTH_CHECK_URL = DEFAULT_API_BASE_URL + "/health";
    public static final String STATUS_URL = DEFAULT_API_BASE_URL + "/status";
    public static final String PING_URL = DEFAULT_API_BASE_URL + "/ping";

    // Fallback URLs for production deployment
    public static final String FALLBACK_API_BASE_URL = "https://your-ichat-server.com/api";
    public static final String FALLBACK_API_URL = FALLBACK_API_BASE_URL + "/chat";

    // Connection Settings
    public static final int CONNECTION_TIMEOUT = 10000; // 10 seconds
    public static final int READ_TIMEOUT = 120000;      // 5 minutes (300 seconds)

    // UI Settings
    public static final int SIDEBAR_WIDTH = 380;
    public static final int SIDEBAR_HEIGHT = 650;
    public static final int SIDEBAR_MARGIN = 20;

    // Application Info
    public static final String APP_NAME = "iChat Assistant";
    public static final String APP_VERSION = "2.0.0";  // Updated to match API server version
    public static final String USER_AGENT = "iChat-Desktop-Client/" + APP_VERSION;
    public static final String CLIENT_ID = "desktop";

    /**
     * Gets the API base URL from system properties or environment variables
     * Falls back to default if not specified
     */
    public static String getApiBaseUrl() {
        // Check system property first
        String apiBaseUrl = System.getProperty("ichat.api.base.url");
        if (apiBaseUrl != null && !apiBaseUrl.trim().isEmpty()) {
            System.out.println("📋 Using API base URL from system property: " + apiBaseUrl);
            return apiBaseUrl.trim();
        }

        // Check environment variable
        apiBaseUrl = System.getenv("ICHAT_API_BASE_URL");
        if (apiBaseUrl != null && !apiBaseUrl.trim().isEmpty()) {
            System.out.println("📋 Using API base URL from environment: " + apiBaseUrl);
            return apiBaseUrl.trim();
        }

        // Use default
        System.out.println("📋 Using default API base URL: " + DEFAULT_API_BASE_URL);
        return DEFAULT_API_BASE_URL;
    }

    /**
     * Gets the chat API URL (base URL + /chat endpoint)
     */
    public static String getApiUrl() {
        return getApiBaseUrl() + "/chat";
    }

    /**
     * Gets the health check URL
     */
    public static String getHealthCheckUrl() {
        return getApiBaseUrl() + "/health";
    }

    /**
     * Gets the status URL
     */
    public static String getStatusUrl() {
        return getApiBaseUrl() + "/status";
    }

    /**
     * Gets the ping URL
     */
    public static String getPingUrl() {
        return getApiBaseUrl() + "/ping";
    }

    /**
     * Prints comprehensive configuration information
     */
    public static void printConfig() {
        System.out.println("🔧 iChat Configuration:");
        System.out.println("   API Base URL: " + getApiBaseUrl());
        System.out.println("   Chat Endpoint: " + getApiUrl());
        System.out.println("   Health Check: " + getHealthCheckUrl());
        System.out.println("   Status Endpoint: " + getStatusUrl());
        System.out.println("   Ping Endpoint: " + getPingUrl());
        System.out.println("   Connection Timeout: " + CONNECTION_TIMEOUT + "ms");
        System.out.println("   Read Timeout: " + READ_TIMEOUT + "ms");
        System.out.println("   App Version: " + APP_VERSION);
        System.out.println("   Client ID: " + CLIENT_ID);
        System.out.println("   User Agent: " + USER_AGENT);
    }

    /**
     * Checks if the API server is accessible by testing the health endpoint
     */
    public static boolean isApiServerHealthy() {
        try {
            java.net.http.HttpClient client = java.net.http.HttpClient.newBuilder()
                    .connectTimeout(java.time.Duration.ofMillis(CONNECTION_TIMEOUT))
                    .build();

            java.net.http.HttpRequest request = java.net.http.HttpRequest.newBuilder()
                    .uri(java.net.URI.create(getHealthCheckUrl()))
                    .timeout(java.time.Duration.ofMillis(READ_TIMEOUT))
                    .GET()
                    .build();

            java.net.http.HttpResponse<String> response = client.send(request,
                    java.net.http.HttpResponse.BodyHandlers.ofString());

            boolean isHealthy = response.statusCode() == 200 &&
                    response.body().contains("\"status\":\"healthy\"");

            if (isHealthy) {
                System.out.println("✅ API Server is healthy and responding");
            } else {
                System.out.println("⚠️ API Server responded but may not be healthy");
            }

            return isHealthy;

        } catch (Exception e) {
            System.out.println("❌ API Server health check failed: " + e.getMessage());
            return false;
        }
    }
}
