package ui.components;

import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.Modality;
import javafx.stage.Stage;
import javafx.stage.StageStyle;
import api.IChatApiService;

import java.awt.Desktop;
import java.net.URI;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * GitHub MCP Configuration Dialog - Handles GitHub OAuth setup
 */
public class GitHubMCPConfig {
    
    private Stage dialogStage;
    private IChatApiService apiService;
    private VBox mainContainer;
    private Label statusLabel;
    
    // GitHub configuration fields
    private TextField clientIdField;
    private PasswordField clientSecretField;
    private TextField redirectUriField;
    private TextField scopeField;
    private Button connectButton;
    
    // Connection status
    private String currentConfigId;
    private boolean isConnected = false;
    
    // Callback for when dialog closes
    private Runnable onCloseCallback;
    
    public GitHubMCPConfig(IChatApiService apiService) {
        this.apiService = apiService;
        this.isConnected = apiService.isGitHubConnected();
    }
    
    /**
     * Show the GitHub configuration dialog
     */
    public void show() {
        if (dialogStage == null) {
            initializeDialog();
        }
        
        dialogStage.show();
        dialogStage.toFront();
        dialogStage.requestFocus();
    }
    
    /**
     * Set callback to run when dialog closes
     */
    public void setOnCloseCallback(Runnable callback) {
        this.onCloseCallback = callback;
    }
    
    /**
     * Initialize the dialog UI
     */
    private void initializeDialog() {
        dialogStage = new Stage();
        dialogStage.initModality(Modality.APPLICATION_MODAL);
        dialogStage.initStyle(StageStyle.DECORATED);
        dialogStage.setTitle("GitHub MCP Configuration");
        dialogStage.setResizable(false);
        
        // Main container
        mainContainer = new VBox(20);
        mainContainer.setPadding(new Insets(30));
        mainContainer.setAlignment(Pos.TOP_CENTER);
        mainContainer.setStyle("-fx-background-color: #f8f9fa; -fx-border-color: #e9ecef; -fx-border-width: 1;");
        
        // Header
        createHeader();
        
        // Configuration form
        createConfigurationForm();
        
        // Status section
        createStatusSection();
        
        // Buttons section
        createButtonsSection();
        
        // Set up scene
        Scene scene = new Scene(mainContainer, 500, 600);
        dialogStage.setScene(scene);
        
        // Handle close event
        dialogStage.setOnCloseRequest(e -> close());
    }
    
    /**
     * Creates the header section
     */
    private void createHeader() {
        Label titleLabel = new Label("🐙 GitHub Configuration");
        titleLabel.setStyle("-fx-font-size: 22px; -fx-font-weight: bold; -fx-text-fill: #212529;");
        
        Label subtitleLabel = new Label("Configure OAuth credentials to connect to GitHub");
        subtitleLabel.setStyle("-fx-font-size: 14px; -fx-text-fill: #6c757d;");
        
        // Connection status indicator
        Label connectionStatus = new Label(isConnected ? "✅ Currently Connected" : "⚪ Not Connected");
        connectionStatus.setStyle("-fx-font-size: 14px; -fx-font-weight: bold; -fx-text-fill: " + 
                                 (isConnected ? "#28a745" : "#6c757d") + "; -fx-padding: 10 0;");
        
        VBox headerBox = new VBox(8);
        headerBox.setAlignment(Pos.CENTER);
        headerBox.getChildren().addAll(titleLabel, subtitleLabel, connectionStatus);
        
        mainContainer.getChildren().add(headerBox);
    }
    
