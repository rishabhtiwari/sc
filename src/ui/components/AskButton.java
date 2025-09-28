package ui.components;

import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.layout.Pane;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.stage.Stage;
import javafx.stage.StageStyle;
import ui.styles.ButtonStyles;

/**
 * Floating Ask button component that provides access to the chat interface.
 * Features a circular design with drag functionality and always-on-top behavior.
 */
public class AskButton {
    
    private Stage buttonStage;
    private EnhancedChatSidebar enhancedChatSidebar;

    public AskButton() {
        this.enhancedChatSidebar = new EnhancedChatSidebar();
    }
    
    /**
     * Shows the Ask button on screen
     */
    public void show() {
        configureStage();
        createButton();
        showStage();
    }
    
    /**
     * Creates the circular Ask button with styling and event handlers
     */
    private void createButton() {
        // Create dock-style iChat button
        Button askButton = new Button("💬\niChat");
        askButton.setPrefSize(67, 67);
        askButton.setStyle(ButtonStyles.ASK_BUTTON_STYLE);
        
        // Add click event to open/toggle sidebar (like dock icon behavior)
        askButton.setOnAction(e -> {
            enhancedChatSidebar.toggle(); // Toggle sidebar without hiding the dock icon
        });

        // Add hover effects like dock icons
        setupHoverEffects(askButton);
        setupDragFunctionality(askButton);
        createButtonScene(askButton);
    }
    
    /**
     * Sets up hover effects like dock icons (scale up on hover)
     */
    private void setupHoverEffects(Button askButton) {
        // Scale up on hover like dock icons
        askButton.setOnMouseEntered(e -> {
            askButton.setScaleX(1.1);
            askButton.setScaleY(1.1);
        });

        // Scale back to normal when mouse leaves
        askButton.setOnMouseExited(e -> {
            askButton.setScaleX(1.0);
            askButton.setScaleY(1.0);
        });
    }

    /**
     * Sets up drag functionality for the button
     */
    private void setupDragFunctionality(Button askButton) {
        final double[] dragDelta = new double[2];

        askButton.setOnMousePressed(e -> {
            dragDelta[0] = buttonStage.getX() - e.getScreenX();
            dragDelta[1] = buttonStage.getY() - e.getScreenY();
        });

        askButton.setOnMouseDragged(e -> {
            buttonStage.setX(e.getScreenX() + dragDelta[0]);
            buttonStage.setY(e.getScreenY() + dragDelta[1]);
        });
    }
    
    /**
     * Creates the scene with circular clipping for the button
     */
    private void createButtonScene(Button askButton) {
        // Create transparent layout
        Pane root = new Pane();
        root.getChildren().add(askButton);
        
        // Create circular clip for the scene
        Circle clip = new Circle(33.5, 33.5, 33.5);
        root.setClip(clip);
        
        // Create transparent scene
        Scene scene = new Scene(root, 67, 67);
        scene.setFill(Color.TRANSPARENT);
        
        buttonStage.setScene(scene);
    }
    
    /**
     * Configures the stage properties
     */
    private void configureStage() {
        buttonStage = new Stage();
        buttonStage.initStyle(StageStyle.TRANSPARENT);
        buttonStage.setAlwaysOnTop(true);
        buttonStage.setResizable(false);
        buttonStage.setTitle("iChat Ask Button");
    }

    /**
     * Shows the button stage and positions it like a dock icon
     */
    private void showStage() {
        buttonStage.show();
        positionAsDockIcon();
    }

    /**
     * Positions the button at the bottom center of the screen like a dock icon
     */
    private void positionAsDockIcon() {
        javafx.stage.Screen primaryScreen = javafx.stage.Screen.getPrimary();
        double screenWidth = primaryScreen.getVisualBounds().getWidth();
        double screenHeight = primaryScreen.getVisualBounds().getHeight();
        double screenMinX = primaryScreen.getVisualBounds().getMinX();
        double screenMinY = primaryScreen.getVisualBounds().getMinY();

        // Position at bottom center of screen (like dock icon)
        double buttonWidth = 67;
        double buttonHeight = 67;
        double bottomMargin = 20; // Distance from bottom edge

        double x = screenMinX + (screenWidth - buttonWidth) / 2; // Center horizontally
        double y = screenMinY + screenHeight - buttonHeight - bottomMargin; // Bottom with margin

        buttonStage.setX(x);
        buttonStage.setY(y);
    }
    
    /**
     * Hides both the button and sidebar
     */
    public void hide() {
        if (buttonStage != null) {
            buttonStage.hide();
        }
        enhancedChatSidebar.hide();
    }

    /**
     * Hides only the button (used when opening sidebar)
     */
    public void hideButton() {
        if (buttonStage != null) {
            buttonStage.hide();
        }
    }

    /**
     * Shows the button (used when closing sidebar)
     */
    public void showButton() {
        if (buttonStage != null) {
            buttonStage.show();
        }
    }
}
