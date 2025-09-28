package api;

import config.IChatConfig;
import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Scanner;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Service class for making API calls to the iChat server
 */
public class IChatApiService {

    private final String apiUrl;
    private final ExecutorService executor;

    /**
     * Constructor with default API URL from configuration
     */
    public IChatApiService() {
        this(IChatConfig.getApiUrl());
    }
    
    /**
     * Constructor with custom API URL
     */
    public IChatApiService(String apiUrl) {
        this.apiUrl = apiUrl;
        this.executor = Executors.newFixedThreadPool(3); // Thread pool for async requests
        System.out.println("✅ iChat API Service initialized with URL: " + apiUrl);
    }
    
    /**
     * Sends a message to the iChat server asynchronously
     * @param message The user message to send
     * @return CompletableFuture with the server response
     */
    public CompletableFuture<String> sendMessage(String message) {
        return sendMessage(message, false, null);
    }

    /**
     * Sends a message to the iChat server asynchronously with RAG support
     * @param message The user message to send
     * @param useRag Whether to use RAG (Retrieval-Augmented Generation)
     * @param sessionId The session ID for context management
     * @return CompletableFuture with the server response
     */
    public CompletableFuture<String> sendMessage(String message, boolean useRag, String sessionId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                System.out.println("📤 Sending message to iChat server: " + message + " (RAG: " + useRag + ")");
                return sendMessageSync(message, useRag, sessionId);
            } catch (Exception e) {
                System.err.println("❌ Error sending message to iChat server: " + e.getMessage());
                return "Sorry, I'm having trouble connecting to the server right now. Please try again later. 🔄";
            }
        }, executor);
    }
    
    /**
     * Sends a message to the iChat server synchronously
     * @param message The user message to send
     * @return The server response
     * @throws IOException if the request fails
     */
    private String sendMessageSync(String message) throws IOException {
        return sendMessageSync(message, false, null);
    }

    /**
     * Sends a message to the iChat server synchronously with RAG support
     * @param message The user message to send
     * @param useRag Whether to use RAG (Retrieval-Augmented Generation)
     * @param sessionId The session ID for context management
     * @return The server response
     * @throws IOException if the request fails
     */
    private String sendMessageSync(String message, boolean useRag, String sessionId) throws IOException {
        URL url = new URL(apiUrl);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        
        try {
            // Configure the connection
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", IChatConfig.USER_AGENT);
            connection.setDoOutput(true);
            connection.setConnectTimeout(IChatConfig.CONNECTION_TIMEOUT);
            connection.setReadTimeout(IChatConfig.READ_TIMEOUT);
            
            // Create JSON payload with client ID from config and RAG support
            String jsonPayload = createJsonPayload(message, IChatConfig.CLIENT_ID, useRag, sessionId);
            System.out.println("📋 JSON Payload: " + jsonPayload);
            
            // Send the request
            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonPayload.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
            
            // Get the response
            int responseCode = connection.getResponseCode();
            System.out.println("📊 Response Code: " + responseCode);
            
            if (responseCode == HttpURLConnection.HTTP_OK) {
                // Read successful response
                try (Scanner scanner = new Scanner(connection.getInputStream(), StandardCharsets.UTF_8)) {
                    String response = scanner.useDelimiter("\\A").next();
                    System.out.println("✅ Server Response: " + response);
                    return parseResponse(response);
                }
            } else {
                // Read error response
                String errorResponse = "";
                try (Scanner scanner = new Scanner(connection.getErrorStream(), StandardCharsets.UTF_8)) {
                    errorResponse = scanner.useDelimiter("\\A").next();
                } catch (Exception e) {
                    errorResponse = "Unknown error";
                }
                
                System.err.println("❌ Server Error (" + responseCode + "): " + errorResponse);
                return "Sorry, the server returned an error (" + responseCode + "). Please try again. 🔄";
            }
            
        } finally {
            connection.disconnect();
        }
    }
    
    /**
     * Creates JSON payload for the API request
     * @param message The user message
     * @param client The client identifier
     * @return JSON string
     */
    private String createJsonPayload(String message, String client) {
        return createJsonPayload(message, client, false, null);
    }

    /**
     * Creates JSON payload for the API request with RAG support
     * @param message The user message
     * @param client The client identifier
     * @param useRag Whether to use RAG
     * @param sessionId The session ID for context management
     * @return JSON string
     */
    private String createJsonPayload(String message, String client, boolean useRag, String sessionId) {
        // Escape JSON special characters
        String escapedMessage = message
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t");

        String escapedClient = client
            .replace("\\", "\\\\")
            .replace("\"", "\\\"");

        StringBuilder jsonBuilder = new StringBuilder();
        jsonBuilder.append("{ ");
        jsonBuilder.append("\"message\": \"").append(escapedMessage).append("\", ");
        jsonBuilder.append("\"timestamp\": ").append(System.currentTimeMillis()).append(", ");
        jsonBuilder.append("\"client\": \"").append(escapedClient).append("\"");

        if (useRag) {
            jsonBuilder.append(", \"use_rag\": true");
        }

        if (sessionId != null && !sessionId.trim().isEmpty()) {
            String escapedSessionId = sessionId
                .replace("\\", "\\\\")
                .replace("\"", "\\\"");
            jsonBuilder.append(", \"session_id\": \"").append(escapedSessionId).append("\"");
        }

        jsonBuilder.append(" }");
        return jsonBuilder.toString();
    }
    
    /**
     * Parses the server response
     * @param response Raw server response
     * @return Parsed message content
     */
    private String parseResponse(String response) {
        try {
            // Simple JSON parsing for response message
            // Look for "message" field in JSON response
            if (response.contains("\"message\"")) {
                int start = response.indexOf("\"message\"") + 10;
                start = response.indexOf("\"", start) + 1;
                int end = response.indexOf("\"", start);
                
                if (start > 10 && end > start) {
                    String message = response.substring(start, end);
                    // Unescape JSON characters
                    return message
                        .replace("\\\"", "\"")
                        .replace("\\n", "\n")
                        .replace("\\r", "\r")
                        .replace("\\t", "\t")
                        .replace("\\\\", "\\");
                }
            }
            
            // If no message field found, return the whole response
            return response;
            
        } catch (Exception e) {
            System.err.println("⚠️ Error parsing response: " + e.getMessage());
            return response; // Return raw response if parsing fails
        }
    }
    
    /**
     * Tests the connection to the iChat server
     * @return CompletableFuture with connection test result
     */
    public CompletableFuture<Boolean> testConnection() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                System.out.println("🔍 Testing connection to iChat server...");
                String response = sendMessageSync("ping");
                System.out.println("✅ Connection test successful");
                return true;
            } catch (Exception e) {
                System.err.println("❌ Connection test failed: " + e.getMessage());
                return false;
            }
        }, executor);
    }
    
    /**
     * Updates the API URL
     * @param newApiUrl The new API URL
     */
    public void setApiUrl(String newApiUrl) {
        System.out.println("🔄 API URL updated to: " + newApiUrl);
    }
    
    /**
     * Shuts down the executor service
     */
    public void shutdown() {
        executor.shutdown();
        System.out.println("🛑 iChat API Service shutdown");
    }
}
