package ui.components;

import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Screen;
import javafx.stage.Stage;
import ui.styles.SidebarStyles;
import api.IChatApiService;
import api.ClientDocumentStorageService;
import config.IChatConfig;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Enhanced Chat sidebar with client-side document storage and RAG support.
 * Integrates with the new ClientDocumentStorageService for intelligent document management.
 */
public class EnhancedChatSidebar {

    private Stage sidebarStage;
    private boolean isVisible = false;
    private TextArea chatArea;
    private Runnable onCloseCallback;
    private IChatApiService apiService;
    private ClientDocumentStorageService documentStorageService;
    private String currentSessionId;
    private boolean ragEnabled = false;

    // Simple UI - no complex document management components needed

    /**
     * Constructor - initializes services with configured URL
     */
    public EnhancedChatSidebar() {
        String apiUrl = IChatConfig.getApiUrl();
        this.apiService = new IChatApiService(apiUrl);
        this.documentStorageService = new ClientDocumentStorageService();
        this.currentSessionId = "session_" + UUID.randomUUID().toString().substring(0, 8);
        
        System.out.println("✅ Enhanced ChatSidebar initialized");
        System.out.println("🆔 Session ID: " + currentSessionId);

        // Print configuration for debugging
        IChatConfig.printConfig();
    }

    /**
     * Toggles the sidebar visibility
     */
    public void toggle() {
        if (isVisible) {
            hide();
        } else {
            show();
        }
    }

    /**
     * Toggles the sidebar visibility on a specific screen
     */
    public void toggleOnScreen(Screen targetScreen) {
        System.out.println("🔄 toggleOnScreen called with screen: " + targetScreen.getBounds());
        System.out.println("📊 Current visibility: " + isVisible);

        if (isVisible) {
            System.out.println("🙈 Hiding sidebar...");
            hide();
        } else {
            System.out.println("👁️ Showing sidebar on target screen...");
            showOnScreen(targetScreen);
        }
    }

    /**
     * Shows the sidebar without a callback
     */
    public void show() {
        show(null);
    }

    /**
     * Shows the sidebar on a specific screen
     */
    public void showOnScreen(Screen targetScreen) {
        showOnScreen(targetScreen, null);
    }

    /**
     * Shows the sidebar on a specific screen with callback
     */
    public void showOnScreen(Screen targetScreen, Runnable onCloseCallback) {
        System.out.println("📺 showOnScreen called with target: " + targetScreen.getBounds());
        this.onCloseCallback = onCloseCallback;

        if (sidebarStage != null && isVisible) {
            System.out.println("🔄 Sidebar already visible, repositioning...");
            positionSidebarOnScreen(targetScreen);
            sidebarStage.toFront();
            sidebarStage.requestFocus();
            return;
        }

        if (sidebarStage == null) {
            System.out.println("🏗️ Creating new enhanced sidebar stage...");
            createSidebar();
        }

        System.out.println("📍 Positioning sidebar on target screen...");
        positionSidebarOnScreen(targetScreen);

        System.out.println("👀 Showing enhanced sidebar stage...");
        sidebarStage.show();
        sidebarStage.toFront();
        sidebarStage.requestFocus();

        isVisible = true;

        // Initialize document context on show
        initializeDocumentContext();

        System.out.println("✅ Enhanced Sidebar shown on target screen: " + targetScreen.getBounds());
    }

    /**
     * Shows the sidebar with an optional close callback
     */
    public void show(Runnable onCloseCallback) {
        this.onCloseCallback = onCloseCallback;

        if (sidebarStage != null && isVisible) {
            positionSidebar();
            sidebarStage.toFront();
            sidebarStage.requestFocus();
            return;
        }

        if (sidebarStage == null) {
            createSidebar();
        }

        positionSidebar();
        sidebarStage.show();
        sidebarStage.toFront();
        sidebarStage.requestFocus();

        isVisible = true;

        // Initialize document context on show
        initializeDocumentContext();

        System.out.println("✅ Enhanced Sidebar shown on active screen");
    }

    /**
     * Hides the sidebar and triggers the close callback
     */
    public void hide() {
        if (sidebarStage != null) {
            sidebarStage.hide();
            isVisible = false;

            if (onCloseCallback != null) {
                onCloseCallback.run();
                onCloseCallback = null;
            }
        }
    }

