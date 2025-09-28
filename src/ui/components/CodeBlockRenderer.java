package ui.components;

import javafx.geometry.Insets;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.layout.VBox;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Priority;
import javafx.scene.paint.Color;
import javafx.scene.text.Font;
import javafx.scene.text.FontWeight;
import javafx.scene.control.Button;
import javafx.scene.control.ContextMenu;
import javafx.scene.control.MenuItem;
import javafx.scene.input.Clipboard;
import javafx.scene.input.ClipboardContent;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * Renders code blocks with proper styling similar to Augment's code display
 */
public class CodeBlockRenderer {
    
    private static final Pattern CODE_BLOCK_PATTERN = Pattern.compile("```(\\w+)?\\n([\\s\\S]*?)```", Pattern.MULTILINE);
    
    /**
     * Creates a VBox containing properly formatted message with code blocks
     */
    public static VBox createFormattedMessage(String sender, String message) {
        VBox messageContainer = new VBox(8);
        messageContainer.setPadding(new Insets(12));
        
        // Sender label
        Label senderLabel = new Label(sender + ":");
        senderLabel.setFont(Font.font("SF Pro Display", FontWeight.BOLD, 14));
        senderLabel.setTextFill(sender.equals("You") ? Color.web("#4facfe") : Color.web("#48bb78"));
        
        // Parse message for code blocks
        VBox contentContainer = parseMessageContent(message);
        
        messageContainer.getChildren().addAll(senderLabel, contentContainer);
        
        // Style message container
        String backgroundColor = sender.equals("You") ? "#2d3748" : "#1a202c";
        messageContainer.setStyle(
            "-fx-background-color: " + backgroundColor + ";" +
            "-fx-border-color: #4a5568;" +
            "-fx-border-width: 1px;" +
            "-fx-border-radius: 8px;" +
            "-fx-background-radius: 8px;"
        );
        
        return messageContainer;
    }
    
    private static VBox parseMessageContent(String message) {
        VBox content = new VBox(12);
        
        Matcher codeBlockMatcher = CODE_BLOCK_PATTERN.matcher(message);
        int lastEnd = 0;
        
        while (codeBlockMatcher.find()) {
            // Add text before code block
            if (codeBlockMatcher.start() > lastEnd) {
                String textPart = message.substring(lastEnd, codeBlockMatcher.start()).trim();
                if (!textPart.isEmpty()) {
                    content.getChildren().add(createTextBlock(textPart));
                }
            }
            
            // Add code block
            String language = codeBlockMatcher.group(1);
            String code = codeBlockMatcher.group(2);
            content.getChildren().add(createCodeBlock(language, code));
            
            lastEnd = codeBlockMatcher.end();
        }
        
        // Add remaining text after last code block
        if (lastEnd < message.length()) {
            String textPart = message.substring(lastEnd).trim();
            if (!textPart.isEmpty()) {
                content.getChildren().add(createTextBlock(textPart));
            }
        }
        
        // If no code blocks found, add entire message as text
        if (content.getChildren().isEmpty()) {
            content.getChildren().add(createTextBlock(message));
        }
        
        return content;
    }
    
    private static javafx.scene.layout.StackPane createTextBlock(String text) {
        javafx.scene.layout.StackPane container = new javafx.scene.layout.StackPane();

        // Create visible label for display
        Label displayLabel = new Label(text);
        displayLabel.setWrapText(true);
        displayLabel.setFont(Font.font("SF Pro Text", 14));
        displayLabel.setTextFill(Color.web("#ffffff"));
        displayLabel.setMaxWidth(Double.MAX_VALUE);
        displayLabel.setPadding(new Insets(4, 0, 4, 0));
        displayLabel.setAlignment(javafx.geometry.Pos.TOP_LEFT);

        // Create invisible TextArea for selection functionality
        TextArea selectionArea = new TextArea(text);
        selectionArea.setEditable(false);
        selectionArea.setWrapText(true);

        // Calculate height based on content
        int lineCount = Math.max(1, text.split("\n").length);
        double lineHeight = 20.0;
        double calculatedHeight = lineCount * lineHeight + 16;

        selectionArea.setPrefRowCount(lineCount);
        selectionArea.setMinHeight(calculatedHeight);
        selectionArea.setPrefHeight(calculatedHeight);
        selectionArea.setMaxHeight(Double.MAX_VALUE);

        // Make selection area completely invisible but functional
        selectionArea.setStyle(
            "-fx-control-inner-background: transparent;" +
            "-fx-text-fill: transparent;" +
            "-fx-font-family: 'SF Pro Text', system-ui, sans-serif;" +
            "-fx-font-size: 14px;" +
            "-fx-border-color: transparent;" +
            "-fx-border-width: 0px;" +
            "-fx-background-color: transparent;" +
            "-fx-background-insets: 0px;" +
            "-fx-border-insets: 0px;" +
            "-fx-padding: 4 0 4 0;" +
            "-fx-highlight-fill: #4a5568;" +
            "-fx-highlight-text-fill: #ffffff;" +
            "-fx-focus-color: transparent;" +
            "-fx-faint-focus-color: transparent;" +
            "-fx-opacity: 0.01;"  // Almost invisible but still functional
        );

        selectionArea.setFocusTraversable(true);

        // Position caret at start
        javafx.application.Platform.runLater(() -> {
            selectionArea.positionCaret(0);
            selectionArea.deselect();
        });

        // Stack them - label visible, textarea invisible but selectable
        container.getChildren().addAll(displayLabel, selectionArea);
        container.setAlignment(javafx.geometry.Pos.TOP_LEFT);

        return container;
    }
    