    /**
     * Creates the configuration form
     */
    private void createConfigurationForm() {
        Label configLabel = new Label("OAuth Configuration");
        configLabel.setStyle("-fx-font-size: 16px; -fx-font-weight: bold; -fx-text-fill: #495057;");
        
        GridPane configGrid = new GridPane();
        configGrid.setHgap(15);
        configGrid.setVgap(15);
        configGrid.setPadding(new Insets(15));
        configGrid.setStyle("-fx-background-color: white; -fx-border-color: #dee2e6; -fx-border-radius: 8;");
        
        // Client ID
        Label clientIdLabel = new Label("Client ID:");
        clientIdLabel.setStyle("-fx-font-weight: bold;");
        clientIdField = new TextField();
        clientIdField.setPromptText("Your GitHub OAuth App Client ID");
        clientIdField.setPrefWidth(300);
        
        // Client Secret
        Label clientSecretLabel = new Label("Client Secret:");
        clientSecretLabel.setStyle("-fx-font-weight: bold;");
        clientSecretField = new PasswordField();
        clientSecretField.setPromptText("Your GitHub OAuth App Client Secret");
        clientSecretField.setPrefWidth(300);
        
        // Redirect URI
        Label redirectLabel = new Label("Redirect URI:");
        redirectLabel.setStyle("-fx-font-weight: bold;");
        redirectUriField = new TextField("http://localhost:8080/api/mcp/oauth/github/callback");
        redirectUriField.setEditable(false);
        redirectUriField.setStyle("-fx-background-color: #f8f9fa;");
        redirectUriField.setPrefWidth(300);
        
        // Scopes
        Label scopeLabel = new Label("Scopes:");
        scopeLabel.setStyle("-fx-font-weight: bold;");
        scopeField = new TextField("repo,read:user");
        scopeField.setPrefWidth(300);
        
        // Add to grid
        configGrid.add(clientIdLabel, 0, 0);
        configGrid.add(clientIdField, 1, 0);
        configGrid.add(clientSecretLabel, 0, 1);
        configGrid.add(clientSecretField, 1, 1);
        configGrid.add(redirectLabel, 0, 2);
        configGrid.add(redirectUriField, 1, 2);
        configGrid.add(scopeLabel, 0, 3);
        configGrid.add(scopeField, 1, 3);
        
        // Instructions
        Label instructionsLabel = new Label("Instructions:");
        instructionsLabel.setStyle("-fx-font-weight: bold; -fx-text-fill: #495057;");
        
        TextArea instructionsText = new TextArea();
        instructionsText.setText("1. Go to GitHub Settings → Developer settings → OAuth Apps\n" +
                               "2. Create a new OAuth App or use existing one\n" +
                               "3. Set Authorization callback URL to: " + redirectUriField.getText() + "\n" +
                               "4. Copy Client ID and Client Secret from your OAuth App\n" +
                               "5. Paste them above and click 'Connect to GitHub'");
        instructionsText.setEditable(false);
        instructionsText.setPrefRowCount(5);
        instructionsText.setWrapText(true);
        instructionsText.setStyle("-fx-background-color: #e9ecef; -fx-border-color: #ced4da; -fx-border-radius: 4;");
        
        VBox configSection = new VBox(15);
        configSection.getChildren().addAll(configLabel, configGrid, instructionsLabel, instructionsText);
        
        mainContainer.getChildren().add(configSection);
    }
    
    /**
     * Creates the status section
     */
    private void createStatusSection() {
        statusLabel = new Label("Ready to configure GitHub connection");
        statusLabel.setStyle("-fx-font-size: 12px; -fx-text-fill: #6c757d; -fx-padding: 10;");
        statusLabel.setWrapText(true);
        
        mainContainer.getChildren().add(statusLabel);
    }
    
    /**
     * Creates the buttons section
     */
    private void createButtonsSection() {
        connectButton = new Button(isConnected ? "🔄 Reconfigure" : "🔗 Connect to GitHub");
        connectButton.setStyle("-fx-background-color: #28a745; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 12 24;");
        connectButton.setOnAction(e -> connectToGitHub());
        
        Button cancelButton = new Button("❌ Cancel");
        cancelButton.setStyle("-fx-background-color: #6c757d; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 12 24;");
        cancelButton.setOnAction(e -> close());
        
        HBox buttonBox = new HBox(15);
        buttonBox.setAlignment(Pos.CENTER);
        buttonBox.getChildren().addAll(connectButton, cancelButton);
        
        mainContainer.getChildren().add(buttonBox);
    }
    