    /**
     * Creates and configures the enhanced sidebar stage
     */
    private void createSidebar() {
        sidebarStage = new Stage();
        sidebarStage.setTitle("iChat Assistant - Enhanced");
        sidebarStage.setAlwaysOnTop(true);
        sidebarStage.setResizable(true);

        // Create enhanced sidebar content
        VBox content = createEnhancedSidebarContent();

        // Create scene with CSS styling - similar size to original
        Scene scene = new Scene(content, 400, 600);
        scene.getStylesheets().add("data:text/css," + SidebarStyles.getSidebarCSS());

        sidebarStage.setScene(scene);

        // Set size constraints similar to original sidebar
        sidebarStage.setMinWidth(350);
        sidebarStage.setMinHeight(400);
        sidebarStage.setMaxWidth(600);
        sidebarStage.setMaxHeight(1000);

        positionSidebar();
        setupCloseHandler();
        setupResizeHandlers();
    }

    /**
     * Creates the simple sidebar content (similar to original ChatSidebar)
     */
    private VBox createEnhancedSidebarContent() {
        VBox content = new VBox();
        content.getStyleClass().add("sidebar-content");

        // Create main sections
        VBox headerSection = createSimpleHeaderSection();
        ScrollPane chatScrollPane = createChatArea();
        VBox inputSection = createInputSection();

        // Set growth priorities
        VBox.setVgrow(chatScrollPane, Priority.ALWAYS);

        // Add all sections to main content
        content.getChildren().addAll(headerSection, chatScrollPane, inputSection);

        return content;
    }

    /**
     * Creates the simple header section (similar to original ChatSidebar)
     */
    private VBox createSimpleHeaderSection() {
        VBox headerSection = new VBox(4);
        headerSection.setPadding(new Insets(20, 20, 16, 20));
        headerSection.getStyleClass().add("header-section");

        Label headerLabel = new Label("iChat Assistant");
        headerLabel.getStyleClass().add("sidebar-header");

        Label subtitleLabel = new Label("Your AI-powered chat companion");
        subtitleLabel.getStyleClass().add("sidebar-subtitle");

        headerSection.getChildren().addAll(headerLabel, subtitleLabel);
        return headerSection;
    }



    /**
     * Creates the chat area
     */
    private ScrollPane createChatArea() {
        chatArea = new TextArea();
        chatArea.setEditable(false);
        chatArea.setWrapText(true);
        chatArea.getStyleClass().add("chat-area");
        updateChatWelcomeMessage();

        ScrollPane chatScrollPane = new ScrollPane(chatArea);
        chatScrollPane.setFitToWidth(true);
        chatScrollPane.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        chatScrollPane.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        chatScrollPane.getStyleClass().add("chat-scroll");

        return chatScrollPane;
    }

    /**
     * Creates the input section
     */
    private VBox createInputSection() {
        VBox inputSection = new VBox(8);

        HBox inputArea = createInputArea();
        inputSection.getChildren().add(inputArea);

        return inputSection;
    }

    /**
     * Creates the message input area
     */
    private HBox createInputArea() {
        HBox inputArea = new HBox(8);
        inputArea.setAlignment(Pos.CENTER);

        TextField messageInput = new TextField();
        messageInput.setPromptText("Type your message here...");
        messageInput.getStyleClass().add("message-input");
        messageInput.setPrefHeight(40);
        HBox.setHgrow(messageInput, Priority.ALWAYS);

        Button menuButton = createMenuButton();
        Button sendButton = new Button("Send");
        sendButton.getStyleClass().add("send-button");

        // Simple send message functionality
        Runnable sendMessage = () -> {
            String message = messageInput.getText().trim();
            if (!message.isEmpty()) {
                addMessage("You", message);
                messageInput.clear();

                addMessage("Assistant", "💭 Thinking...");

                // Send message (RAG will be enabled automatically if documents are uploaded)
                apiService.sendMessage(message, true, currentSessionId)
                    .thenAccept(response -> {
                        Platform.runLater(() -> {
                            removeLastMessage();
                            addMessage("Assistant", response);
                        });
                    })
                    .exceptionally(throwable -> {
                        Platform.runLater(() -> {
                            removeLastMessage();
                            addMessage("Assistant", "Sorry, I encountered an error: " + throwable.getMessage() + " 😔");
                        });
                        return null;
                    });
            }
        };

        sendButton.setOnAction(e -> sendMessage.run());
        messageInput.setOnAction(e -> sendMessage.run());

        inputArea.getChildren().addAll(messageInput, menuButton, sendButton);
        return inputArea;
    }

