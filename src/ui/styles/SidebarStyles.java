package ui.styles;

/**
 * Centralized styling definitions for the chat sidebar.
 * Contains all CSS styles for the sidebar components.
 */
public class SidebarStyles {
    
    /**
     * Complete CSS stylesheet for the sidebar components
     */
    public static String getSidebarCSS() {
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
