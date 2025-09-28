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
import config.IChatConfig;

import java.awt.Desktop;
import java.net.URI;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * MCP Connection Dialog - Similar to Augment's repository configuration
 * Provides a clean interface for connecting to GitHub repositories via MCP
 */
public class MCPConnectionDialog {
    
    private Stage dialogStage;
    private IChatApiService apiService;
    private VBox mainContainer;
    private VBox providersList;
    private Label statusLabel;
    private ProgressIndicator loadingIndicator;
    
    // GitHub configuration fields
    private TextField clientIdField;
    private PasswordField clientSecretField;
    private TextField redirectUriField;
    private TextField scopeField;
    private Button connectButton;
    
    // Connection status
    private String currentConfigId;
    private boolean isConnected = false;

    // Status refresh timer
    private java.util.Timer statusTimer;
    
    public MCPConnectionDialog() {
        // Use regular chat API URL - the createMCPConnection method will handle MCP routing
        String apiUrl = IChatConfig.getApiUrl();
        this.apiService = new IChatApiService(apiUrl);
        initializeDialog();
        startStatusRefresh();
    }
    
    /**
     * Shows the MCP connection dialog
     */
    public void show() {
        if (dialogStage == null) {
            initializeDialog();
        }
        
        // Load available providers
        loadProviders();
        
        dialogStage.show();
        dialogStage.toFront();
        dialogStage.requestFocus();
    }
    
    /**
     * Initializes the dialog window and UI components
     */
    private void initializeDialog() {
        dialogStage = new Stage();
        dialogStage.initModality(Modality.APPLICATION_MODAL);
        dialogStage.initStyle(StageStyle.DECORATED);
        dialogStage.setTitle("Connect Repository - MCP Integration");
        dialogStage.setResizable(false);
        
        // Main container
        mainContainer = new VBox(20);
        mainContainer.setPadding(new Insets(30));
        mainContainer.setAlignment(Pos.TOP_CENTER);
        mainContainer.setStyle("-fx-background-color: #f8f9fa; -fx-border-color: #e9ecef; -fx-border-width: 1;");
        
        // Header
        createHeader();
        
        // Providers section
        createProvidersSection();
        
        // GitHub configuration section
        createGitHubConfigSection();
        
        // Status section
        createStatusSection();
        
        // Action buttons
        createActionButtons();
        
        // Scene setup
        Scene scene = new Scene(mainContainer, 600, 700);
        scene.getStylesheets().add(getClass().getResource("/ui/styles/mcp-dialog.css").toExternalForm());
        dialogStage.setScene(scene);
        
        // Center on screen
        dialogStage.centerOnScreen();
    }
    
    /**
     * Creates the header section
     */
    private void createHeader() {
        Label titleLabel = new Label("🔗 Connect Repository");
        titleLabel.setStyle("-fx-font-size: 24px; -fx-font-weight: bold; -fx-text-fill: #2c3e50;");
        
        Label subtitleLabel = new Label("Connect your GitHub repositories for intelligent code assistance");
        subtitleLabel.setStyle("-fx-font-size: 14px; -fx-text-fill: #6c757d;");
        
        VBox headerBox = new VBox(8);
        headerBox.setAlignment(Pos.CENTER);
        headerBox.getChildren().addAll(titleLabel, subtitleLabel);
        
        mainContainer.getChildren().add(headerBox);
    }
    
    /**
     * Creates the providers section
     */
    private void createProvidersSection() {
        Label providersLabel = new Label("Available Providers");
        providersLabel.setStyle("-fx-font-size: 16px; -fx-font-weight: bold; -fx-text-fill: #495057;");
        
        providersList = new VBox(10);
        providersList.setStyle("-fx-background-color: white; -fx-border-color: #dee2e6; -fx-border-radius: 8; -fx-padding: 15;");
        
        // Loading indicator
        loadingIndicator = new ProgressIndicator();
        loadingIndicator.setMaxSize(30, 30);
        loadingIndicator.setVisible(false);
        
        VBox providersSection = new VBox(10);
        providersSection.getChildren().addAll(providersLabel, providersList, loadingIndicator);
        
        mainContainer.getChildren().add(providersSection);
    }
    
