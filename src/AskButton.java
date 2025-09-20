import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.layout.Pane;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

public class AskButton {
    
    private Stage buttonStage;
    private ChatSidebar chatSidebar;
    
    public AskButton() {
        this.chatSidebar = new ChatSidebar();
    }
    
    public void show() {
        // Create circular Ask button with question mark and iChat text
        Button askButton = new Button("?\niChat");
        askButton.setPrefSize(67, 67);
        askButton.setStyle(
            "-fx-background-radius: 33.5; " +
            "-fx-border-radius: 33.5; " +
            "-fx-background-color: linear-gradient(to bottom, #FF6B35, #F7931E); " +
            "-fx-border-color: #FFFFFF; " +
            "-fx-border-width: 2px; " +
            "-fx-text-fill: white; " +
            "-fx-font-weight: 900; " +
            "-fx-font-size: 12px; " +
            "-fx-font-family: 'SF Pro Display Black', 'Helvetica Neue Bold', 'Arial Black', sans-serif; " +
            "-fx-text-alignment: center; " +
            "-fx-letter-spacing: 0.3px; " +
            "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.5), 6, 0, 0, 3), " +
            "dropshadow(gaussian, rgba(0,0,0,0.8), 1, 0, 0, 1);"
        );
        
        // Add click event to open sidebar and hide button
        askButton.setOnAction(e -> {
            hideButton();
            chatSidebar.show(() -> showButton()); // Pass callback to show button when sidebar closes
        });
        
        // Create button stage
        buttonStage = new Stage();
        
        // Make button draggable across entire screen
        final double[] dragDelta = new double[2];
        askButton.setOnMousePressed(e -> {
            dragDelta[0] = buttonStage.getX() - e.getScreenX();
            dragDelta[1] = buttonStage.getY() - e.getScreenY();
        });
        
        askButton.setOnMouseDragged(e -> {
            buttonStage.setX(e.getScreenX() + dragDelta[0]);
            buttonStage.setY(e.getScreenY() + dragDelta[1]);
        });
        
        // Create transparent layout
        Pane root = new Pane();
        root.getChildren().add(askButton);
        
        // Create circular clip for the scene
        Circle clip = new Circle(33.5, 33.5, 33.5);
        root.setClip(clip);
        
        // Create transparent scene
        Scene scene = new Scene(root, 67, 67);
        scene.setFill(Color.TRANSPARENT);
        
        // Configure stage to be transparent and always on top
        buttonStage.initStyle(StageStyle.TRANSPARENT);
        buttonStage.setAlwaysOnTop(true);
        buttonStage.setResizable(false);
        buttonStage.setTitle("iChat Ask Button");
        buttonStage.setScene(scene);
        buttonStage.show();
    }
    
    public void hide() {
        if (buttonStage != null) {
            buttonStage.hide();
        }
        chatSidebar.hide();
    }

    public void hideButton() {
        if (buttonStage != null) {
            buttonStage.hide();
        }
    }

    public void showButton() {
        if (buttonStage != null) {
            buttonStage.show();
        }
    }
}