    private static VBox createCodeBlock(String language, String code) {
        VBox codeContainer = new VBox();
        
        // Header with language and copy button
        HBox header = new HBox();
        header.setPadding(new Insets(8, 12, 8, 12));
        header.setStyle(
            "-fx-background-color: #2d3748;" +
            "-fx-border-color: #4a5568;" +
            "-fx-border-width: 0 0 1 0;"
        );
        
        // Language label
        Label languageLabel = new Label(language != null ? language.toLowerCase() : "code");
        languageLabel.setFont(Font.font("SF Pro Text", FontWeight.MEDIUM, 12));
        languageLabel.setTextFill(Color.web("#a0aec0"));
        
        // Copy button
        Button copyButton = new Button("Copy");
        copyButton.setFont(Font.font("SF Pro Text", 11));
        copyButton.setStyle(
            "-fx-background-color: #4a5568;" +
            "-fx-text-fill: #e2e8f0;" +
            "-fx-border-color: #718096;" +
            "-fx-border-width: 1px;" +
            "-fx-border-radius: 4px;" +
            "-fx-background-radius: 4px;" +
            "-fx-padding: 4 8 4 8;"
        );
        
        // Copy functionality
        copyButton.setOnAction(e -> {
            Clipboard clipboard = Clipboard.getSystemClipboard();
            ClipboardContent content = new ClipboardContent();
            content.putString(code.trim());
            clipboard.setContent(content);
            
            // Visual feedback
            copyButton.setText("Copied!");
            copyButton.setStyle(copyButton.getStyle() + "-fx-background-color: #48bb78;");
            
            // Reset after 2 seconds
            new Thread(() -> {
                try {
                    Thread.sleep(2000);
                    javafx.application.Platform.runLater(() -> {
                        copyButton.setText("Copy");
                        copyButton.setStyle(
                            "-fx-background-color: #4a5568;" +
                            "-fx-text-fill: #e2e8f0;" +
                            "-fx-border-color: #718096;" +
                            "-fx-border-width: 1px;" +
                            "-fx-border-radius: 4px;" +
                            "-fx-background-radius: 4px;" +
                            "-fx-padding: 4 8 4 8;"
                        );
                    });
                } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                }
            }).start();
        });
        
        HBox.setHgrow(languageLabel, Priority.ALWAYS);
        header.getChildren().addAll(languageLabel, copyButton);
        
        // Code content
        TextArea codeArea = new TextArea(code.trim());
        codeArea.setEditable(false);
        codeArea.setWrapText(false);
        codeArea.setFont(Font.font("SF Mono", 13));

        // Calculate height based on content - ensure full output is always visible
        String[] lines = code.trim().split("\n");
        int lineCount = Math.max(lines.length, 1);

        // Calculate actual height needed
        double lineHeight = 18.0; // Height per line in pixels
        double padding = 24.0;    // Top and bottom padding
        double calculatedHeight = (lineCount * lineHeight) + padding;

        // Set explicit height to ensure full content is visible
        codeArea.setPrefRowCount(lineCount);
        codeArea.setMinHeight(calculatedHeight);
        codeArea.setPrefHeight(calculatedHeight);
        codeArea.setMaxHeight(Double.MAX_VALUE);

        // Force the TextArea to show all content
        codeArea.setScrollTop(0);
        codeArea.positionCaret(0);
        
        // Style code area
        codeArea.setStyle(
            "-fx-control-inner-background: #1a202c;" +
            "-fx-text-fill: #f7fafc;" +
            "-fx-border-color: transparent;" +
            "-fx-background-color: #1a202c;" +
            "-fx-padding: 12px;" +
            "-fx-font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;" +
            "-fx-highlight-fill: #4a5568;" +
            "-fx-highlight-text-fill: #ffffff;" +
            "-fx-focus-color: #4a5568;" +
            "-fx-faint-focus-color: #4a5568;"
        );

        // Enable text selection and Ctrl+C support
        codeArea.setFocusTraversable(true);

        // Ensure the TextArea properly displays all content
        javafx.application.Platform.runLater(() -> {
            codeArea.requestLayout();
            codeArea.autosize();
            codeArea.positionCaret(0);
        });
        
        codeContainer.getChildren().addAll(header, codeArea);

        // Style container
        codeContainer.setStyle(
            "-fx-background-color: #1a202c;" +
            "-fx-border-color: #4a5568;" +
            "-fx-border-width: 1px;" +
            "-fx-border-radius: 8px;" +
            "-fx-background-radius: 8px;"
        );

        // Ensure container properly sizes to content
        codeContainer.setMaxHeight(Double.MAX_VALUE);
        codeContainer.setFillWidth(true);
        VBox.setVgrow(codeArea, Priority.ALWAYS);

        // Debug: Print code length to help diagnose truncation issues
        System.out.println("🔍 Code block created - Lines: " + lines.length + ", Height: " + calculatedHeight + "px");

        return codeContainer;
    }
}
