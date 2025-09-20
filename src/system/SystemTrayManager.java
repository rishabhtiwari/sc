package system;

import javafx.application.Platform;
import ui.components.ChatSidebar;

import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;

/**
 * Manages system tray integration for the iChat application.
 * Provides native dock/taskbar icon functionality.
 */
public class SystemTrayManager {

    private SystemTray systemTray;
    private TrayIcon trayIcon;
    private ChatSidebar chatSidebar;

    public SystemTrayManager() {
        this.chatSidebar = new ChatSidebar();
    }

    /**
     * Initializes and shows the system tray icon
     */
    public void initialize() {
        // Run on AWT Event Dispatch Thread for proper system tray initialization
        java.awt.EventQueue.invokeLater(() -> {
            initializeSystemTray();
        });
    }

    /**
     * Internal method to initialize system tray (runs on AWT EDT)
     */
    private void initializeSystemTray() {
        System.out.println("Checking system tray support...");

        if (!SystemTray.isSupported()) {
            System.err.println("❌ System tray is not supported on this platform");
            // Fallback to floating button if system tray not supported
            Platform.runLater(() -> {
                System.out.println("Falling back to floating button...");
                // You can uncomment this if you want fallback to floating button
                // new ui.components.AskButton().show();
            });
            return;
        }

        System.out.println("✅ System tray is supported");

        try {
            systemTray = SystemTray.getSystemTray();
            System.out.println("✅ System tray instance obtained");

            // Create tray icon
            Image trayImage = createTrayIcon();
            System.out.println("✅ Tray icon image created");

            trayIcon = new TrayIcon(trayImage, "iChat Assistant");
            trayIcon.setImageAutoSize(true);
            trayIcon.setToolTip("iChat Assistant - Click to open chat");

            // Add click listener
            trayIcon.addActionListener(new ActionListener() {
                @Override
                public void actionPerformed(ActionEvent e) {
                    System.out.println("🖱️ Tray icon clicked!");
                    System.out.println("🔍 Starting screen detection...");

                    Platform.runLater(() -> {
                        try {
                            // Get the screen where the active window is located
                            javafx.stage.Screen activeScreen = detectActiveWindowScreen();
                            System.out.println("🎯 Detected screen: " + activeScreen.getBounds());
                            System.out.println("📱 Calling toggleOnScreen...");
                            chatSidebar.toggleOnScreen(activeScreen);
                        } catch (Exception ex) {
                            System.err.println("❌ Error in tray click handler: " + ex.getMessage());
                            ex.printStackTrace();
                            // Fallback to regular toggle
                            chatSidebar.toggle();
                        }
                    });
                }
            });

            // Create popup menu
            PopupMenu popupMenu = createPopupMenu();
            trayIcon.setPopupMenu(popupMenu);
            System.out.println("✅ Popup menu created");

            // Add to system tray
            systemTray.add(trayIcon);
            System.out.println("🎉 iChat system tray icon added successfully!");
            System.out.println("📍 Look for the iChat icon in your system tray/menu bar");

        } catch (AWTException e) {
            System.err.println("❌ Failed to add system tray icon: " + e.getMessage());
            e.printStackTrace();
        } catch (Exception e) {
            System.err.println("❌ Unexpected error during tray initialization: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Creates the tray icon image
     */
    private Image createTrayIcon() {
        // Create a more visible chat bubble icon
        int size = 32; // Larger size for better visibility
        BufferedImage image = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2d = image.createGraphics();

        // Enable antialiasing for smooth graphics
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        // Create gradient background (purple to blue)
        GradientPaint gradient = new GradientPaint(0, 0, new Color(102, 126, 234),
                0, size, new Color(118, 75, 162));
        g2d.setPaint(gradient);
        g2d.fillOval(2, 2, size - 4, size - 4);

        // Add subtle white border
        g2d.setColor(new Color(255, 255, 255, 180));
        g2d.setStroke(new BasicStroke(2.0f));
        g2d.drawOval(2, 2, size - 4, size - 4);

        // Add "iC" text for iChat
        g2d.setColor(Color.WHITE);
        g2d.setFont(new Font("Arial", Font.BOLD, 14));
        FontMetrics fm = g2d.getFontMetrics();
        String text = "iC";
        int textWidth = fm.stringWidth(text);
        int textHeight = fm.getAscent();

        // Center the text
        int x = (size - textWidth) / 2;
        int y = (size + textHeight) / 2 - 2;

        // Add text shadow for better visibility
        g2d.setColor(new Color(0, 0, 0, 100));
        g2d.drawString(text, x + 1, y + 1);

        // Draw main text
        g2d.setColor(Color.WHITE);
        g2d.drawString(text, x, y);

        g2d.dispose();

        System.out.println("✅ Created tray icon: " + size + "x" + size + " pixels");
        return image;
    }

    /**
     * Creates the popup menu for the tray icon
     */
    private PopupMenu createPopupMenu() {
        PopupMenu popupMenu = new PopupMenu();

        // Open Chat menu item
        MenuItem openItem = new MenuItem("Open iChat");
        openItem.addActionListener(e -> {
            Platform.runLater(() -> {
                javafx.stage.Screen activeScreen = detectActiveWindowScreen();
                chatSidebar.showOnScreen(activeScreen);
            });
        });

        // Separator
        popupMenu.addSeparator();

        // About menu item
        MenuItem aboutItem = new MenuItem("About iChat");
        aboutItem.addActionListener(e -> {
            Platform.runLater(() -> {
                showAboutDialog();
            });
        });

        // Exit menu item
        MenuItem exitItem = new MenuItem("Exit");
        exitItem.addActionListener(e -> {
            // Cleanup resources
            if (chatSidebar != null) {
                chatSidebar.cleanup();
            }
            cleanup();
            Platform.exit();
            System.exit(0);
        });

        popupMenu.add(openItem);
        popupMenu.add(aboutItem);
        popupMenu.addSeparator();
        popupMenu.add(exitItem);

        return popupMenu;
    }

    /**
     * Shows an about dialog
     */
    private void showAboutDialog() {
        if (Desktop.isDesktopSupported()) {
            trayIcon.displayMessage("About iChat",
                    "iChat Assistant v1.0\nYour AI-powered chat companion",
                    TrayIcon.MessageType.INFO);
        }
    }

    /**
     * Updates the tray icon tooltip
     */
    public void updateTooltip(String tooltip) {
        if (trayIcon != null) {
            trayIcon.setToolTip(tooltip);
        }
    }

    /**
     * Shows a notification message
     */
    public void showNotification(String title, String message) {
        if (trayIcon != null) {
            trayIcon.displayMessage(title, message, TrayIcon.MessageType.INFO);
        }
    }

    /**
     * Detects the screen where the user's mouse pointer is currently located.
     * Falls back to primary screen if the mouse location can't be obtained.
     */
    private javafx.stage.Screen detectActiveWindowScreen() {
        try {
// Create a JavaFX Robot to get the mouse position in the correct coordinate system
            javafx.scene.robot.Robot robot = new javafx.scene.robot.Robot();
            javafx.geometry.Point2D mousePos = robot.getMousePosition(); // in JavaFX coordinates

            if (mousePos != null) {
// Check each screen's bounds to see which contains the mouse
                for (javafx.stage.Screen screen : javafx.stage.Screen.getScreens()) {
                    javafx.geometry.Rectangle2D bounds = screen.getBounds();
                    System.out.println("Checking screen bounds: " + bounds);

                    if (bounds.contains(mousePos)) {
                        System.out.println("✅ Mouse is on screen: " + bounds);
                        return screen;
                    }
                }
            } else {
                System.out.println("⚠️ Robot returned null mouse position. Check permissions on macOS.");
            }
        } catch (Exception e) {
            System.err.println("Error detecting screen by mouse pointer: " + e.getMessage());
            e.printStackTrace();
        }
// Fallback to primary if nothing else worked
        System.out.println("⚠️ Using primary screen as fallback");
        return javafx.stage.Screen.getPrimary();
    }

    /**
     * Cleans up system tray resources
     */
    public void cleanup() {
        if (systemTray != null && trayIcon != null) {
            systemTray.remove(trayIcon);
        }
    }
}
