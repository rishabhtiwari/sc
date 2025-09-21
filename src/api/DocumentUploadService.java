package api;

import config.IChatConfig;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Scanner;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Service class for uploading documents to the iChat OCR service
 */
public class DocumentUploadService {

    private final String documentApiUrl;
    private final ExecutorService executor;
    private static final String BOUNDARY = "----WebKitFormBoundary" + System.currentTimeMillis();

    /**
     * Constructor with default API URL from configuration
     */
    public DocumentUploadService() {
        // Use the document upload endpoint
        String baseUrl = IChatConfig.getApiUrl().replace("/api/chat", "");
        this.documentApiUrl = baseUrl + "/api/documents/upload";
        this.executor = Executors.newFixedThreadPool(2);
        System.out.println("✅ Document Upload Service initialized with URL: " + documentApiUrl);
    }

    /**
     * Uploads a document file asynchronously
     * @param file The file to upload
     * @param outputFormat The desired output format (text, json, markdown)
     * @param language The OCR language (en, ch, fr, german, korean, japan)
     * @return CompletableFuture with the OCR result
     */
    public CompletableFuture<String> uploadDocument(File file, String outputFormat, String language) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                System.out.println("📤 Uploading document: " + file.getName());
                return uploadDocumentSync(file, outputFormat, language);
            } catch (Exception e) {
                System.err.println("❌ Error uploading document: " + e.getMessage());
                return "Sorry, I encountered an error while processing your document: " + e.getMessage() + " 😔";
            }
        }, executor);
    }

    /**
     * Uploads a document file synchronously
     * @param file The file to upload
     * @param outputFormat The desired output format
     * @param language The OCR language
     * @return The OCR result
     * @throws IOException if the request fails
     */
    private String uploadDocumentSync(File file, String outputFormat, String language) throws IOException {
        URL url = new URL(documentApiUrl);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();

        try {
            // Configure the connection for multipart form data
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + BOUNDARY);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("User-Agent", IChatConfig.USER_AGENT);
            connection.setDoOutput(true);
            connection.setConnectTimeout(IChatConfig.CONNECTION_TIMEOUT);
            connection.setReadTimeout(120000); // 2 minutes for OCR processing

            // Create multipart form data
            try (OutputStream os = connection.getOutputStream();
                 PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, StandardCharsets.UTF_8), true)) {

                // Add file part
                addFilePart(writer, os, "file", file);

                // Add output format part
                addFormField(writer, "output_format", outputFormat != null ? outputFormat : "text");

                // Add language part
                addFormField(writer, "language", language != null ? language : "en");

                // End of multipart/form-data
                writer.append("--").append(BOUNDARY).append("--").append("\r\n");
            }

            // Get the response
            int responseCode = connection.getResponseCode();
            System.out.println("📊 Upload Response Code: " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                // Read successful response
                try (Scanner scanner = new Scanner(connection.getInputStream(), StandardCharsets.UTF_8)) {
                    String response = scanner.useDelimiter("\\A").next();
                    System.out.println("✅ Upload Response: " + response);
                    return parseDocumentResponse(response);
                }
            } else {
                // Read error response
                String errorResponse = "";
                try (Scanner scanner = new Scanner(connection.getErrorStream(), StandardCharsets.UTF_8)) {
                    errorResponse = scanner.useDelimiter("\\A").next();
                } catch (Exception e) {
                    errorResponse = "Unknown error";
                }

                System.err.println("❌ Upload Error (" + responseCode + "): " + errorResponse);
                return "Sorry, the document upload failed (" + responseCode + "). Please try again. 🔄";
            }

        } finally {
            connection.disconnect();
        }
    }

    /**
     * Adds a form field to the multipart request
     */
    private void addFormField(PrintWriter writer, String name, String value) {
        writer.append("--").append(BOUNDARY).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(name).append("\"").append("\r\n");
        writer.append("Content-Type: text/plain; charset=UTF-8").append("\r\n");
        writer.append("\r\n");
        writer.append(value).append("\r\n");
    }

    /**
     * Adds a file part to the multipart request
     */
    private void addFilePart(PrintWriter writer, OutputStream outputStream, String fieldName, File file) throws IOException {
        String fileName = file.getName();
        writer.append("--").append(BOUNDARY).append("\r\n");
        writer.append("Content-Disposition: form-data; name=\"").append(fieldName).append("\"; filename=\"").append(fileName).append("\"").append("\r\n");
        writer.append("Content-Type: ").append(getContentType(fileName)).append("\r\n");
        writer.append("Content-Transfer-Encoding: binary").append("\r\n");
        writer.append("\r\n");
        writer.flush();

        // Write file content
        Files.copy(file.toPath(), outputStream);
        outputStream.flush();

        writer.append("\r\n");
        writer.flush();
    }

    /**
     * Gets the content type based on file extension
     */
    private String getContentType(String fileName) {
        String extension = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase();
        switch (extension) {
            case "pdf":
                return "application/pdf";
            case "docx":
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "png":
                return "image/png";
            case "jpg":
            case "jpeg":
                return "image/jpeg";
            case "bmp":
                return "image/bmp";
            case "tiff":
                return "image/tiff";
            case "webp":
                return "image/webp";
            default:
                return "application/octet-stream";
        }
    }

    /**
     * Parses the document upload response
     */
    private String parseDocumentResponse(String response) {
        try {
            // Simple JSON parsing for document response
            if (response.contains("\"extracted_text\"")) {
                int start = response.indexOf("\"extracted_text\"") + 17;
                start = response.indexOf("\"", start) + 1;
                int end = response.indexOf("\"", start);

                if (start > 17 && end > start) {
                    String extractedText = response.substring(start, end);
                    // Unescape JSON characters
                    extractedText = extractedText
                        .replace("\\\"", "\"")
                        .replace("\\n", "\n")
                        .replace("\\r", "\r")
                        .replace("\\t", "\t")
                        .replace("\\\\", "\\");
                    
                    return "📄 Document processed successfully!\n\n" + 
                           "📝 Extracted Text:\n" + 
                           "─────────────────\n" + 
                           extractedText;
                }
            }

            // If no extracted_text field, look for message field
            if (response.contains("\"message\"")) {
                int start = response.indexOf("\"message\"") + 10;
                start = response.indexOf("\"", start) + 1;
                int end = response.indexOf("\"", start);

                if (start > 10 && end > start) {
                    String message = response.substring(start, end);
                    return message.replace("\\\"", "\"").replace("\\n", "\n");
                }
            }

            // Return formatted response if no specific field found
            return "📄 Document uploaded successfully!\n\nResponse: " + response;

        } catch (Exception e) {
            System.err.println("⚠️ Error parsing document response: " + e.getMessage());
            return "📄 Document processed, but response format was unexpected:\n\n" + response;
        }
    }

    /**
     * Checks if a file is supported for OCR processing
     */
    public boolean isSupportedFile(File file) {
        if (file == null || !file.exists() || !file.isFile()) {
            return false;
        }

        String fileName = file.getName().toLowerCase();
        return fileName.endsWith(".pdf") || fileName.endsWith(".docx") ||
               fileName.endsWith(".png") || fileName.endsWith(".jpg") ||
               fileName.endsWith(".jpeg") || fileName.endsWith(".bmp") ||
               fileName.endsWith(".tiff") || fileName.endsWith(".webp");
    }

    /**
     * Gets supported file extensions as a string
     */
    public String getSupportedExtensions() {
        return "PDF, DOCX, PNG, JPG, JPEG, BMP, TIFF, WEBP";
    }

    /**
     * Shuts down the executor service
     */
    public void shutdown() {
        executor.shutdown();
        System.out.println("🛑 Document Upload Service shutdown");
    }
}