    /**
     * Creates the GitHub configuration section
     */
    private void createGitHubConfigSection() {
        Label configLabel = new Label("GitHub OAuth Configuration");
        configLabel.setStyle("-fx-font-size: 16px; -fx-font-weight: bold; -fx-text-fill: #495057;");
        
        GridPane configGrid = new GridPane();
        configGrid.setHgap(15);
        configGrid.setVgap(12);
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
        redirectUriField.setPrefWidth(300);
        
        // Scope
        Label scopeLabel = new Label("Scopes:");
        scopeLabel.setStyle("-fx-font-weight: bold;");
        scopeField = new TextField("repo,read:user");
        scopeField.setPrefWidth(300);
        
        configGrid.add(clientIdLabel, 0, 0);
        configGrid.add(clientIdField, 1, 0);
        configGrid.add(clientSecretLabel, 0, 1);
        configGrid.add(clientSecretField, 1, 1);
        configGrid.add(redirectLabel, 0, 2);
        configGrid.add(redirectUriField, 1, 2);
        configGrid.add(scopeLabel, 0, 3);
        configGrid.add(scopeField, 1, 3);
        
        VBox configSection = new VBox(10);
        configSection.getChildren().addAll(configLabel, configGrid);
        
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
     * Creates the action buttons
     */
    private void createActionButtons() {
        connectButton = new Button("🔗 Connect to GitHub");
        connectButton.setStyle("-fx-background-color: #28a745; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 10 20;");
        connectButton.setOnAction(e -> connectToGitHub());
        
        Button cancelButton = new Button("❌ Cancel");
        cancelButton.setStyle("-fx-background-color: #6c757d; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 10 20;");
        cancelButton.setOnAction(e -> close());
        
        HBox buttonBox = new HBox(15);
        buttonBox.setAlignment(Pos.CENTER);
        buttonBox.getChildren().addAll(connectButton, cancelButton);
        
        mainContainer.getChildren().add(buttonBox);
    }
    
    /**
     * Loads available MCP providers
     */
    private void loadProviders() {
        loadingIndicator.setVisible(true);
        statusLabel.setText("Loading available providers...");
        
        CompletableFuture.supplyAsync(() -> {
            try {
                return apiService.getMCPProviders();
            } catch (Exception e) {
                Platform.runLater(() -> {
                    statusLabel.setText("❌ Error loading providers: " + e.getMessage());
                    statusLabel.setStyle("-fx-text-fill: #dc3545;");
                });
                return null;
            }
        }).thenAccept(result -> {
            Platform.runLater(() -> {
                loadingIndicator.setVisible(false);
                if (result != null) {
                    displayProviders(result);
                    statusLabel.setText("✅ Providers loaded successfully");
                    statusLabel.setStyle("-fx-text-fill: #28a745;");
                }
            });
        });
    }
    
    /**
     * Displays the available providers
     */
    private void displayProviders(Map<String, Object> response) {
        providersList.getChildren().clear();

        try {
            Object providersObj = response.get("providers");

            // Handle case where providers might be parsed as a string instead of map
            boolean hasGitHub = false;
            if (providersObj instanceof String) {
                String providersStr = (String) providersObj;
                hasGitHub = providersStr.contains("github");
            } else if (providersObj instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> providers = (Map<String, Object>) providersObj;
                hasGitHub = providers != null && providers.containsKey("github");
            }

            if (hasGitHub) {
                createGitHubProviderBox();
            }
        } catch (Exception e) {
            System.err.println("❌ Error displaying providers: " + e.getMessage());
            // Fallback: always show GitHub provider
            createGitHubProviderBox();
        }
    }

    /**
     * Creates the GitHub provider box UI element
     */
    private void createGitHubProviderBox() {
        HBox providerBox = new HBox(15);
        providerBox.setAlignment(Pos.CENTER_LEFT);
        providerBox.setStyle("-fx-padding: 10; -fx-border-color: #28a745; -fx-border-radius: 5; -fx-background-color: #f8fff9;");

        Label providerIcon = new Label("🐙");
        providerIcon.setStyle("-fx-font-size: 24px;");

        VBox providerInfo = new VBox(5);
        Label providerName = new Label("GitHub");
        providerName.setStyle("-fx-font-size: 16px; -fx-font-weight: bold;");

        Label providerDesc = new Label("Connect to GitHub repositories and perform Git operations");
        providerDesc.setStyle("-fx-font-size: 12px; -fx-text-fill: #6c757d;");
        providerDesc.setWrapText(true);

        providerInfo.getChildren().addAll(providerName, providerDesc);

        Label statusIcon = new Label(isConnected ? "✅" : "⚪");
        statusIcon.setStyle("-fx-font-size: 20px;");

        providerBox.getChildren().addAll(providerIcon, providerInfo, statusIcon);
        HBox.setHgrow(providerInfo, Priority.ALWAYS);

        providersList.getChildren().add(providerBox);
    }
    
    /**
     * Saves the GitHub OAuth configuration
     */
    private void saveConfiguration() {
        if (clientIdField.getText().trim().isEmpty() || clientSecretField.getText().trim().isEmpty()) {
            statusLabel.setText("❌ Please fill in Client ID and Client Secret");
            statusLabel.setStyle("-fx-text-fill: #dc3545;");
            return;
        }
        
        connectButton.setDisable(true);
        statusLabel.setText("💾 Saving configuration...");
        statusLabel.setStyle("-fx-text-fill: #007bff;");
        
        Map<String, String> config = new HashMap<>();
        config.put("client_id", clientIdField.getText().trim());
        config.put("client_secret", clientSecretField.getText().trim());
        config.put("redirect_uri", redirectUriField.getText().trim());
        config.put("scope", scopeField.getText().trim());
        
        CompletableFuture.supplyAsync(() -> {
            try {
                return apiService.configureMCPProvider("github", config);
            } catch (Exception e) {
                Platform.runLater(() -> {
                    statusLabel.setText("❌ Error saving configuration: " + e.getMessage());
                    statusLabel.setStyle("-fx-text-fill: #dc3545;");
                    connectButton.setDisable(false);
                });
                return null;
            }
        }).thenAccept(result -> {
            Platform.runLater(() -> {
                connectButton.setDisable(false);
                if (result != null) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> response = (Map<String, Object>) result;
                    currentConfigId = (String) response.get("config_id");
                    
                    statusLabel.setText("✅ Configuration saved successfully!");
                    statusLabel.setStyle("-fx-text-fill: #28a745;");
                }
            });
        });
    }
    