    /**
     * Handles the GitHub connection process
     */
    private void connectToGitHub() {
        String clientId = clientIdField.getText().trim();
        String clientSecret = clientSecretField.getText().trim();
        String redirectUri = redirectUriField.getText().trim();
        String scope = scopeField.getText().trim();
        
        // Validate inputs
        if (clientId.isEmpty() || clientSecret.isEmpty()) {
            statusLabel.setText("❌ Please enter both Client ID and Client Secret");
            statusLabel.setStyle("-fx-text-fill: #dc3545;");
            return;
        }
        
        statusLabel.setText("🔄 Configuring GitHub OAuth...");
        statusLabel.setStyle("-fx-text-fill: #6c757d;");
        connectButton.setDisable(true);
        
        // Step 1: Configure OAuth
        CompletableFuture.supplyAsync(() -> {
            try {
                return apiService.configureMCPProvider("github", clientId, clientSecret, redirectUri, scope);
            } catch (Exception e) {
                Platform.runLater(() -> {
                    statusLabel.setText("❌ Configuration failed: " + e.getMessage());
                    statusLabel.setStyle("-fx-text-fill: #dc3545;");
                    connectButton.setDisable(false);
                });
                return null;
            }
        }).thenAccept(configResult -> {
            if (configResult != null && "success".equals(configResult.get("status"))) {
                currentConfigId = (String) configResult.get("config_id");
                
                Platform.runLater(() -> {
                    statusLabel.setText("✅ Configuration saved. Starting OAuth flow...");
                    statusLabel.setStyle("-fx-text-fill: #28a745;");
                });
                
                // Step 2: Start OAuth flow
                CompletableFuture.supplyAsync(() -> {
                    try {
                        return apiService.startMCPOAuth("github", currentConfigId);
                    } catch (Exception e) {
                        Platform.runLater(() -> {
                            statusLabel.setText("❌ OAuth start failed: " + e.getMessage());
                            statusLabel.setStyle("-fx-text-fill: #dc3545;");
                            connectButton.setDisable(false);
                        });
                        return null;
                    }
                }).thenAccept(authResult -> {
                    Platform.runLater(() -> {
                        connectButton.setDisable(false);
                        
                        if (authResult != null && "success".equals(authResult.get("status"))) {
                            String authUrl = (String) authResult.get("auth_url");
                            
                            // Open browser for OAuth
                            try {
                                Desktop.getDesktop().browse(new URI(authUrl));
                                
                                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                                alert.setTitle("GitHub Authorization");
                                alert.setHeaderText("Complete GitHub Authorization");
                                alert.setContentText("Your browser has been opened for GitHub authorization.\n\n" +
                                                   "After authorizing, you'll be redirected back and the connection will be established.\n\n" +
                                                   "This dialog will automatically close when the connection is complete.");
                                alert.showAndWait();
                                
                                // Start monitoring for connection completion
                                startConnectionMonitoring();
                                
                            } catch (Exception e) {
                                statusLabel.setText("❌ Failed to open browser: " + e.getMessage());
                                statusLabel.setStyle("-fx-text-fill: #dc3545;");
                            }
                        } else {
                            statusLabel.setText("❌ Failed to start OAuth flow");
                            statusLabel.setStyle("-fx-text-fill: #dc3545;");
                        }
                    });
                });
            }
        });
    }
    
    /**
     * Monitor for connection completion and auto-close dialog
     */
    private void startConnectionMonitoring() {
        java.util.Timer monitorTimer = new java.util.Timer(true);
        monitorTimer.scheduleAtFixedRate(new java.util.TimerTask() {
            private int attempts = 0;
            private final int maxAttempts = 30; // Monitor for 30 seconds
            
            @Override
            public void run() {
                attempts++;
                
                boolean connected = apiService.isGitHubConnected();
                
                Platform.runLater(() -> {
                    if (connected) {
                        statusLabel.setText("✅ GitHub successfully connected! Closing dialog...");
                        statusLabel.setStyle("-fx-text-fill: #28a745;");
                        
                        // Close dialog after short delay
                        CompletableFuture.runAsync(() -> {
                            try {
                                Thread.sleep(2000);
                            } catch (InterruptedException ignored) {}
                        }).thenRun(() -> Platform.runLater(() -> close()));
                        
                        monitorTimer.cancel();
                    } else if (attempts >= maxAttempts) {
                        statusLabel.setText("⏱️ Connection monitoring timed out. Please check manually.");
                        statusLabel.setStyle("-fx-text-fill: #ffc107;");
                        monitorTimer.cancel();
                    }
                });
            }
        }, 2000, 1000); // Check every second, start after 2 seconds
    }
    
    /**
     * Close the dialog and run callback
     */
    public void close() {
        if (onCloseCallback != null) {
            onCloseCallback.run();
        }
        if (dialogStage != null) {
            dialogStage.close();
        }
    }
}
