package app;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.stage.Stage;
import system.SystemTrayManager;

/**
 * Main JavaFX application class for the iChat Assistant.
 * Manages the application lifecycle and system tray integration.
 */
public class IChatApplication extends Application {

    private SystemTrayManager systemTrayManager;

    @Override
    public void start(Stage stage) throws Exception {
        System.out.println("🚀 Starting iChat Assistant...");

        // Hide the primary stage since we don't need it
        stage.hide();

        // Keep the application running even when no windows are visible
        Platform.setImplicitExit(false);
        System.out.println("✅ JavaFX application initialized");

        // Initialize system tray
        System.out.println("🔧 Initializing system tray...");
        systemTrayManager = new SystemTrayManager();
        systemTrayManager.initialize();

        // Delay notification to ensure tray icon is ready
        Platform.runLater(() -> {
            try {
                Thread.sleep(1000); // Wait 1 second
                if (systemTrayManager != null) {
                    systemTrayManager.showNotification("iChat Assistant",
                        "iChat is now running! Look for the 'iC' icon in your system tray.");
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });

        System.out.println("✅ iChat Assistant startup complete!");
        System.out.println("📍 Look for the purple 'iC' icon in your system tray/menu bar");
    }

    @Override
    public void stop() throws Exception {
        // Clean up system tray when application is closing
        if (systemTrayManager != null) {
            systemTrayManager.cleanup();
        }
        super.stop();
    }
}
