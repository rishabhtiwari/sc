package api;

import config.IChatConfig;
// Using simple JSON parsing to avoid external dependencies

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Client-side document storage service for iChat Assistant.
 * Manages local document storage (max 1GB) and document ID mapping for RAG context.
 */
public class ClientDocumentStorageService {

    private final String apiBaseUrl;
    private final ExecutorService executor;
    // Simple JSON handling without external dependencies
    private final Path storageDirectory;
    private final Path metadataFile;
    private final long MAX_STORAGE_SIZE = 1024L * 1024L * 1024L; // 1GB in bytes
    private static final String BOUNDARY = "----WebKitFormBoundary" + System.currentTimeMillis();

    // In-memory storage for document metadata
    private Map<String, DocumentMetadata> documentMetadataMap;
    private Set<String> currentContextDocuments;
    private String currentSessionId;

    /**
     * Constructor with default API URL from configuration
     */
    public ClientDocumentStorageService() {
        this.apiBaseUrl = IChatConfig.getApiBaseUrl();
        this.executor = Executors.newFixedThreadPool(3);
        // Initialize without Gson dependency
        this.currentContextDocuments = new HashSet<>();
        this.currentSessionId = "default_session";

        // Initialize storage directory
        this.storageDirectory = initializeStorageDirectory();
        this.metadataFile = storageDirectory.resolve("document_metadata.json");

        // Load existing metadata
        this.documentMetadataMap = loadDocumentMetadata();

        System.out.println("✅ Client Document Storage Service initialized");
        System.out.println("📁 Storage directory: " + storageDirectory.toAbsolutePath());
        System.out.println("📊 Current storage: " + formatBytes(getCurrentStorageSize()) + " / " + formatBytes(MAX_STORAGE_SIZE));
        System.out.println("📄 Documents stored: " + documentMetadataMap.size());
    }

    /**
     * Document metadata class for client storage
     */
    public static class DocumentMetadata {
        public String documentId;
        public String filename;
        public String title;
        public String author;
        public String category;
        public long uploadDate;
        public long fileSize;
        public String storageKey;
        public String localPath;
        public String contentType;

        public DocumentMetadata() {}

        public DocumentMetadata(String documentId, String filename, String title, String author, 
                              String category, long fileSize, String localPath, String contentType) {
            this.documentId = documentId;
            this.filename = filename;
            this.title = title;
            this.author = author;
            this.category = category;
            this.uploadDate = System.currentTimeMillis();
            this.fileSize = fileSize;
            this.storageKey = "client_doc_" + documentId;
            this.localPath = localPath;
            this.contentType = contentType;
        }
    }

    /**
     * Uploads and stores a document with client-side storage
     */
    public CompletableFuture<DocumentMetadata> uploadAndStoreDocument(File file, String title, String author, String category) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                System.out.println("📤 Uploading and storing document: " + file.getName());

                // Check storage space
                if (!hasStorageSpace(file.length())) {
                    throw new RuntimeException("Insufficient storage space. Current: " + 
                        formatBytes(getCurrentStorageSize()) + ", Available: " + 
                        formatBytes(getRemainingStorageSpace()) + ", Required: " + formatBytes(file.length()));
                }

                // Upload to server for embedding
                String documentId = uploadDocumentForEmbedding(file, title, author, category);
                
                if (documentId == null || documentId.isEmpty()) {
                    throw new RuntimeException("Failed to get document ID from server");
                }

                // Store document locally
                String localPath = storeDocumentLocally(file, documentId);

                // Create metadata
                DocumentMetadata metadata = new DocumentMetadata(
                    documentId, file.getName(), title, author, category, 
                    file.length(), localPath, getContentType(file.getName())
                );

                // Save metadata
                documentMetadataMap.put(documentId, metadata);
                saveDocumentMetadata();

