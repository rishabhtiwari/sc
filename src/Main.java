import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.stage.Stage;


public class Main extends Application {
    public static void main(String[] args) {
        launch(args);
    }

    @Override
    public void start(Stage stage) throws Exception {
        Label label = new Label("Hello, World!");
        Scene scene = new Scene(label, 300, 200);
        stage.setTitle("Hello World");
        stage.setScene(scene);
        stage.show();
    }
}