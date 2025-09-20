package config;

/**
 * Configuration class for iChat application settings
 */
public class IChatConfig {
    
    // API Configuration
    public static final String DEFAULT_API_URL = "http://localhost:8080/api/chat";
    public static final String FALLBACK_API_URL = "https://your-ichat-server.com/api/chat";
    
    // Connection Settings
    public static final int CONNECTION_TIMEOUT = 10000; // 10 seconds
    public static final int READ_TIMEOUT = 30000;       // 30 seconds
    
    // UI Settings
    public static final int SIDEBAR_WIDTH = 380;
    public static final int SIDEBAR_HEIGHT = 650;
    public static final int SIDEBAR_MARGIN = 20;
    
    // Application Info
    public static final String APP_NAME = "iChat Assistant";
    public static final String APP_VERSION = "1.0.0";
    public static final String USER_AGENT = "iChat-Desktop-Client/" + APP_VERSION;
    
    /**
     * Gets the API URL from system properties or environment variables
     * Falls back to default if not specified
     */
    public static String getApiUrl() {
        // Check system property first
        String apiUrl = System.getProperty("ichat.api.url");
        if (apiUrl != null && !apiUrl.trim().isEmpty()) {
            System.out.println("📋 Using API URL from system property: " + apiUrl);
            return apiUrl.trim();
        }
        
        // Check environment variable
        apiUrl = System.getenv("ICHAT_API_URL");
        if (apiUrl != null && !apiUrl.trim().isEmpty()) {
            System.out.println("📋 Using API URL from environment: " + apiUrl);
            return apiUrl.trim();
        }
        
        // Use default
        System.out.println("📋 Using default API URL: " + DEFAULT_API_URL);
        return DEFAULT_API_URL;
    }
    
    /**
     * Prints configuration information
     */
    public static void printConfig() {
        System.out.println("🔧 iChat Configuration:");
        System.out.println("   API URL: " + getApiUrl());
        System.out.println("   Connection Timeout: " + CONNECTION_TIMEOUT + "ms");
        System.out.println("   Read Timeout: " + READ_TIMEOUT + "ms");
        System.out.println("   App Version: " + APP_VERSION);
    }
}