                System.out.println("✅ Document stored successfully: " + documentId);
                return metadata;

            } catch (Exception e) {
                System.err.println("❌ Error uploading and storing document: " + e.getMessage());
                throw new RuntimeException("Document upload failed: " + e.getMessage(), e);
            }
        }, executor);
    }

    /**
     * Sets the context for the current session using document IDs
     */
    public CompletableFuture<Boolean> setSessionContext(List<String> documentIds, String sessionId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                System.out.println("🔗 Setting session context with " + documentIds.size() + " documents");

                // Validate document IDs exist locally
                List<String> validDocumentIds = new ArrayList<>();
                for (String docId : documentIds) {
                    if (documentMetadataMap.containsKey(docId)) {
                        validDocumentIds.add(docId);
                    } else {
                        System.out.println("⚠️ Document ID not found locally: " + docId);
                    }
                }

                if (validDocumentIds.isEmpty()) {
                    System.out.println("❌ No valid document IDs found");
                    return false;
                }

                // Call API server to set context
                boolean success = setServerContext(validDocumentIds, sessionId);
                
                if (success) {
                    this.currentContextDocuments = new HashSet<>(validDocumentIds);
                    this.currentSessionId = sessionId;
                    System.out.println("✅ Session context set successfully");
                } else {
                    System.out.println("❌ Failed to set server context");
                }

                return success;

            } catch (Exception e) {
                System.err.println("❌ Error setting session context: " + e.getMessage());
                return false;
            }
        }, executor);
    }

    /**
     * Gets the current context status
     */
    public Map<String, Object> getContextStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("session_id", currentSessionId);
        status.put("document_count", currentContextDocuments.size());
        status.put("document_ids", new ArrayList<>(currentContextDocuments));
        
        List<Map<String, Object>> documentInfo = new ArrayList<>();
        for (String docId : currentContextDocuments) {
            DocumentMetadata metadata = documentMetadataMap.get(docId);
            if (metadata != null) {
                Map<String, Object> info = new HashMap<>();
                info.put("document_id", metadata.documentId);
                info.put("title", metadata.title);
                info.put("filename", metadata.filename);
                info.put("author", metadata.author);
                info.put("category", metadata.category);
                info.put("file_size", metadata.fileSize);
                info.put("upload_date", metadata.uploadDate);
                documentInfo.add(info);
            }
        }
        status.put("documents", documentInfo);
        
        return status;
    }

    /**
     * Clears the current session context
     */
    public CompletableFuture<Boolean> clearSessionContext() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                System.out.println("🧹 Clearing session context");

                // Call API server to clear context
                boolean success = clearServerContext(currentSessionId);
                
                if (success) {
                    this.currentContextDocuments.clear();
                    System.out.println("✅ Session context cleared successfully");
                } else {
                    System.out.println("❌ Failed to clear server context");
                }

                return success;

            } catch (Exception e) {
                System.err.println("❌ Error clearing session context: " + e.getMessage());
                return false;
            }
        }, executor);
    }

    /**
     * Gets all stored documents metadata
     */
    public List<DocumentMetadata> getAllDocuments() {
        return new ArrayList<>(documentMetadataMap.values());
    }

    /**
     * Removes a document from storage
     */
    public CompletableFuture<Boolean> removeDocument(String documentId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                DocumentMetadata metadata = documentMetadataMap.get(documentId);
                if (metadata == null) {
                    System.out.println("⚠️ Document not found: " + documentId);
                    return false;
                }

                // Remove from local storage
                Path localFile = Paths.get(metadata.localPath);
                if (Files.exists(localFile)) {
                    Files.delete(localFile);
                }

                // Remove from metadata
                documentMetadataMap.remove(documentId);
                saveDocumentMetadata();

                // Remove from current context if present
                currentContextDocuments.remove(documentId);

                System.out.println("✅ Document removed: " + documentId);
                return true;

            } catch (Exception e) {
                System.err.println("❌ Error removing document: " + e.getMessage());
                return false;
            }
        }, executor);
    }

    /**
     * Gets current storage statistics
     */
    public Map<String, Object> getStorageStats() {
        long currentSize = getCurrentStorageSize();
        Map<String, Object> stats = new HashMap<>();
        stats.put("current_size_bytes", currentSize);
        stats.put("current_size_formatted", formatBytes(currentSize));
        stats.put("max_size_bytes", MAX_STORAGE_SIZE);
        stats.put("max_size_formatted", formatBytes(MAX_STORAGE_SIZE));
        stats.put("remaining_bytes", MAX_STORAGE_SIZE - currentSize);
        stats.put("remaining_formatted", formatBytes(MAX_STORAGE_SIZE - currentSize));
        stats.put("usage_percentage", (double) currentSize / MAX_STORAGE_SIZE * 100);
        stats.put("document_count", documentMetadataMap.size());
        return stats;
    }

    /**
     * Initializes the storage directory
     */
    private Path initializeStorageDirectory() {
        try {
            String userHome = System.getProperty("user.home");
            Path storageDir = Paths.get(userHome, ".ichat", "documents");
            Files.createDirectories(storageDir);
            return storageDir;
        } catch (Exception e) {
            System.err.println("❌ Error creating storage directory: " + e.getMessage());
            // Fallback to temp directory
            return Paths.get(System.getProperty("java.io.tmpdir"), "ichat_documents");
        }
    }

    /**
     * Loads document metadata from file (simplified JSON parsing)
     */
    private Map<String, DocumentMetadata> loadDocumentMetadata() {
        try {
            if (Files.exists(metadataFile)) {
                String content = Files.readString(metadataFile, StandardCharsets.UTF_8);
                return parseDocumentMetadataJson(content);
            }
        } catch (Exception e) {
            System.err.println("⚠️ Error loading document metadata: " + e.getMessage());
        }
        return new HashMap<>();
    }

    /**
     * Saves document metadata to file (simplified JSON generation)
     */
    private void saveDocumentMetadata() {
        try {
            String json = generateDocumentMetadataJson(documentMetadataMap);
            Files.writeString(metadataFile, json, StandardCharsets.UTF_8);
        } catch (Exception e) {
            System.err.println("❌ Error saving document metadata: " + e.getMessage());
        }
    }

    /**
     * Uploads document to server for embedding and returns document ID
     */
    private String uploadDocumentForEmbedding(File file, String title, String author, String category) throws IOException {
        URL url = new URL(apiBaseUrl + "/documents/embed");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();

        try {
            // Configure the connection for multipart form data
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", IChatConfig.USER_AGENT);
            connection.setDoOutput(true);
            connection.setConnectTimeout(IChatConfig.CONNECTION_TIMEOUT);
            connection.setReadTimeout(120000); // 2 minutes for embedding processing

            // Create multipart form data
            try (OutputStream os = connection.getOutputStream();
                 PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, StandardCharsets.UTF_8), true)) {

                // Add file part
                addFilePart(writer, os, "file", file);

                // Add metadata parts
                addFormField(writer, "title", title != null ? title : file.getName());
                addFormField(writer, "author", author != null ? author : "Unknown");
                addFormField(writer, "category", category != null ? category : "General");

                // End of multipart/form-data
                writer.append("--").append(BOUNDARY).append("--").append("\r\n");
            }

            // Get the response
            int responseCode = connection.getResponseCode();
            System.out.println("📊 Embedding Response Code: " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                // Read successful response
                try (Scanner scanner = new Scanner(connection.getInputStream(), StandardCharsets.UTF_8)) {
                    String response = scanner.useDelimiter("\\A").next();
                    System.out.println("✅ Embedding Response: " + response);
                    return parseDocumentId(response);
                }
            } else {
                // Read error response
                String errorResponse = "";
                try (Scanner scanner = new Scanner(connection.getErrorStream(), StandardCharsets.UTF_8)) {
                    errorResponse = scanner.useDelimiter("\\A").next();
                } catch (Exception e) {
                    errorResponse = "Unknown error";
                }
                throw new IOException("Embedding failed (" + responseCode + "): " + errorResponse);
            }

        } finally {
            connection.disconnect();
        }
    }

    /**
     * Stores document locally and returns the local path
     */
    private String storeDocumentLocally(File file, String documentId) throws IOException {
        String filename = documentId + "_" + file.getName();
        Path localPath = storageDirectory.resolve(filename);
        Files.copy(file.toPath(), localPath, StandardCopyOption.REPLACE_EXISTING);
        return localPath.toString();
    }

    /**
     * Sets context on the server
     */
    private boolean setServerContext(List<String> documentIds, String sessionId) throws IOException {
        URL url = new URL(apiBaseUrl + "/chat/set-context");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();

        try {
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", IChatConfig.USER_AGENT);
            connection.setDoOutput(true);
            connection.setConnectTimeout(IChatConfig.CONNECTION_TIMEOUT);
            connection.setReadTimeout(IChatConfig.READ_TIMEOUT);

            // Create JSON payload (simple string construction)
            StringBuilder jsonBuilder = new StringBuilder();
            jsonBuilder.append("{");
            jsonBuilder.append("\"document_ids\":[");
            for (int i = 0; i < documentIds.size(); i++) {
                if (i > 0) jsonBuilder.append(",");
                jsonBuilder.append("\"").append(escapeJson(documentIds.get(i))).append("\"");
            }
            jsonBuilder.append("],");
            jsonBuilder.append("\"client_id\":\"").append(escapeJson(IChatConfig.CLIENT_ID)).append("\",");
            jsonBuilder.append("\"session_id\":\"").append(escapeJson(sessionId)).append("\"");
            jsonBuilder.append("}");

            String jsonPayload = jsonBuilder.toString();
            System.out.println("📋 Context Payload: " + jsonPayload);

            // Send the request
            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonPayload.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            // Get the response
            int responseCode = connection.getResponseCode();
            return responseCode == HttpURLConnection.HTTP_OK;

        } finally {
            connection.disconnect();
        }
    }

    /**
     * Clears context on the server
     */
    private boolean clearServerContext(String sessionId) throws IOException {
        URL url = new URL(apiBaseUrl + "/chat/clear-context");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();

        try {
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", IChatConfig.USER_AGENT);
            connection.setDoOutput(true);
            connection.setConnectTimeout(IChatConfig.CONNECTION_TIMEOUT);
            connection.setReadTimeout(IChatConfig.READ_TIMEOUT);

            // Create JSON payload (simple string construction)
            String jsonPayload = "{" +
                "\"client_id\":\"" + escapeJson(IChatConfig.CLIENT_ID) + "\"," +
                "\"session_id\":\"" + escapeJson(sessionId) + "\"" +
                "}";

            // Send the request
            try (OutputStream os = connection.getOutputStream()) {
                byte[] input = jsonPayload.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }

            // Get the response
            int responseCode = connection.getResponseCode();
            return responseCode == HttpURLConnection.HTTP_OK;

        } finally {
            connection.disconnect();
        }
    }

    /**
     * Utility methods for file handling and parsing
     */
    private void addFormField(PrintWriter writer, String name, String value) {
        writer.append("--").append(BOUNDARY).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(name).append("\"").append("\r\n");
        writer.append("Content-Type: text/plain; charset=UTF-8").append("\r\n");
        writer.append("\r\n");
        writer.append(value).append("\r\n");
    }

    private void addFilePart(PrintWriter writer, OutputStream outputStream, String fieldName, File file) throws IOException {
        String fileName = file.getName();
        writer.append("--").append(BOUNDARY).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(fieldName).append("\"; filename=\"").append(fileName).append("\"").append("\r\n");
        writer.append("Content-Type: ").append(getContentType(fileName)).append("\r\n");
        writer.append("Content-Transfer-Encoding: binary").append("\r\n");
        writer.append("\r\n");
        writer.flush();

        Files.copy(file.toPath(), outputStream);
        outputStream.flush();

        writer.append("\r\n");
        writer.flush();
    }

    private String getContentType(String fileName) {
        String extension = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase();
        switch (extension) {
            case "pdf": return "application/pdf";
            case "docx": return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "png": return "image/png";
            case "jpg":
            case "jpeg": return "image/jpeg";
            case "bmp": return "image/bmp";
            case "tiff": return "image/tiff";
            case "webp": return "image/webp";
            default: return "application/octet-stream";
        }
    }

    private String parseDocumentId(String response) {
        try {
            // Simple JSON parsing for document_id
            // Try to get document_id from client_storage_info first
            String storageInfoPattern = "\"client_storage_info\"\\s*:\\s*\\{[^}]*\"document_id\"\\s*:\\s*\"([^\"]+)\"";
            java.util.regex.Pattern pattern = java.util.regex.Pattern.compile(storageInfoPattern);
            java.util.regex.Matcher matcher = pattern.matcher(response);

            if (matcher.find()) {
                return matcher.group(1);
            }

            // Fallback to direct document_id field
            String directPattern = "\"document_id\"\\s*:\\s*\"([^\"]+)\"";
            pattern = java.util.regex.Pattern.compile(directPattern);
            matcher = pattern.matcher(response);

            if (matcher.find()) {
                return matcher.group(1);
            }

        } catch (Exception e) {
            System.err.println("⚠️ Error parsing document ID: " + e.getMessage());
        }
        return null;
    }

    private boolean hasStorageSpace(long requiredBytes) {
        return getCurrentStorageSize() + requiredBytes <= MAX_STORAGE_SIZE;
    }

    private long getCurrentStorageSize() {
        return documentMetadataMap.values().stream()
            .mapToLong(metadata -> metadata.fileSize)
            .sum();
    }

    private long getRemainingStorageSpace() {
        return MAX_STORAGE_SIZE - getCurrentStorageSize();
    }

    private String formatBytes(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        if (bytes < 1024 * 1024 * 1024) return String.format("%.1f MB", bytes / (1024.0 * 1024.0));
        return String.format("%.1f GB", bytes / (1024.0 * 1024.0 * 1024.0));
    }

    /**
     * Simple JSON utility methods
     */
    private String escapeJson(String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\")
                   .replace("\"", "\\\"")
                   .replace("\n", "\\n")
                   .replace("\r", "\\r")
                   .replace("\t", "\\t");
    }

    private String generateDocumentMetadataJson(Map<String, DocumentMetadata> metadataMap) {
        StringBuilder json = new StringBuilder();
        json.append("{");

        boolean first = true;
        for (Map.Entry<String, DocumentMetadata> entry : metadataMap.entrySet()) {
            if (!first) json.append(",");
            first = false;

            DocumentMetadata metadata = entry.getValue();
            json.append("\"").append(escapeJson(entry.getKey())).append("\":{");
            json.append("\"documentId\":\"").append(escapeJson(metadata.documentId)).append("\",");
            json.append("\"filename\":\"").append(escapeJson(metadata.filename)).append("\",");
            json.append("\"title\":\"").append(escapeJson(metadata.title)).append("\",");
            json.append("\"author\":\"").append(escapeJson(metadata.author)).append("\",");
            json.append("\"category\":\"").append(escapeJson(metadata.category)).append("\",");
            json.append("\"uploadDate\":").append(metadata.uploadDate).append(",");
            json.append("\"fileSize\":").append(metadata.fileSize).append(",");
            json.append("\"storageKey\":\"").append(escapeJson(metadata.storageKey)).append("\",");
            json.append("\"localPath\":\"").append(escapeJson(metadata.localPath)).append("\",");
            json.append("\"contentType\":\"").append(escapeJson(metadata.contentType)).append("\"");
            json.append("}");
        }

        json.append("}");
        return json.toString();
    }

    private Map<String, DocumentMetadata> parseDocumentMetadataJson(String json) {
        Map<String, DocumentMetadata> result = new HashMap<>();

        try {
            // Simple regex-based JSON parsing for our specific structure
            String pattern = "\"([^\"]+)\"\\s*:\\s*\\{([^}]+)\\}";
            java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern);
            java.util.regex.Matcher m = p.matcher(json);

            while (m.find()) {
                String key = m.group(1);
                String metadataJson = m.group(2);

                DocumentMetadata metadata = parseDocumentMetadata(metadataJson);
                if (metadata != null) {
                    result.put(key, metadata);
                }
            }
        } catch (Exception e) {
            System.err.println("⚠️ Error parsing metadata JSON: " + e.getMessage());
        }

        return result;
    }

    private DocumentMetadata parseDocumentMetadata(String metadataJson) {
        try {
            DocumentMetadata metadata = new DocumentMetadata();

            metadata.documentId = extractJsonString(metadataJson, "documentId");
            metadata.filename = extractJsonString(metadataJson, "filename");
            metadata.title = extractJsonString(metadataJson, "title");
            metadata.author = extractJsonString(metadataJson, "author");
            metadata.category = extractJsonString(metadataJson, "category");
            metadata.storageKey = extractJsonString(metadataJson, "storageKey");
            metadata.localPath = extractJsonString(metadataJson, "localPath");
            metadata.contentType = extractJsonString(metadataJson, "contentType");

            metadata.uploadDate = extractJsonLong(metadataJson, "uploadDate");
            metadata.fileSize = extractJsonLong(metadataJson, "fileSize");

            return metadata;
        } catch (Exception e) {
            System.err.println("⚠️ Error parsing document metadata: " + e.getMessage());
            return null;
        }
    }

    private String extractJsonString(String json, String key) {
        String pattern = "\"" + key + "\"\\s*:\\s*\"([^\"]+)\"";
        java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern);
        java.util.regex.Matcher m = p.matcher(json);
        return m.find() ? m.group(1) : "";
    }

    private long extractJsonLong(String json, String key) {
        String pattern = "\"" + key + "\"\\s*:\\s*(\\d+)";
        java.util.regex.Pattern p = java.util.regex.Pattern.compile(pattern);
        java.util.regex.Matcher m = p.matcher(json);
        return m.find() ? Long.parseLong(m.group(1)) : 0L;
    }

    /**
     * Shuts down the executor service
     */
    public void shutdown() {
        executor.shutdown();
        System.out.println("🛑 Client Document Storage Service shutdown");
    }
}