    /**
     * Starts the OAuth authentication flow
     */
    private void startOAuthFlow() {
        if (currentConfigId == null) {
            statusLabel.setText("❌ Please save configuration first");
            statusLabel.setStyle("-fx-text-fill: #dc3545;");
            return;
        }
        

        statusLabel.setText("🔗 Starting OAuth flow...");
        statusLabel.setStyle("-fx-text-fill: #007bff;");
        
        Map<String, String> authRequest = new HashMap<>();
        authRequest.put("config_id", currentConfigId);
        
        CompletableFuture.supplyAsync(() -> {
            try {
                return apiService.startMCPOAuth("github", authRequest);
            } catch (Exception e) {
                Platform.runLater(() -> {
                    statusLabel.setText("❌ Error starting OAuth: " + e.getMessage());
                    statusLabel.setStyle("-fx-text-fill: #dc3545;");

                });
                return null;
            }
        }).thenAccept(result -> {
            Platform.runLater(() -> {

                if (result != null) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> response = (Map<String, Object>) result;
                    String authUrl = (String) response.get("auth_url");
                    
                    statusLabel.setText("✅ OAuth URL generated! Opening browser...");
                    statusLabel.setStyle("-fx-text-fill: #28a745;");
                    
                    // Open browser with OAuth URL
                    try {
                        java.awt.Desktop.getDesktop().browse(java.net.URI.create(authUrl));
                        
                        // Show success message
                        Alert alert = new Alert(Alert.AlertType.INFORMATION);
                        alert.setTitle("OAuth Flow Started");
                        alert.setHeaderText("GitHub Authorization");
                        alert.setContentText("Your browser has been opened for GitHub authorization.\n\n" +
                                           "After authorizing, you'll be redirected back and the connection will be established.");
                        alert.showAndWait();
                        
                    } catch (Exception e) {
                        statusLabel.setText("❌ Error opening browser: " + e.getMessage());
                        statusLabel.setStyle("-fx-text-fill: #dc3545;");
                    }
                }
            });
        });
    }

    /**
     * Connects to GitHub by saving configuration and starting OAuth flow in one step
     */
    private void connectToGitHub() {
        // Validate input fields
        if (clientIdField.getText().trim().isEmpty() || clientSecretField.getText().trim().isEmpty()) {
            statusLabel.setText("❌ Please fill in Client ID and Client Secret");
            statusLabel.setStyle("-fx-text-fill: #dc3545;");
            return;
        }

        connectButton.setDisable(true);
        statusLabel.setText("🔄 Connecting to GitHub...");
        statusLabel.setStyle("-fx-text-fill: #007bff;");

        // Step 1: Save configuration
        Map<String, String> config = new HashMap<>();
        config.put("client_id", clientIdField.getText().trim());
        config.put("client_secret", clientSecretField.getText().trim());
        config.put("redirect_uri", redirectUriField.getText().trim());
        config.put("scope", scopeField.getText().trim());

        CompletableFuture.supplyAsync(() -> {
            try {
                return apiService.configureMCPProvider("github", config);
            } catch (Exception e) {
                Platform.runLater(() -> {
                    statusLabel.setText("❌ Error saving configuration: " + e.getMessage());
                    statusLabel.setStyle("-fx-text-fill: #dc3545;");
                    connectButton.setDisable(false);
                });
                return null;
            }
        }).thenCompose(configResult -> {
            if (configResult == null) {
                return CompletableFuture.completedFuture(null);
            }

            // Step 2: Start OAuth flow
            Platform.runLater(() -> {
                statusLabel.setText("🔗 Starting GitHub authorization...");
                statusLabel.setStyle("-fx-text-fill: #007bff;");
            });

            @SuppressWarnings("unchecked")
            Map<String, Object> response = (Map<String, Object>) configResult;
            currentConfigId = (String) response.get("config_id");

            Map<String, String> authRequest = new HashMap<>();
            authRequest.put("config_id", currentConfigId);

            return CompletableFuture.supplyAsync(() -> {
                try {
                    return apiService.startMCPOAuth("github", authRequest);
                } catch (Exception e) {
                    Platform.runLater(() -> {
                        statusLabel.setText("❌ Error starting OAuth: " + e.getMessage());
                        statusLabel.setStyle("-fx-text-fill: #dc3545;");
                        connectButton.setDisable(false);
                    });
                    return null;
                }
            });
        }).thenAccept(oauthResult -> {
            Platform.runLater(() -> {
                connectButton.setDisable(false);
                if (oauthResult != null) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> response = (Map<String, Object>) oauthResult;
                    String authUrl = (String) response.get("auth_url");

                    if (authUrl != null) {
                        statusLabel.setText("✅ Opening GitHub authorization in browser...");
                        statusLabel.setStyle("-fx-text-fill: #28a745;");

                        try {
                            Desktop.getDesktop().browse(new URI(authUrl));

                            Alert alert = new Alert(Alert.AlertType.INFORMATION);
                            alert.setTitle("GitHub Authorization");
                            alert.setHeaderText("GitHub Authorization");
                            alert.setContentText("Your browser has been opened for GitHub authorization.\n\n" +
                                               "After authorizing, you'll be redirected back and the connection will be established.\n\n" +
                                               "The dialog will automatically update when the connection is complete.");
                            alert.showAndWait();

                            // Trigger immediate status refresh after user closes the alert
                            CompletableFuture.runAsync(() -> {
                                try {
                                    Thread.sleep(3000); // Wait 3 seconds for user to complete OAuth
                                    refreshConnectionStatus();
                                } catch (InterruptedException ignored) {}
                            });

                        } catch (Exception e) {
                            statusLabel.setText("❌ Error opening browser: " + e.getMessage());
                            statusLabel.setStyle("-fx-text-fill: #dc3545;");
                        }
                    } else {
                        statusLabel.setText("❌ No authorization URL received");
                        statusLabel.setStyle("-fx-text-fill: #dc3545;");
                    }
                } else {
                    statusLabel.setText("❌ Failed to start GitHub authorization");
                    statusLabel.setStyle("-fx-text-fill: #dc3545;");
                }
            });
        });
    }

    /**
     * Start periodic status refresh to check for OAuth completion
     */
    private void startStatusRefresh() {
        statusTimer = new java.util.Timer(true); // daemon thread
        statusTimer.scheduleAtFixedRate(new java.util.TimerTask() {
            @Override
            public void run() {
                refreshConnectionStatus();
            }
        }, 2000, 5000); // Check every 5 seconds, start after 2 seconds
    }

    /**
     * Refresh the GitHub connection status
     */
    private void refreshConnectionStatus() {
        CompletableFuture.supplyAsync(() -> {
            return apiService.isGitHubConnected();
        }).thenAccept(connected -> {
            Platform.runLater(() -> {
                if (connected != isConnected) {
                    isConnected = connected;
                    loadProviders(); // Refresh the providers list to show updated status

                    if (connected) {
                        statusLabel.setText("✅ GitHub successfully connected!");
                        statusLabel.setStyle("-fx-text-fill: #28a745;");
                    }
                }
            });
        }).exceptionally(throwable -> {
            // Silently handle errors in background status checks
            return null;
        });
    }

    /**
     * Stop the status refresh timer when dialog is closed
     */
    public void close() {
        if (statusTimer != null) {
            statusTimer.cancel();
        }
        dialogStage.close();
    }
}
