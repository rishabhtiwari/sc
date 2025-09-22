package ui.styles;

/**
 * Centralized styling definitions for the chat sidebar.
 * Contains all CSS styles for the sidebar components.
 */
public class SidebarStyles {
    
    /**
     * Complete CSS stylesheet for the sidebar components - Augment Design System
     */
    public static String getSidebarCSS() {
        return ".sidebar-content {" +
                "-fx-background-color: #2d3748;" +
                "-fx-effect: dropshadow(gaussian, rgba(0,0,0,0.25), 16, 0, 0, 4);" +
                "-fx-border-color: #4a5568;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 12px;" +
                "-fx-background-radius: 12px;" +
                "-fx-min-width: 320px;" +
                "-fx-min-height: 400px;" +
                "}" +

                ".header-section {" +
                "-fx-background-color: #2d3748;" +
                "-fx-border-color: #4a5568;" +
                "-fx-border-width: 0 0 1 0;" +
                "-fx-background-radius: 12 12 0 0;" +
                "}" +

                ".sidebar-header {" +
                "-fx-font-family: 'SF Pro Display', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 20px;" +
                "-fx-font-weight: 600;" +
                "-fx-text-fill: #ffffff;" +
                "}" +

                ".sidebar-subtitle {" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 13px;" +
                "-fx-text-fill: #e2e8f0;" +
                "-fx-font-weight: 400;" +
                "}" +

                ".chat-area {" +
                "-fx-background-color: #4a5568;" +
                "-fx-border-color: #718096;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 8px;" +
                "-fx-background-radius: 8px;" +
                "-fx-padding: 16px;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 14px;" +
                "-fx-text-fill: #ffffff;" +
                "-fx-line-spacing: 4px;" +
                "}" +

                ".chat-scroll {" +
                "-fx-background-color: #4a5568;" +
                "-fx-border-color: transparent;" +
                "-fx-fit-to-width: true;" +
                "-fx-fit-to-height: true;" +
                "}" +

                ".scroll-pane {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".scroll-pane .viewport {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".scroll-pane .content {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".input-section {" +
                "-fx-background-color: #2d3748;" +
                "-fx-background-radius: 0 0 12 12;" +
                "-fx-border-color: #4a5568;" +
                "-fx-border-width: 1 0 0 0;" +
                "}" +

                ".input-container {" +
                "-fx-background-color: #4a5568;" +
                "-fx-background-radius: 8px;" +
                "-fx-border-color: #718096;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 8px;" +
                "-fx-padding: 6px;" +
                "-fx-min-height: 52px;" +
                "}" +

                ".message-input {" +
                "-fx-background-color: transparent;" +
                "-fx-border-color: transparent;" +
                "-fx-padding: 12 16 12 16;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 14px;" +
                "-fx-text-fill: #ffffff;" +
                "-fx-prompt-text-fill: #cbd5e0;" +
                "-fx-pref-height: 40px;" +
                "}" +

                ".send-button {" +
                "-fx-background-color: #3182ce;" +
                "-fx-text-fill: white;" +
                "-fx-border-radius: 6px;" +
                "-fx-background-radius: 6px;" +
                "-fx-padding: 10 16 10 16;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 14px;" +
                "-fx-font-weight: 500;" +
                "-fx-cursor: hand;" +
                "}" +

                ".send-button:hover {" +
                "-fx-background-color: #2c5aa0;" +
                "}" +

                ".upload-button {" +
                "-fx-background-color: #718096;" +
                "-fx-text-fill: #ffffff;" +
                "-fx-border-color: #a0aec0;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 6px;" +
                "-fx-background-radius: 6px;" +
                "-fx-padding: 8 8 8 8;" +
                "-fx-font-size: 16px;" +
                "-fx-cursor: hand;" +
                "-fx-min-width: 32px;" +
                "-fx-max-width: 32px;" +
                "-fx-pref-width: 32px;" +
                "-fx-min-height: 32px;" +
                "-fx-max-height: 32px;" +
                "-fx-pref-height: 32px;" +
                "}" +

                ".upload-button:hover {" +
                "-fx-background-color: #a0aec0;" +
                "-fx-text-fill: #ffffff;" +
                "}" +

                ".menu-button {" +
                "-fx-background-color: #f3f4f6;" +
                "-fx-border-color: #d1d5db;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 6px;" +
                "-fx-background-radius: 6px;" +
                "-fx-cursor: hand;" +
                "-fx-min-width: 40px;" +
                "-fx-pref-width: 40px;" +
                "-fx-min-height: 40px;" +
                "-fx-pref-height: 40px;" +
                "}" +

                ".menu-button:hover {" +
                "-fx-background-color: #e5e7eb;" +
                "}" +

                ".menu-button .arrow {" +
                "-fx-background-color: transparent;" +
                "}" +

                ".menu-button:showing {" +
                "-fx-background-color: #e5e7eb;" +
                "}" +

                ".context-menu {" +
                "-fx-font-size: 12px;" +
                "}" +

                ".context-menu .menu-item {" +
                "-fx-font-size: 12px;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "}" +

                ".context-menu .menu-item .label {" +
                "-fx-font-size: 12px;" +
                "}" +

                ".text-area {" +
                "-fx-background-color: #4a5568;" +
                "-fx-text-fill: #ffffff;" +
                "}" +

                ".text-area .content {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".text-area .scroll-pane {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".text-area .scroll-pane .viewport {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".text-area .scroll-pane .content {" +
                "-fx-background-color: #4a5568;" +
                "}" +

                ".action-button {" +
                "-fx-background-color: #f3f4f6;" +
                "-fx-text-fill: #374151;" +
                "-fx-border-color: #d1d5db;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 6px;" +
                "-fx-background-radius: 6px;" +
                "-fx-padding: 8 12 8 12;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 13px;" +
                "-fx-font-weight: 500;" +
                "-fx-cursor: hand;" +
                "}" +

                ".action-button:hover {" +
                "-fx-background-color: #e5e7eb;" +
                "}" +

                ".clear-button {" +
                "-fx-background-color: #fef3c7;" +
                "-fx-text-fill: #92400e;" +
                "-fx-border-color: #fcd34d;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 6px;" +
                "-fx-background-radius: 6px;" +
                "-fx-padding: 8 12 8 12;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 13px;" +
                "-fx-font-weight: 500;" +
                "-fx-cursor: hand;" +
                "}" +

                ".clear-button:hover {" +
                "-fx-background-color: #fef3c7;" +
                "-fx-border-color: #f59e0b;" +
                "}" +

                ".close-button {" +
                "-fx-background-color: #fef2f2;" +
                "-fx-text-fill: #dc2626;" +
                "-fx-border-color: #fca5a5;" +
                "-fx-border-width: 1px;" +
                "-fx-border-radius: 6px;" +
                "-fx-background-radius: 6px;" +
                "-fx-padding: 8 12 8 12;" +
                "-fx-font-family: 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;" +
                "-fx-font-size: 13px;" +
                "-fx-font-weight: 500;" +
                "-fx-cursor: hand;" +
                "}" +

                ".close-button:hover {" +
                "-fx-background-color: #fee2e2;" +
                "-fx-border-color: #f87171;" +
                "}";
    }
}
