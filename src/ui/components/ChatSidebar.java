package ui.components;

import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ScrollPane;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;
import javafx.stage.FileChooser;
import javafx.stage.Screen;
import javafx.stage.Stage;
import ui.styles.SidebarStyles;
import api.IChatApiService;
import api.DocumentUploadService;
import config.IChatConfig;
import java.io.File;

/**
 * Chat sidebar component that provides the main chat interface.
 * Features a modern design with header, chat area, and input controls.
 */
public class ChatSidebar {

    private Stage sidebarStage;
    private boolean isVisible = false;
    private TextArea chatArea;
    private Runnable onCloseCallback;
    private IChatApiService apiService;
    private DocumentUploadService documentService;

    /**
     * Constructor - initializes the API service with configured URL
     */
    public ChatSidebar() {
        String apiUrl = IChatConfig.getApiUrl();
        this.apiService = new IChatApiService(apiUrl);
        this.documentService = new DocumentUploadService();
        System.out.println("✅ ChatSidebar initialized with API service and document upload service");

        // Print configuration for debugging
        IChatConfig.printConfig();
    }

    /**
     * Constructor with custom API URL
     */
    public ChatSidebar(String apiUrl) {
        this.apiService = new IChatApiService(apiUrl);
        System.out.println("✅ ChatSidebar initialized with custom API URL: " + apiUrl);
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
            // Re-position on target screen and bring to front
            positionSidebarOnScreen(targetScreen);
            sidebarStage.toFront();
            sidebarStage.requestFocus();
            return;
        }

        if (sidebarStage == null) {
            System.out.println("🏗️ Creating new sidebar stage...");
            createSidebar();
        }

        System.out.println("📍 Positioning sidebar on target screen...");
        // Position on target screen before showing
        positionSidebarOnScreen(targetScreen);

        System.out.println("👀 Showing sidebar stage...");
        sidebarStage.show();
        sidebarStage.toFront();
        sidebarStage.requestFocus();

        isVisible = true;

