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
import java.util.Map;
import java.util.HashMap;
import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;

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
     * Get available MCP providers
     * @return Map containing the list of available providers
     */
    public Map<String, Object> getMCPProviders() throws IOException {
        String endpoint = "/api/mcp/providers";
        HttpURLConnection connection = createMCPConnection(endpoint, "GET");

        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * Configure an MCP provider
     * @param provider The provider name (e.g., "github")
     * @param config Configuration parameters
     * @return Map containing the configuration result
     */
    public Map<String, Object> configureMCPProvider(String provider, Map<String, String> config) throws IOException {
        String endpoint = "/api/mcp/provider/" + provider + "/config";
        String jsonPayload = mapToJson(config);

        HttpURLConnection connection = createMCPConnection(endpoint, "POST");
        connection.setRequestProperty("Content-Type", "application/json");

        // Send request
        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = jsonPayload.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        // Read response
        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * Start MCP OAuth flow for a provider
     * @param provider The provider name (e.g., "github")
     * @param authRequest Map containing the authentication request parameters
     * @return Map containing the authentication URL
     */
    public Map<String, Object> startMCPOAuth(String provider, Map<String, String> authRequest) throws IOException {
        String endpoint = "/api/mcp/provider/" + provider + "/auth";
        String jsonPayload = mapToJson(authRequest);

        HttpURLConnection connection = createMCPConnection(endpoint, "POST");
        connection.setRequestProperty("Content-Type", "application/json");

        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = jsonPayload.getBytes("utf-8");
            os.write(input, 0, input.length);
        }

        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * Start MCP authentication for a provider
     * @param provider The provider name (e.g., "github")
     * @return Map containing the authentication URL
     */
    public Map<String, Object> startMCPAuthentication(String provider) throws IOException {
        String endpoint = "/api/mcp/provider/" + provider + "/auth";
        Map<String, String> payload = new HashMap<>();
        // For now, we'll use a default config_id - this could be enhanced
        payload.put("config_id", "default");

        String jsonPayload = mapToJson(payload);

        HttpURLConnection connection = createMCPConnection(endpoint, "POST");
        connection.setRequestProperty("Content-Type", "application/json");

        // Send request
        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = jsonPayload.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        // Read response
        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * List MCP connections
     * @return Map containing the list of connections
     */
    public Map<String, Object> listMCPConnections() throws IOException {
        String endpoint = "/api/mcp/connections";
        HttpURLConnection connection = createMCPConnection(endpoint, "GET");

        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * List OAuth tokens
     * @return Map containing the list of tokens
     */
    public Map<String, Object> listOAuthTokens() throws IOException {
        String endpoint = "/api/mcp/tokens";
        HttpURLConnection connection = createMCPConnection(endpoint, "GET");

        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * Check if GitHub is connected via MCP
     * @return boolean indicating if GitHub OAuth token exists
     */
    public boolean isGitHubConnected() {
        try {
            Map<String, Object> tokensResponse = listOAuthTokens();
            if ("success".equals(tokensResponse.get("status"))) {
                Object tokensObj = tokensResponse.get("tokens");

                // Handle case where tokens might be parsed as a JSON string instead of list
                if (tokensObj instanceof String) {
                    String tokensStr = (String) tokensObj;
                    // Check if the JSON string contains GitHub provider tokens
                    return tokensStr.contains("\"provider\": \"github\"") ||
                           tokensStr.contains("\"provider\":\"github\"") ||
                           tokensStr.contains("github");
                } else if (tokensObj instanceof java.util.List) {
                    @SuppressWarnings("unchecked")
                    java.util.List<Map<String, Object>> tokens = (java.util.List<Map<String, Object>>) tokensObj;
                    // Check if any token is for GitHub provider
                    return tokens.stream().anyMatch(token -> "github".equals(token.get("provider")));
                }

                // Also check if total_tokens > 0 as a fallback
                Object totalTokens = tokensResponse.get("total_tokens");
                if (totalTokens instanceof Number) {
                    return ((Number) totalTokens).intValue() > 0;
                }
            }
            return false;
        } catch (Exception e) {
            System.err.println("❌ Error checking GitHub connection: " + e.getMessage());
            return false;
        }
    }

    /**
     * Helper method to create HTTP connection
     */
    private HttpURLConnection createConnection(String endpoint, String method) throws IOException {
        URL url = new URL(apiUrl + endpoint);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(30000);

        if (method.equals("POST") || method.equals("PUT")) {
            connection.setDoOutput(true);
        }

        return connection;
    }

    /**
     * Helper method to create HTTP connection for MCP endpoints (uses base API URL)
     */
    private HttpURLConnection createMCPConnection(String endpoint, String method) throws IOException {
        // Extract base server URL from apiUrl (remove /api/chat suffix) and add MCP endpoint
        String baseUrl = apiUrl.replace("/api/chat", "");
        String url = baseUrl + endpoint;



        URL connectionUrl = new URL(url);
        HttpURLConnection connection = (HttpURLConnection) connectionUrl.openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(30000);

        if (method.equals("POST") || method.equals("PUT")) {
            connection.setDoOutput(true);
        }

        return connection;
    }

    /**
     * Helper method to read response from connection
     */
    private String readResponse(HttpURLConnection connection) throws IOException {
        Scanner scanner;
        if (connection.getResponseCode() >= 200 && connection.getResponseCode() < 300) {
            scanner = new Scanner(connection.getInputStream(), StandardCharsets.UTF_8.name());
        } else {
            scanner = new Scanner(connection.getErrorStream(), StandardCharsets.UTF_8.name());
        }

        scanner.useDelimiter("\\A");
        String response = scanner.hasNext() ? scanner.next() : "";
        scanner.close();

        return response;
    }

    /**
     * Simple JSON utility to convert Map to JSON string
     */
    private String mapToJson(Map<String, String> map) {
        StringBuilder json = new StringBuilder("{");
        boolean first = true;
        for (Map.Entry<String, String> entry : map.entrySet()) {
            if (!first) {
                json.append(",");
            }
            json.append("\"").append(escapeJson(entry.getKey())).append("\":");
            json.append("\"").append(escapeJson(entry.getValue())).append("\"");
            first = false;
        }
        json.append("}");
        return json.toString();
    }

    /**
     * Parse JSON response using proper JSONObject library
     */
    private Map<String, Object> parseJsonResponse(String jsonResponse) {
        Map<String, Object> result = new HashMap<>();

        try {
            JSONObject jsonObj = new JSONObject(jsonResponse);

            // Convert JSONObject to Map
            for (String key : jsonObj.keySet()) {
                Object value = jsonObj.get(key);

                if (value instanceof JSONArray) {
                    // Convert JSONArray to formatted string for compatibility with existing code
                    JSONArray jsonArray = (JSONArray) value;
                    result.put(key, jsonArray.toString(2)); // Pretty print with 2-space indent
                } else if (value instanceof JSONObject) {
                    // Convert nested JSONObject to formatted string
                    JSONObject nestedObj = (JSONObject) value;
                    result.put(key, nestedObj.toString(2));
                } else {
                    result.put(key, value);
                }
            }

        } catch (JSONException e) {
            System.err.println("❌ JSON parsing error: " + e.getMessage());
            System.err.println("📄 Raw JSON: " + jsonResponse);
            result.put("status", "error");
            result.put("error", "JSON parsing failed: " + e.getMessage());
        } catch (Exception e) {
            System.err.println("❌ Unexpected error parsing JSON: " + e.getMessage());
            result.put("status", "error");
            result.put("error", "Unexpected parsing error: " + e.getMessage());
        }

        return result;
    }

    /**
     * Escape special characters for JSON
     */
    private String escapeJson(String str) {
        if (str == null) return "";
        return str.replace("\\", "\\\\")
                  .replace("\"", "\\\"")
                  .replace("\n", "\\n")
                  .replace("\r", "\\r")
                  .replace("\t", "\\t");
    }

    /**
     * Configure MCP provider with individual parameters (convenience method)
     * @param provider The provider name (e.g., "github")
     * @param clientId OAuth client ID
     * @param clientSecret OAuth client secret
     * @param redirectUri OAuth redirect URI
     * @param scope OAuth scopes
     * @return Map containing the configuration result
     */
    public Map<String, Object> configureMCPProvider(String provider, String clientId, String clientSecret, String redirectUri, String scope) throws IOException {
        Map<String, String> config = new HashMap<>();
        config.put("client_id", clientId);
        config.put("client_secret", clientSecret);
        config.put("redirect_uri", redirectUri);
        config.put("scope", scope);
        return configureMCPProvider(provider, config);
    }

    /**
     * Start MCP OAuth flow with config ID (convenience method)
     * @param provider The provider name (e.g., "github")
     * @param configId The configuration ID
     * @return Map containing the authentication URL
     */
    public Map<String, Object> startMCPOAuth(String provider, String configId) throws IOException {
        Map<String, String> authRequest = new HashMap<>();
        authRequest.put("config_id", configId);
        return startMCPOAuth(provider, authRequest);
    }

    /**
     * Revoke a specific OAuth token
     * @param tokenId The token ID to revoke
     * @return Map containing the revocation result
     */
    public Map<String, Object> revokeToken(String tokenId) throws IOException {
        String endpoint = "/api/mcp/token/" + tokenId + "/revoke";
        HttpURLConnection connection = createMCPConnection(endpoint, "POST");
        connection.setRequestProperty("Content-Type", "application/json");

        String response = readResponse(connection);
        return parseJsonResponse(response);
    }

    /**
     * Revoke all OAuth tokens for a provider
     * @param provider The provider name (e.g., "github")
     * @return Map containing the revocation result
     */
    public Map<String, Object> revokeAllTokens(String provider) throws IOException {
        // First, get all tokens
        Map<String, Object> tokensResponse = listOAuthTokens();
        if (!"success".equals(tokensResponse.get("status"))) {
            throw new IOException("Failed to list tokens: " + tokensResponse.get("error"));
        }

        Object tokensObj = tokensResponse.get("tokens");
        java.util.List<String> tokenIds = new java.util.ArrayList<>();

        if (tokensObj instanceof String) {
            String tokensStr = (String) tokensObj;
            // Simple check: if no tokens for this provider, return success
            if (!tokensStr.contains("\"provider\": \"" + provider + "\"") &&
                !tokensStr.contains("\"provider\":\"" + provider + "\"")) {
                return Map.of("status", "success", "message", "No tokens found for " + provider, "revoked_count", 0);
            }

            // Improved token parsing - find all token objects for the specified provider
            tokenIds = extractTokenIdsForProvider(tokensStr, provider);
        }

        // Revoke each token
        int revokedCount = 0;
        java.util.List<String> errors = new java.util.ArrayList<>();

        for (String tokenId : tokenIds) {
            try {
                Map<String, Object> result = revokeToken(tokenId);
                if ("success".equals(result.get("status"))) {
                    revokedCount++;
                } else {
                    errors.add("Token " + tokenId + ": " + result.get("error"));
                }
            } catch (Exception e) {
                errors.add("Token " + tokenId + ": " + e.getMessage());
            }
        }

        // Return result
        Map<String, Object> result = new HashMap<>();
        result.put("status", "success");
        result.put("message", "Revoked " + revokedCount + " out of " + tokenIds.size() + " tokens for " + provider);
        result.put("revoked_count", revokedCount);
        result.put("total_tokens", tokenIds.size());

        if (!errors.isEmpty()) {
            result.put("errors", errors);
        }

        return result;
    }

    /**
     * Extract token IDs for a specific provider using proper JSON parsing
     * @param tokensJson JSON string containing tokens array
     * @param provider Provider name to filter by
     * @return List of token IDs for the specified provider
     */
    private java.util.List<String> extractTokenIdsForProvider(String tokensJson, String provider) {
        java.util.List<String> tokenIds = new java.util.ArrayList<>();

        try {
            System.out.println("🔍 Parsing tokens JSON for provider: " + provider);
            System.out.println("📄 JSON length: " + tokensJson.length());

            // Use proper JSON parsing
            JSONArray tokensArray = new JSONArray(tokensJson);

            for (int i = 0; i < tokensArray.length(); i++) {
                JSONObject token = tokensArray.getJSONObject(i);

                // Check if this token is for the specified provider
                if (token.has("provider") && provider.equals(token.getString("provider"))) {
                    if (token.has("token_id")) {
                        String tokenId = token.getString("token_id");
                        tokenIds.add(tokenId);
                        System.out.println("✅ Found " + provider + " token: " + tokenId);
                    }
                }
            }

        } catch (JSONException e) {
            System.err.println("❌ JSON parsing error: " + e.getMessage());
            System.err.println("📄 Trying fallback parsing...");

            // Fallback to pattern matching if JSON parsing fails
            tokenIds = extractTokenIdsUsingPatternMatching(tokensJson, provider);

        } catch (Exception e) {
            System.err.println("❌ Unexpected error parsing tokens JSON: " + e.getMessage());
            e.printStackTrace();
        }

        System.out.println("📊 Extracted " + tokenIds.size() + " token IDs for " + provider);
        return tokenIds;
    }

    /**
     * Alternative method to extract token IDs using pattern matching
     */
    private java.util.List<String> extractTokenIdsUsingPatternMatching(String tokensJson, String provider) {
        java.util.List<String> tokenIds = new java.util.ArrayList<>();

        try {
            // Find all token objects that contain the provider
            int searchStart = 0;
            while (true) {
                // Find next occurrence of provider
                int providerIndex = tokensJson.indexOf("\"provider\": \"" + provider + "\"", searchStart);
                if (providerIndex == -1) {
                    providerIndex = tokensJson.indexOf("\"provider\":\"" + provider + "\"", searchStart);
                }

                if (providerIndex == -1) {
                    break; // No more occurrences
                }

                // Find the token_id in the same token object (search backwards and forwards)
                String tokenId = findTokenIdNearProvider(tokensJson, providerIndex);
                if (tokenId != null && !tokenIds.contains(tokenId)) {
                    tokenIds.add(tokenId);
                    System.out.println("✅ Pattern matched " + provider + " token: " + tokenId);
                }

                searchStart = providerIndex + 1;
            }

        } catch (Exception e) {
            System.err.println("❌ Error in pattern matching: " + e.getMessage());
        }

        return tokenIds;
    }

    /**
     * Find token_id near a provider occurrence
     */
    private String findTokenIdNearProvider(String json, int providerIndex) {
        try {
            // Search backwards and forwards from provider index to find token_id
            int searchStart = Math.max(0, providerIndex - 500); // Search 500 chars before
            int searchEnd = Math.min(json.length(), providerIndex + 500); // Search 500 chars after

            String searchArea = json.substring(searchStart, searchEnd);

            // Look for token_id pattern
            String[] patterns = {"\"token_id\": \"", "\"token_id\":\""};

            for (String pattern : patterns) {
                int tokenIdIndex = searchArea.indexOf(pattern);
                if (tokenIdIndex != -1) {
                    int start = tokenIdIndex + pattern.length();
                    int end = searchArea.indexOf("\"", start);
                    if (end > start) {
                        return searchArea.substring(start, end);
                    }
                }
            }

        } catch (Exception e) {
            System.err.println("❌ Error finding token ID near provider: " + e.getMessage());
        }

        return null;
    }

    /**
     * Extract token_id from a line of JSON
     */
    private String extractTokenIdFromLine(String line) {
        try {
            String[] patterns = {"\"token_id\": \"", "\"token_id\":\""};

            for (String pattern : patterns) {
                int start = line.indexOf(pattern);
                if (start != -1) {
                    start += pattern.length();
                    int end = line.indexOf("\"", start);
                    if (end > start) {
                        return line.substring(start, end);
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("❌ Error extracting token ID from line: " + e.getMessage());
        }

        return null;
    }

    /**
     * Extract token_id from a single token object JSON string
     * @param tokenObject JSON string of a single token object
     * @return Token ID or null if not found
     */
    private String extractTokenIdFromObject(String tokenObject) {
        try {
            // Look for "token_id": "uuid-value"
            String[] patterns = {"\"token_id\": \"", "\"token_id\":\""};

            for (String pattern : patterns) {
                int start = tokenObject.indexOf(pattern);
                if (start != -1) {
                    start += pattern.length();
                    int end = tokenObject.indexOf("\"", start);
                    if (end > start) {
                        return tokenObject.substring(start, end);
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("❌ Error extracting token ID: " + e.getMessage());
        }

        return null;
    }

    /**
     * Shuts down the executor service
     */
    public void shutdown() {
        executor.shutdown();
        System.out.println("🛑 iChat API Service shutdown");
    }
}
