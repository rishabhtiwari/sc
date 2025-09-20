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

public class ChatSidebar {

    private Stage sidebarStage;
    private boolean isVisible = false;
    private TextArea chatArea;
    private Runnable onCloseCallback;
    
    public void toggle() {
        if (isVisible) {
            hide();
        } else {
            show();
        }
    }

    public void show() {
        show(null);
    }

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
    
    private void createSidebar() {
        sidebarStage = new Stage();
        sidebarStage.setTitle("iChat Assistant");
        sidebarStage.setAlwaysOnTop(true);
        
        // Create sidebar content
        VBox content = createSidebarContent();
        
        // Create scene with CSS styling
        Scene scene = new Scene(content, 380, 650);
        scene.getStylesheets().add("data:text/css," + getSidebarCSS());
        
        sidebarStage.setScene(scene);
        
        // Position sidebar on the right side of screen
        double screenWidth = Screen.getPrimary().getVisualBounds().getWidth();
        sidebarStage.setX(screenWidth - 380);
        sidebarStage.setY(30);
        
        // Handle close event
        sidebarStage.setOnCloseRequest(e -> {
            hide(); // Use hide() method to trigger callback
        });
    }
    
    private VBox createSidebarContent() {
        VBox content = new VBox();
        content.getStyleClass().add("sidebar-content");

        // Compact header section
        VBox headerSection = new VBox(3);
        headerSection.setPadding(new Insets(20, 25, 15, 25));
        headerSection.getStyleClass().add("header-section");

        Label headerLabel = new Label("💬 iChat Assistant");
        headerLabel.getStyleClass().add("sidebar-header");

        Label subtitleLabel = new Label("Your AI-powered chat companion");
        subtitleLabel.getStyleClass().add("sidebar-subtitle");

        headerSection.getChildren().addAll(headerLabel, subtitleLabel);

        // Maximized chat area - takes most of the space
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

        // Compact input section at bottom
        VBox inputSection = new VBox(10);
        inputSection.setPadding(new Insets(10, 25, 20, 25));
        inputSection.getStyleClass().add("input-section");

        HBox inputArea = createInputArea();

        // Compact action buttons in single row
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

        inputSection.getChildren().addAll(inputArea, actionButtons);

        // Add all sections to main content
        content.getChildren().addAll(headerSection, chatScrollPane, inputSection);

        return content;
    }
    
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
    
    private void addMessage(String sender, String message) {
        chatArea.appendText("\n\n" + sender + ": " + message);
        chatArea.setScrollTop(Double.MAX_VALUE);
    }
    
    private String getSidebarCSS() {
        return ".sidebar-content {" +
                "-fx-background-color: linear-gradient(to bottom, #ffffff, #f8fafc);" +
                "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.15), 20, 0, 0, 5);" +
                "}" +

                ".header-section {" +
                "-fx-background-color: linear-gradient(to bottom, #667eea, #764ba2);" +
                "-fx-background-radius: 0 0 20 20;" +
                "}" +

                ".sidebar-header {" +
                "-fx-font-size: 24px;" +
                "-fx-font-weight: bold;" +
                "-fx-text-fill: white;" +
                "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.3), 2, 0, 0, 1);" +
                "}" +

                ".sidebar-subtitle {" +
                "-fx-font-size: 14px;" +
                "-fx-text-fill: #e0e0e0;" +
                "-fx-font-style: italic;" +
                "}" +

                ".chat-area {" +
                "-fx-background-color: #ffffff;" +
                "-fx-border-color: #e2e8f0;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 15px;" +
                "-fx-background-radius: 15px;" +
                "-fx-padding: 15px;" +
                "-fx-font-size: 14px;" +
                "-fx-text-fill: #2d3748;" +
                "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.08), 8, 0, 0, 2);" +
                "}" +

                ".chat-scroll {" +
                "-fx-background-color: transparent;" +
                "-fx-border-color: transparent;" +
                "-fx-fit-to-width: true;" +
                "-fx-fit-to-height: true;" +
                "}" +

                ".input-section {" +
                "-fx-background-color: #f8fafc;" +
                "-fx-background-radius: 20 20 0 0;" +
                "-fx-border-color: #e2e8f0;" +
                "-fx-border-width: 1 0 0 0;" +
                "}" +

                ".input-container {" +
                "-fx-background-color: white;" +
                "-fx-background-radius: 25px;" +
                "-fx-padding: 8px;" +
                "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.1), 10, 0, 0, 2);" +
                "}" +

                ".message-input {" +
                "-fx-background-color: transparent;" +
                "-fx-border-color: transparent;" +
                "-fx-padding: 12 18 12 18;" +
                "-fx-font-size: 14px;" +
                "-fx-text-fill: #2d3748;" +
                "-fx-prompt-text-fill: #a0aec0;" +
                "}" +

                ".send-button {" +
                "-fx-background-color: linear-gradient(to bottom, #4facfe, #00f2fe);" +
                "-fx-text-fill: white;" +
                "-fx-border-radius: 20px;" +
                "-fx-background-radius: 20px;" +
                "-fx-padding: 12 20 12 20;" +
                "-fx-font-size: 14px;" +
                "-fx-font-weight: bold;" +
                "-fx-effect: dropshadow(gaussian, rgba(79,172,254,0.4), 8, 0, 0, 2);" +
                "}" +

                ".action-button {" +
                "-fx-background-color: linear-gradient(to bottom, #ffecd2, #fcb69f);" +
                "-fx-text-fill: #8b4513;" +
                "-fx-border-radius: 18px;" +
                "-fx-background-radius: 18px;" +
                "-fx-padding: 10 16 10 16;" +
                "-fx-font-size: 13px;" +
                "-fx-font-weight: bold;" +
                "-fx-effect: dropshadow(gaussian, rgba(252,182,159,0.4), 6, 0, 0, 2);" +
                "}" +

                ".close-button {" +
                "-fx-background-color: linear-gradient(to bottom, #ff9a9e, #fecfef);" +
                "-fx-text-fill: #8b2635;" +
                "-fx-border-radius: 18px;" +
                "-fx-background-radius: 18px;" +
                "-fx-padding: 10 16 10 16;" +
                "-fx-font-size: 13px;" +
                "-fx-font-weight: bold;" +
                "-fx-effect: dropshadow(gaussian, rgba(255,154,158,0.4), 6, 0, 0, 2);" +
                "}";
    }
}