        System.out.println("✅ Sidebar shown on target screen: " + targetScreen.getBounds());
    }

    /**
     * Shows the sidebar with an optional close callback
     */
    public void show(Runnable onCloseCallback) {
        this.onCloseCallback = onCloseCallback;

        if (sidebarStage != null && isVisible) {
            // Re-position on active screen and bring to front
            positionSidebar();
            sidebarStage.toFront();
            sidebarStage.requestFocus();
            return;
        }

        if (sidebarStage == null) {
            createSidebar();
        }

        // Position on active screen before showing
        positionSidebar();

        sidebarStage.show();
        sidebarStage.toFront();
        sidebarStage.requestFocus();

        isVisible = true;

        System.out.println("✅ Sidebar shown on active screen");
    }
    
    /**
     * Hides the sidebar and triggers the close callback
     */
    public void hide() {
        if (sidebarStage != null) {
            sidebarStage.hide();
            isVisible = false;

            // Call the callback to show the Ask button again
            if (onCloseCallback != null) {
                onCloseCallback.run();
                onCloseCallback = null;
            }
        }
    }
    
    /**
     * Creates and configures the sidebar stage
     */
    private void createSidebar() {
        sidebarStage = new Stage();
        sidebarStage.setTitle("iChat Assistant");
        sidebarStage.setAlwaysOnTop(true);
        sidebarStage.setResizable(true); // Allow resizing

        // Create sidebar content
        VBox content = createSidebarContent();

        // Create scene with CSS styling - initial size
        Scene scene = new Scene(content, 380, 650);
        scene.getStylesheets().add("data:text/css," + SidebarStyles.getSidebarCSS());

        sidebarStage.setScene(scene);

        // Set minimum and maximum size constraints
        sidebarStage.setMinWidth(320);  // Minimum width for usability
        sidebarStage.setMinHeight(400); // Minimum height for usability
        sidebarStage.setMaxWidth(800);  // Maximum width to prevent too wide
        sidebarStage.setMaxHeight(1200); // Maximum height for very tall screens

        positionSidebar();
        setupCloseHandler();
        setupResizeHandlers();
    }
    
    /**
     * Positions the sidebar on the active screen (where user is currently working)
     */
    private void positionSidebar() {
        try {
            // Get the active screen based on mouse position
            Screen activeScreen = getActiveScreen();

            double screenWidth = activeScreen.getVisualBounds().getWidth();
            double screenHeight = activeScreen.getVisualBounds().getHeight();
            double screenMinX = activeScreen.getVisualBounds().getMinX();
            double screenMinY = activeScreen.getVisualBounds().getMinY();

            // Position on right side of active screen
            double sidebarWidth = sidebarStage.getWidth() > 0 ? sidebarStage.getWidth() : 380;
            double sidebarHeight = sidebarStage.getHeight() > 0 ? sidebarStage.getHeight() : 650;
            double rightMargin = 20;
            double topMargin = 50;

            double x = screenMinX + screenWidth - sidebarWidth - rightMargin;
            double y = screenMinY + topMargin;

            // Ensure sidebar fits within screen bounds
            if (y + sidebarHeight > screenMinY + screenHeight) {
                y = screenMinY + screenHeight - sidebarHeight - 20;
            }

            System.out.println("Positioning sidebar on screen: " + activeScreen.getBounds());
            System.out.println("Sidebar position: x=" + x + ", y=" + y);

            sidebarStage.setX(x);
            sidebarStage.setY(y);

        } catch (Exception e) {
            System.err.println("Error positioning sidebar: " + e.getMessage());
            // Fallback to primary screen
            positionOnPrimaryScreen();
        }
    }

    /**
     * Gets the screen where the user is currently active (based on mouse position)
     */
    private Screen getActiveScreen() {
        try {
            // Get current mouse position
            java.awt.Point mouseLocation = java.awt.MouseInfo.getPointerInfo().getLocation();
            double mouseX = mouseLocation.getX();
            double mouseY = mouseLocation.getY();

            System.out.println("Mouse position: x=" + mouseX + ", y=" + mouseY);

            // Find which screen contains the mouse
            for (Screen screen : Screen.getScreens()) {
                javafx.geometry.Rectangle2D bounds = screen.getBounds();
                if (bounds.contains(mouseX, mouseY)) {
                    System.out.println("Found active screen: " + bounds);
                    return screen;
                }
            }

            // If mouse not found on any screen, try visual bounds
            for (Screen screen : Screen.getScreens()) {
                javafx.geometry.Rectangle2D bounds = screen.getVisualBounds();
                if (bounds.contains(mouseX, mouseY)) {
                    System.out.println("Found active screen (visual): " + bounds);
                    return screen;
                }
            }

        } catch (Exception e) {
            System.err.println("Error detecting active screen: " + e.getMessage());
        }

        // Fallback to primary screen
        System.out.println("Falling back to primary screen");
        return Screen.getPrimary();
    }

    /**
     * Positions the sidebar on a specific screen
     */
    private void positionSidebarOnScreen(Screen targetScreen) {
        try {
            System.out.println("🎯 Positioning sidebar on screen: " + targetScreen.getBounds());
            System.out.println("📐 Visual bounds: " + targetScreen.getVisualBounds());

            double screenWidth = targetScreen.getVisualBounds().getWidth();
            double screenHeight = targetScreen.getVisualBounds().getHeight();
            double screenMinX = targetScreen.getVisualBounds().getMinX();
            double screenMinY = targetScreen.getVisualBounds().getMinY();

            System.out.println("📊 Screen dimensions: " + screenWidth + "x" + screenHeight + " at (" + screenMinX + "," + screenMinY + ")");

            // Position on right side of target screen
            double sidebarWidth = sidebarStage.getWidth() > 0 ? sidebarStage.getWidth() : 380;
            double sidebarHeight = sidebarStage.getHeight() > 0 ? sidebarStage.getHeight() : 650;
            double rightMargin = 20;
            double topMargin = 50;

            double x = screenMinX + screenWidth - sidebarWidth - rightMargin;
            double y = screenMinY + topMargin;

            // Ensure sidebar fits within screen bounds
            if (y + sidebarHeight > screenMinY + screenHeight) {
                y = screenMinY + screenHeight - sidebarHeight - 20;
                System.out.println("⚠️ Adjusted Y position to fit screen: " + y);
            }

            System.out.println("📍 Final sidebar position: x=" + x + ", y=" + y);

            sidebarStage.setX(x);
            sidebarStage.setY(y);

            System.out.println("✅ Sidebar positioned successfully");

        } catch (Exception e) {
            System.err.println("❌ Error positioning sidebar on target screen: " + e.getMessage());
            e.printStackTrace();
            // Fallback to primary screen
            positionOnPrimaryScreen();
        }
    }

    /**
     * Fallback method to position on primary screen
     */
    private void positionOnPrimaryScreen() {
        Screen primaryScreen = Screen.getPrimary();
        double screenWidth = primaryScreen.getVisualBounds().getWidth();
        double screenMinX = primaryScreen.getVisualBounds().getMinX();
        double screenMinY = primaryScreen.getVisualBounds().getMinY();

        double sidebarWidth = sidebarStage != null && sidebarStage.getWidth() > 0 ? sidebarStage.getWidth() : 380;
        double rightMargin = 20;
        double topMargin = 50;

        double x = screenMinX + screenWidth - sidebarWidth - rightMargin;
        double y = screenMinY + topMargin;

        sidebarStage.setX(x);
        sidebarStage.setY(y);
    }
    
    /**
     * Sets up the close event handler
     */
    private void setupCloseHandler() {
        sidebarStage.setOnCloseRequest(e -> {
            hide(); // Use hide() method to trigger callback
        });
    }

    /**
     * Sets up resize event handlers to provide user feedback
     */
    private void setupResizeHandlers() {
        // Add resize feedback
        sidebarStage.widthProperty().addListener((obs, oldWidth, newWidth) -> {
            if (isVisible && newWidth.doubleValue() > 0) {
                System.out.println("📏 Sidebar width changed to: " + Math.round(newWidth.doubleValue()) + "px");
            }
        });

        sidebarStage.heightProperty().addListener((obs, oldHeight, newHeight) -> {
            if (isVisible && newHeight.doubleValue() > 0) {
                System.out.println("📏 Sidebar height changed to: " + Math.round(newHeight.doubleValue()) + "px");
            }
        });
    }
    
    /**
     * Creates the main sidebar content structure
     */
    private VBox createSidebarContent() {
        VBox content = new VBox();
        content.getStyleClass().add("sidebar-content");

        // Create main sections
        VBox headerSection = createHeaderSection();
        ScrollPane chatScrollPane = createChatArea();
        VBox inputSection = createInputSection();

        // Add all sections to main content
        content.getChildren().addAll(headerSection, chatScrollPane, inputSection);

        return content;
    }
    
    /**
     * Creates the header section with title and subtitle
     */
    private VBox createHeaderSection() {
        VBox headerSection = new VBox(3);
        headerSection.setPadding(new Insets(20, 25, 15, 25));
        headerSection.getStyleClass().add("header-section");

        Label headerLabel = new Label("💬 iChat Assistant");
        headerLabel.getStyleClass().add("sidebar-header");

        Label subtitleLabel = new Label("Your AI-powered chat companion • Resizable");
        subtitleLabel.getStyleClass().add("sidebar-subtitle");

        headerSection.getChildren().addAll(headerLabel, subtitleLabel);
        return headerSection;
    }
    
    /**
     * Creates the scrollable chat area
     */
    private ScrollPane createChatArea() {
        chatArea = new TextArea();
        chatArea.setEditable(false);
        chatArea.setWrapText(true);
        chatArea.getStyleClass().add("chat-area");
        chatArea.setText("👋 Welcome to iChat Assistant!\n\n✨ I'm here to help you with any questions or tasks you might have. Feel free to start a conversation!");

        ScrollPane chatScrollPane = new ScrollPane(chatArea);
        chatScrollPane.setFitToWidth(true);
        chatScrollPane.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        chatScrollPane.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        chatScrollPane.getStyleClass().add("chat-scroll");

        // Set margins for chat area
        VBox.setMargin(chatScrollPane, new Insets(0, 25, 15, 25));

        // Make chat area grow to fill available space
        VBox.setVgrow(chatScrollPane, Priority.ALWAYS);
        
        return chatScrollPane;
    }
    
    /**
     * Creates the input section with message input and action buttons
     */
    private VBox createInputSection() {
        VBox inputSection = new VBox(10);
        inputSection.setPadding(new Insets(10, 25, 20, 25));
        inputSection.getStyleClass().add("input-section");

        HBox inputArea = createInputArea();
        HBox actionButtons = createActionButtons();

        inputSection.getChildren().addAll(inputArea, actionButtons);
        return inputSection;
    }
    
    /**
     * Creates the message input area with text field, upload button, and send button
     */
    private HBox createInputArea() {
        HBox inputArea = new HBox(8);
        inputArea.setAlignment(Pos.CENTER);
        inputArea.getStyleClass().add("input-container");

        TextField messageInput = new TextField();
        messageInput.setPromptText("💭 Type your message here...");
        messageInput.getStyleClass().add("message-input");
        HBox.setHgrow(messageInput, Priority.ALWAYS);

        // Small upload button
        Button uploadButton = new Button("📎");
        uploadButton.getStyleClass().add("upload-button");
        uploadButton.setOnAction(e -> handleDocumentUpload());

        Button sendButton = new Button("🚀 Send");
        sendButton.getStyleClass().add("send-button");

        // Send message functionality with API integration
        Runnable sendMessage = () -> {
            String message = messageInput.getText().trim();
            if (!message.isEmpty()) {
                // Add user message to chat
                addMessage("You", message);
                messageInput.clear();

                // Show typing indicator
                addMessage("Assistant", "💭 Thinking...");

                // Send message to API asynchronously
                apiService.sendMessage(message)
                    .thenAccept(response -> {
                        // Update UI on JavaFX Application Thread
                        Platform.runLater(() -> {
                            // Remove typing indicator (last message)
                            removeLastMessage();
                            // Add actual response
                            addMessage("Assistant", response);
                        });
                    })
                    .exceptionally(throwable -> {
                        // Handle errors on JavaFX Application Thread
                        Platform.runLater(() -> {
                            // Remove typing indicator
                            removeLastMessage();
                            // Add error message
                            addMessage("Assistant", "Sorry, I encountered an error: " + throwable.getMessage() + " 😔");
                        });
                        return null;
                    });
            }
        };

        sendButton.setOnAction(e -> sendMessage.run());
        messageInput.setOnAction(e -> sendMessage.run());

        inputArea.getChildren().addAll(messageInput, uploadButton, sendButton);
        return inputArea;
    }
    
    /**
     * Creates the action buttons (Clear, Resize Info, and Close)
     */
    private HBox createActionButtons() {
        HBox actionButtons = new HBox(8);
        actionButtons.setAlignment(Pos.CENTER);

        Button clearButton = new Button("🗑️ Clear");
        clearButton.getStyleClass().add("action-button");
        clearButton.setOnAction(e -> {
            chatArea.setText("👋 Welcome to iChat Assistant!\n\n✨ I'm here to help you with any questions or tasks you might have. Feel free to start a conversation!\n\n📏 Tip: You can resize this window by dragging the edges or corners!");
        });

        Button resizeInfoButton = new Button("📏 Resize");
        resizeInfoButton.getStyleClass().add("action-button");
        resizeInfoButton.setOnAction(e -> {
            double currentWidth = Math.round(sidebarStage.getWidth());
            double currentHeight = Math.round(sidebarStage.getHeight());
            addMessage("System", "📏 Current size: " + currentWidth + "×" + currentHeight + "px\n\n💡 Drag the window edges to resize!\n• Min: 320×400px\n• Max: 800×1200px");
        });

        Button closeButton = new Button("✖️ Close");
        closeButton.getStyleClass().add("close-button");
        closeButton.setOnAction(e -> hide());

        actionButtons.getChildren().addAll(clearButton, resizeInfoButton, closeButton);
        return actionButtons;
    }
    
    /**
     * Adds a message to the chat area
     */
    private void addMessage(String sender, String message) {
        chatArea.appendText("\n\n" + sender + ": " + message);
        chatArea.setScrollTop(Double.MAX_VALUE);
    }

    /**
     * Removes the last message from the chat area (used to remove typing indicator)
     */
    private void removeLastMessage() {
        String currentText = chatArea.getText();
        int lastMessageIndex = currentText.lastIndexOf("\n\n");
        if (lastMessageIndex > 0) {
            chatArea.setText(currentText.substring(0, lastMessageIndex));
        }
    }

    /**
     * Handles document upload functionality
     */
    private void handleDocumentUpload() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Select Document for OCR Processing");

        // Set file extension filters
        fileChooser.getExtensionFilters().addAll(
            new FileChooser.ExtensionFilter("All Supported", "*.pdf", "*.docx", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp"),
            new FileChooser.ExtensionFilter("PDF Documents", "*.pdf"),
            new FileChooser.ExtensionFilter("Word Documents", "*.docx"),
            new FileChooser.ExtensionFilter("Images", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.webp")
        );

        File selectedFile = fileChooser.showOpenDialog(sidebarStage);

        if (selectedFile != null) {
            // Check if file is supported
            if (!documentService.isSupportedFile(selectedFile)) {
                addMessage("System", "❌ Unsupported file type. Supported formats: " + documentService.getSupportedExtensions());
                return;
            }

            // Add upload message
            addMessage("You", "📎 Uploading document: " + selectedFile.getName());
            addMessage("Assistant", "⏳ Processing your document with OCR... Please wait.");

            // Upload document asynchronously
            documentService.uploadDocument(selectedFile, "text", "en")
                .thenAccept(response -> {
                    // Update UI on JavaFX Application Thread
                    Platform.runLater(() -> {
                        // Remove processing message
                        removeLastMessage();
                        // Add OCR result
                        addMessage("Assistant", response);
                    });
                })
                .exceptionally(throwable -> {
                    // Handle errors on JavaFX Application Thread
                    Platform.runLater(() -> {
                        // Remove processing message
                        removeLastMessage();
                        // Add error message
                        addMessage("Assistant", "Sorry, I encountered an error processing your document: " + throwable.getMessage() + " 😔");
                    });
                    return null;
                });
        }
    }

    /**
     * Cleanup method to shutdown API service
     */
    public void cleanup() {
        if (apiService != null) {
            apiService.shutdown();
        }
        if (documentService != null) {
            documentService.shutdown();
        }
    }
}
