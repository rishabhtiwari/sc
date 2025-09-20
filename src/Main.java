import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.layout.Pane;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
public class Main extends Application {
    public static void main(String[] args) {
        launch(args);
    }

    @Override
    public void start(Stage stage) throws Exception {
        // Create circular Ask button with question mark icon
        Button askButton = new Button("?");
        askButton.setPrefSize(58, 58);
        askButton.setStyle(
            "-fx-background-radius: 29; " +
            "-fx-border-radius: 29; " +
            "-fx-background-color: linear-gradient(to bottom, #FF6B35, #F7931E); " +
            "-fx-border-color: #FFFFFF; " +
            "-fx-border-width: 2px; " +
            "-fx-text-fill: white; " +
            "-fx-font-weight: bold; " +
            "-fx-font-size: 26px; " +
            "-fx-font-family: 'Arial Black'; " +
            "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.5), 6, 0, 0, 3);"
        );

        // Add click event
        askButton.setOnAction(e -> {
            System.out.println("Ask button clicked!");
        });

        // Make button draggable across entire screen
        final double[] dragDelta = new double[2];
        askButton.setOnMousePressed(e -> {
            dragDelta[0] = stage.getX() - e.getScreenX();
            dragDelta[1] = stage.getY() - e.getScreenY();
        });

        askButton.setOnMouseDragged(e -> {
            stage.setX(e.getScreenX() + dragDelta[0]);
            stage.setY(e.getScreenY() + dragDelta[1]);
        });

        // Create transparent layout
        Pane root = new Pane();
        root.getChildren().add(askButton);

        // Create circular clip for the scene
        Circle clip = new Circle(29, 29, 29); // center at (29,29) with radius 29
        root.setClip(clip);

        // Create transparent scene
        Scene scene = new Scene(root, 58, 58);
        scene.setFill(Color.TRANSPARENT);

        // Configure stage to be transparent and always on top
        stage.initStyle(StageStyle.TRANSPARENT);
        stage.setAlwaysOnTop(true);
        stage.setResizable(false);
        stage.setScene(scene);
        stage.show();
    }
}