    /**
     * Creates the simple menu button with only essential actions
     */
    private Button createMenuButton() {
        Button menuButton = new Button("⋯");
        menuButton.getStyleClass().add("upload-button");
        menuButton.setTooltip(new Tooltip("More actions"));

        ContextMenu contextMenu = new ContextMenu();

        MenuItem uploadItem = new MenuItem("📎 Upload Document");
        uploadItem.setOnAction(e -> handleDocumentUpload());

        MenuItem clearChatItem = new MenuItem("🧹 Clear Conversation");
        clearChatItem.setOnAction(e -> clearChat());

        MenuItem closeItem = new MenuItem("❌ Close iChat Assistant");
        closeItem.setOnAction(e -> hide());

        contextMenu.getItems().addAll(uploadItem, clearChatItem, closeItem);

        menuButton.setOnAction(e -> {
            contextMenu.show(menuButton, javafx.geometry.Side.BOTTOM, 0, 0);
        });

        return menuButton;
    }





    /**
     * Event handlers and utility methods
     */
    private void handleDocumentUpload() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Document for Upload and Storage");

        fileChooser.getExtensionFilters().addAll(
            new FileChooser.ExtensionFilter("All Supported", "*.pdf", "*.docx", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp"),
            new FileChooser.ExtensionFilter("PDF Documents", "*.pdf"),
            new FileChooser.ExtensionFilter("Word Documents", "*.docx"),
            new FileChooser.ExtensionFilter("Images", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp")
        );

        File selectedFile = fileChooser.showOpenDialog(sidebarStage);

        if (selectedFile != null) {
            // Show upload dialog for metadata
            showUploadDialog(selectedFile);
        }
    }

    private void showUploadDialog(File file) {
        addMessage("System", "📤 Uploading: " + file.getName());
        addMessage("Assistant", "⏳ Processing and storing your document...");

        // Simple upload with default metadata
        documentStorageService.uploadAndStoreDocument(
            file, file.getName(), "User", "General")
            .thenAccept(metadata -> {
                Platform.runLater(() -> {
                    removeLastMessage();
                    addMessage("Assistant", "✅ Document uploaded successfully!\n" +
                        "📄 " + metadata.title + " is now available for intelligent responses.\n" +
                        "💾 Storage: " + formatFileSize(metadata.fileSize));

                    // Automatically set as context for intelligent responses
                    setDocumentAsContext(metadata.documentId);
                });
            })
            .exceptionally(throwable -> {
                Platform.runLater(() -> {
                    removeLastMessage();
                    addMessage("Assistant", "❌ Upload failed: " + throwable.getMessage());
                });
                return null;
            });
    }

    /**
     * Add a document to the existing session context (preserves existing documents)
     */
    private void setDocumentAsContext(String documentId) {
        System.out.println("🔍 Setting document as context: " + documentId + " for session: " + currentSessionId);

        // Get current context status first
        Map<String, Object> contextStatus = documentStorageService.getContextStatus();
        System.out.println("📊 Current context status: " + contextStatus);

        List<String> existingDocumentIds = (List<String>) contextStatus.get("document_ids");

        // Create new list with existing documents plus the new one
        List<String> documentIds = new ArrayList<>();
        if (existingDocumentIds != null && !existingDocumentIds.isEmpty()) {
            documentIds.addAll(existingDocumentIds);
            System.out.println("📋 Preserving " + existingDocumentIds.size() + " existing documents in context: " + existingDocumentIds);
        } else {
            System.out.println("📋 No existing documents found in context");
        }

        // Add the new document if it's not already in the context
        if (!documentIds.contains(documentId)) {
            documentIds.add(documentId);
            System.out.println("➕ Adding new document to context: " + documentId);
        } else {
            System.out.println("ℹ️ Document already in context: " + documentId);
        }

        System.out.println("📝 Final document list for context: " + documentIds);

        documentStorageService.setSessionContext(documentIds, currentSessionId)
            .thenAccept(success -> {
                if (success) {
                    System.out.println("✅ Document context updated with " + documentIds.size() + " documents");
                } else {
                    System.out.println("⚠️ Failed to update document context");
                }
            });
    }

    private void initializeDocumentContext() {
        // Simple initialization - just ensure storage service is ready
        System.out.println("📁 Document storage initialized and ready");
    }

    private void updateChatWelcomeMessage() {
        String welcomeMessage = "👋 Welcome to iChat Assistant!\n\n" +
            "✨ I'm your AI-powered chat companion.\n\n" +
            "📎 Upload documents using the ⋯ menu for intelligent responses\n" +
            "💬 Ask me anything and I'll help you!\n\n" +
            "Ready to chat! 🚀";

        if (chatArea != null) {
            chatArea.setText(welcomeMessage);
        }
    }

    private void clearChat() {
        updateChatWelcomeMessage();
    }

    private void addMessage(String sender, String message) {
        if (chatArea != null) {
            chatArea.appendText("\n\n" + sender + ": " + message);
            chatArea.setScrollTop(Double.MAX_VALUE);
        }
    }

    private void removeLastMessage() {
        if (chatArea != null) {
            String currentText = chatArea.getText();
            int lastMessageIndex = currentText.lastIndexOf("\n\n");
            if (lastMessageIndex > 0) {
                chatArea.setText(currentText.substring(0, lastMessageIndex));
            }
        }
    }

    private String formatFileSize(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        if (bytes < 1024 * 1024 * 1024) return String.format("%.1f MB", bytes / (1024.0 * 1024.0));
        return String.format("%.1f GB", bytes / (1024.0 * 1024.0 * 1024.0));
    }

    /**
     * Positioning and window management methods (reused from original ChatSidebar)
     */
    private void positionSidebar() {
        try {
            Screen activeScreen = getActiveScreen();
            positionSidebarOnScreen(activeScreen);
        } catch (Exception e) {
            System.err.println("Error positioning sidebar: " + e.getMessage());
            positionOnPrimaryScreen();
        }
    }

    private Screen getActiveScreen() {
        try {
            java.awt.Point mouseLocation = java.awt.MouseInfo.getPointerInfo().getLocation();
            double mouseX = mouseLocation.getX();
            double mouseY = mouseLocation.getY();

            for (Screen screen : Screen.getScreens()) {
                javafx.geometry.Rectangle2D bounds = screen.getBounds();
                if (bounds.contains(mouseX, mouseY)) {
                    return screen;
                }
            }
        } catch (Exception e) {
            System.err.println("Error detecting active screen: " + e.getMessage());
        }
        return Screen.getPrimary();
    }

    private void positionSidebarOnScreen(Screen targetScreen) {
        try {
            double screenWidth = targetScreen.getVisualBounds().getWidth();
            double screenHeight = targetScreen.getVisualBounds().getHeight();
            double screenMinX = targetScreen.getVisualBounds().getMinX();
            double screenMinY = targetScreen.getVisualBounds().getMinY();

            double sidebarWidth = sidebarStage.getWidth() > 0 ? sidebarStage.getWidth() : 400;
            double sidebarHeight = sidebarStage.getHeight() > 0 ? sidebarStage.getHeight() : 600;
            double rightMargin = 20;
            double topMargin = 50;

            double x = screenMinX + screenWidth - sidebarWidth - rightMargin;
            double y = screenMinY + topMargin;

            if (y + sidebarHeight > screenMinY + screenHeight) {
                y = screenMinY + screenHeight - sidebarHeight - 20;
            }

            sidebarStage.setX(x);
            sidebarStage.setY(y);
        } catch (Exception e) {
            System.err.println("Error positioning sidebar on target screen: " + e.getMessage());
            positionOnPrimaryScreen();
        }
    }

    private void positionOnPrimaryScreen() {
        Screen primaryScreen = Screen.getPrimary();
        double screenWidth = primaryScreen.getVisualBounds().getWidth();
        double screenMinX = primaryScreen.getVisualBounds().getMinX();
        double screenMinY = primaryScreen.getVisualBounds().getMinY();

        double sidebarWidth = sidebarStage != null && sidebarStage.getWidth() > 0 ? sidebarStage.getWidth() : 400;
        double rightMargin = 20;
        double topMargin = 50;

        double x = screenMinX + screenWidth - sidebarWidth - rightMargin;
        double y = screenMinY + topMargin;

        sidebarStage.setX(x);
        sidebarStage.setY(y);
    }

    private void setupCloseHandler() {
        sidebarStage.setOnCloseRequest(e -> hide());
    }

    private void setupResizeHandlers() {
        sidebarStage.widthProperty().addListener((obs, oldWidth, newWidth) -> {
            if (isVisible && newWidth.doubleValue() > 0) {
                System.out.println("📏 Enhanced Sidebar width: " + Math.round(newWidth.doubleValue()) + "px");
            }
        });

        sidebarStage.heightProperty().addListener((obs, oldHeight, newHeight) -> {
            if (isVisible && newHeight.doubleValue() > 0) {
                System.out.println("📏 Enhanced Sidebar height: " + Math.round(newHeight.doubleValue()) + "px");
            }
        });
    }

    /**
     * Cleanup method
     */
    public void cleanup() {
        if (apiService != null) {
            apiService.shutdown();
        }
        if (documentStorageService != null) {
            documentStorageService.shutdown();
        }
    }
}
