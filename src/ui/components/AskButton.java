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
    private ChatSidebar chatSidebar;
    
    public AskButton() {
        this.chatSidebar = new ChatSidebar();
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
        // Create circular Ask button with question mark and iChat text
        Button askButton = new Button("?\niChat");
        askButton.setPrefSize(67, 67);
        askButton.setStyle(ButtonStyles.ASK_BUTTON_STYLE);
        
        // Add click event to open sidebar and hide button
        askButton.setOnAction(e -> {
            hideButton();
            chatSidebar.show(() -> showButton()); // Pass callback to show button when sidebar closes
        });
        
        setupDragFunctionality(askButton);
        createButtonScene(askButton);
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
     * Shows the button stage
     */
    private void showStage() {
        buttonStage.show();
    }
    
    /**
     * Hides both the button and sidebar
     */
    public void hide() {
        if (buttonStage != null) {
            buttonStage.hide();
        }
        chatSidebar.hide();
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
