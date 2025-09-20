package ui.components;

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
import javafx.stage.Screen;
import javafx.stage.Stage;
import ui.styles.SidebarStyles;

/**
 * Chat sidebar component that provides the main chat interface.
 * Features a modern design with header, chat area, and input controls.
 */
public class ChatSidebar {

    private Stage sidebarStage;
    private boolean isVisible = false;
    private TextArea chatArea;
    private Runnable onCloseCallback;
    
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
     * Shows the sidebar without a callback
     */
    public void show() {
        show(null);
    }

    /**
     * Shows the sidebar with an optional close callback
     */
    public void show(Runnable onCloseCallback) {
        this.onCloseCallback = onCloseCallback;

        if (sidebarStage != null && isVisible) {
            sidebarStage.toFront();
            return;
        }

        if (sidebarStage == null) {
            createSidebar();
        }

        sidebarStage.show();
        isVisible = true;
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
        
        // Create sidebar content
        VBox content = createSidebarContent();
        
        // Create scene with CSS styling
        Scene scene = new Scene(content, 380, 650);
        scene.getStylesheets().add("data:text/css," + SidebarStyles.getSidebarCSS());
        
        sidebarStage.setScene(scene);
        
        positionSidebar();
        setupCloseHandler();
    }
    
    /**
     * Positions the sidebar on the right side of the screen (opening from system tray)
     */
    private void positionSidebar() {
        Screen primaryScreen = Screen.getPrimary();
        double screenWidth = primaryScreen.getVisualBounds().getWidth();
        double screenHeight = primaryScreen.getVisualBounds().getHeight();
        double screenMinX = primaryScreen.getVisualBounds().getMinX();
        double screenMinY = primaryScreen.getVisualBounds().getMinY();

        // Position on right side with margin from edges (like system tray apps)
        double sidebarWidth = 380;
        double sidebarHeight = 650;
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

        Label subtitleLabel = new Label("Your AI-powered chat companion");
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
     * Creates the message input area with text field and send button
     */
    private HBox createInputArea() {
        HBox inputArea = new HBox(12);
        inputArea.setAlignment(Pos.CENTER);
        inputArea.getStyleClass().add("input-container");

        TextField messageInput = new TextField();
        messageInput.setPromptText("💭 Type your message here...");
        messageInput.getStyleClass().add("message-input");
        HBox.setHgrow(messageInput, Priority.ALWAYS);

        Button sendButton = new Button("🚀 Send");
        sendButton.getStyleClass().add("send-button");

        // Send message functionality with better responses
        Runnable sendMessage = () -> {
            String message = messageInput.getText().trim();
            if (!message.isEmpty()) {
                addMessage("You", message);

                // Generate more engaging demo responses
                String[] responses = {
                    "That's a great question! Let me help you with that. 🤔",
                    "I understand what you're looking for. Here's what I think... 💡",
                    "Thanks for sharing that with me! I'd be happy to assist. ✨",
                    "Interesting point! Let me provide you with some insights. 🎯",
                    "I'm here to help! Let me break that down for you. 📝"
                };
                String response = responses[(int) (Math.random() * responses.length)];
                addMessage("Assistant", response);
                messageInput.clear();
            }
        };

        sendButton.setOnAction(e -> sendMessage.run());
        messageInput.setOnAction(e -> sendMessage.run());

        inputArea.getChildren().addAll(messageInput, sendButton);
        return inputArea;
    }
    
    /**
     * Creates the action buttons (Clear and Close)
     */
    private HBox createActionButtons() {
        HBox actionButtons = new HBox(8);
        actionButtons.setAlignment(Pos.CENTER);

        Button clearButton = new Button("🗑️ Clear");
        clearButton.getStyleClass().add("action-button");
        clearButton.setOnAction(e -> {
            chatArea.setText("👋 Welcome to iChat Assistant!\n\n✨ I'm here to help you with any questions or tasks you might have. Feel free to start a conversation!");
        });

        Button closeButton = new Button("✖️ Close");
        closeButton.getStyleClass().add("close-button");
        closeButton.setOnAction(e -> hide());

        actionButtons.getChildren().addAll(clearButton, closeButton);
        return actionButtons;
    }
    
    /**
     * Adds a message to the chat area
     */
    private void addMessage(String sender, String message) {
        chatArea.appendText("\n\n" + sender + ": " + message);
        chatArea.setScrollTop(Double.MAX_VALUE);
    }
}
