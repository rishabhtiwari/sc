package ui.styles;

/**
 * Centralized styling definitions for buttons in the iChat application.
 * Contains all button-related CSS styles as constants for easy maintenance.
 */
public class ButtonStyles {
    
    /**
     * Style for the main Ask button - dock icon style with modern design
     */
    public static final String ASK_BUTTON_STYLE =
        "-fx-background-radius: 33.5; " +
        "-fx-border-radius: 33.5; " +
        "-fx-background-color: linear-gradient(to bottom, #667eea, #764ba2); " +
        "-fx-border-color: rgba(255,255,255,0.3); " +
        "-fx-border-width: 2px; " +
        "-fx-text-fill: white; " +
        "-fx-font-weight: 900; " +
        "-fx-font-size: 11px; " +
        "-fx-font-family: 'SF Pro Display', 'Helvetica Neue', 'Arial', sans-serif; " +
        "-fx-text-alignment: center; " +
        "-fx-letter-spacing: 0.2px; " +
        "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.3), 8, 0, 0, 4), " +
        "innershadow(gaussian, rgba(255,255,255,0.2), 2, 0, 0, 1); " +
        "-fx-cursor: hand;";

    /**
     * Style for the send button in the chat interface
     */
    public static final String SEND_BUTTON_STYLE = 
        "-fx-background-color: linear-gradient(to bottom, #4facfe, #00f2fe);" +
        "-fx-text-fill: white;" +
        "-fx-border-radius: 20px;" +
        "-fx-background-radius: 20px;" +
        "-fx-padding: 12 20 12 20;" +
        "-fx-font-size: 14px;" +
        "-fx-font-weight: bold;" +
        "-fx-effect: dropshadow(gaussian, rgba(79,172,254,0.4), 8, 0, 0, 2);";

    /**
     * Style for action buttons (like Clear button)
     */
    public static final String ACTION_BUTTON_STYLE = 
        "-fx-background-color: linear-gradient(to bottom, #ffecd2, #fcb69f);" +
        "-fx-text-fill: #8b4513;" +
        "-fx-border-radius: 18px;" +
        "-fx-background-radius: 18px;" +
        "-fx-padding: 10 16 10 16;" +
        "-fx-font-size: 13px;" +
        "-fx-font-weight: bold;" +
        "-fx-effect: dropshadow(gaussian, rgba(252,182,159,0.4), 6, 0, 0, 2);";

    /**
     * Style for close/cancel buttons
     */
    public static final String CLOSE_BUTTON_STYLE = 
        "-fx-background-color: linear-gradient(to bottom, #ff9a9e, #fecfef);" +
        "-fx-text-fill: #8b2635;" +
        "-fx-border-radius: 18px;" +
        "-fx-background-radius: 18px;" +
        "-fx-padding: 10 16 10 16;" +
        "-fx-font-size: 13px;" +
        "-fx-font-weight: bold;" +
        "-fx-effect: dropshadow(gaussian, rgba(255,154,158,0.4), 6, 0, 0, 2);";
}
