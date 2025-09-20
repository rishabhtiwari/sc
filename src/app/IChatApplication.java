package app;

import javafx.application.Application;
import javafx.stage.Stage;
import ui.components.AskButton;

/**
 * Main JavaFX application class for the iChat Assistant.
 * Manages the application lifecycle and coordinates the main components.
 */
public class IChatApplication extends Application {

    private AskButton askButton;

    @Override
    public void start(Stage stage) throws Exception {
        // Create and show the Ask button
        askButton = new AskButton();
        askButton.show();

        // Close the primary stage since we don't need it
        stage.close();
    }

    @Override
    public void stop() throws Exception {
        // Clean up when application is closing
        if (askButton != null) {
            askButton.hide();
        }
        super.stop();
    }
}
