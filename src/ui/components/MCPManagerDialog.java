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

import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * Main MCP Management Dialog - Shows all available MCP providers
 */
public class MCPManagerDialog {
    
    private Stage dialogStage;
    private IChatApiService apiService;
    private VBox mainContainer;
    private VBox providersList;
    private Label statusLabel;
    private ProgressIndicator loadingIndicator;
    
    // Status refresh timer
    private java.util.Timer statusTimer;
    
    public MCPManagerDialog(IChatApiService apiService) {
        this.apiService = apiService;
    }
    
    /**
     * Show the MCP Manager dialog
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
        
        // Start status refresh
        startStatusRefresh();
    }
    
    /**
     * Initialize the dialog UI
     */
    private void initializeDialog() {
        dialogStage = new Stage();
        dialogStage.initModality(Modality.APPLICATION_MODAL);
        dialogStage.initStyle(StageStyle.DECORATED);
        dialogStage.setTitle("MCP Provider Management");
        dialogStage.setResizable(true);
        dialogStage.setMinWidth(500);
        dialogStage.setMinHeight(400);
        
        // Main container
        mainContainer = new VBox(20);
        mainContainer.setPadding(new Insets(30));
        mainContainer.setAlignment(Pos.TOP_CENTER);
        mainContainer.setStyle("-fx-background-color: #f8f9fa; -fx-border-color: #e9ecef; -fx-border-width: 1;");
        
        // Header
        createHeader();
        
        // Providers section
        createProvidersSection();
        
        // Status section
        createStatusSection();
        
        // Buttons section
        createButtonsSection();
        
        // Set up scene
        Scene scene = new Scene(mainContainer, 600, 500);
        dialogStage.setScene(scene);
        
        // Handle close event
        dialogStage.setOnCloseRequest(e -> close());
    }
    
    /**
     * Creates the header section
     */
    private void createHeader() {
        Label titleLabel = new Label("🔗 MCP Provider Management");
        titleLabel.setStyle("-fx-font-size: 24px; -fx-font-weight: bold; -fx-text-fill: #212529;");
        
        Label subtitleLabel = new Label("Manage connections to Model Context Protocol providers");
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
        providersLabel.setStyle("-fx-font-size: 18px; -fx-font-weight: bold; -fx-text-fill: #495057;");
        
        providersList = new VBox(15);
        providersList.setStyle("-fx-background-color: white; -fx-border-color: #dee2e6; -fx-border-radius: 8; -fx-padding: 20;");
        
        // Loading indicator
        loadingIndicator = new ProgressIndicator();
        loadingIndicator.setMaxSize(40, 40);
        loadingIndicator.setVisible(false);
        
        VBox providersSection = new VBox(15);
        providersSection.getChildren().addAll(providersLabel, providersList, loadingIndicator);
        
        mainContainer.getChildren().add(providersSection);
        VBox.setVgrow(providersSection, Priority.ALWAYS);
    }
    
    /**
     * Creates the status section
     */
    private void createStatusSection() {
        statusLabel = new Label("Ready to manage MCP providers");
        statusLabel.setStyle("-fx-font-size: 12px; -fx-text-fill: #6c757d; -fx-padding: 10;");
        statusLabel.setWrapText(true);
        
        mainContainer.getChildren().add(statusLabel);
    }
    
    /**
     * Creates the buttons section
     */
    private void createButtonsSection() {
        Button refreshButton = new Button("🔄 Refresh");
        refreshButton.setStyle("-fx-background-color: #007bff; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 10 20;");
        refreshButton.setOnAction(e -> loadProviders());
        
        Button closeButton = new Button("❌ Close");
        closeButton.setStyle("-fx-background-color: #6c757d; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 10 20;");
        closeButton.setOnAction(e -> close());
        
        HBox buttonBox = new HBox(15);
        buttonBox.setAlignment(Pos.CENTER);
        buttonBox.getChildren().addAll(refreshButton, closeButton);
        
        mainContainer.getChildren().add(buttonBox);
    }
    
    /**
     * Loads available MCP providers
     */
    private void loadProviders() {
        loadingIndicator.setVisible(true);
        statusLabel.setText("Loading available providers...");
        statusLabel.setStyle("-fx-text-fill: #6c757d;");
        
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
            // Always show GitHub provider (it's the main one we support)
            createGitHubProviderCard();
            
            // TODO: Add other providers here as they become available
            
        } catch (Exception e) {
            System.err.println("❌ Error displaying providers: " + e.getMessage());
            statusLabel.setText("❌ Error displaying providers: " + e.getMessage());
            statusLabel.setStyle("-fx-text-fill: #dc3545;");
        }
    }
    
    /**
     * Creates the GitHub provider card
     */
    private void createGitHubProviderCard() {
        // Check connection status
        boolean isConnected = apiService.isGitHubConnected();
        
        VBox providerCard = new VBox(15);
        providerCard.setStyle("-fx-background-color: white; -fx-border-color: " + 
                             (isConnected ? "#28a745" : "#dee2e6") + 
                             "; -fx-border-radius: 8; -fx-padding: 20; -fx-effect: dropshadow(gaussian, rgba(0,0,0,0.1), 5, 0, 0, 2);");
        
        // Header with icon and status
        HBox headerBox = new HBox(15);
        headerBox.setAlignment(Pos.CENTER_LEFT);
        
        Label providerIcon = new Label("🐙");
        providerIcon.setStyle("-fx-font-size: 32px;");
        
        VBox providerInfo = new VBox(5);
        Label providerName = new Label("GitHub");
        providerName.setStyle("-fx-font-size: 20px; -fx-font-weight: bold; -fx-text-fill: #212529;");
        
        Label providerDesc = new Label("Connect to GitHub repositories for code analysis and operations");
        providerDesc.setStyle("-fx-font-size: 14px; -fx-text-fill: #6c757d;");
        providerDesc.setWrapText(true);
        
        providerInfo.getChildren().addAll(providerName, providerDesc);
        
        Label statusIcon = new Label(isConnected ? "✅ Connected" : "⚪ Not Connected");
        statusIcon.setStyle("-fx-font-size: 14px; -fx-font-weight: bold; -fx-text-fill: " + 
                           (isConnected ? "#28a745" : "#6c757d") + ";");
        
        headerBox.getChildren().addAll(providerIcon, providerInfo, statusIcon);
        HBox.setHgrow(providerInfo, Priority.ALWAYS);
        
        // Action buttons
        HBox actionBox = new HBox(10);
        actionBox.setAlignment(Pos.CENTER_RIGHT);
        
        if (isConnected) {
            Button disconnectButton = new Button("🔌 Disconnect");
            disconnectButton.setStyle("-fx-background-color: #dc3545; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 8 16;");
            disconnectButton.setOnAction(e -> disconnectGitHub());
            
            Button manageButton = new Button("⚙️ Manage");
            manageButton.setStyle("-fx-background-color: #6c757d; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 8 16;");
            manageButton.setOnAction(e -> openGitHubConfig());
            
            actionBox.getChildren().addAll(manageButton, disconnectButton);
        } else {
            Button connectButton = new Button("🔗 Connect");
            connectButton.setStyle("-fx-background-color: #28a745; -fx-text-fill: white; -fx-font-weight: bold; -fx-padding: 8 16;");
            connectButton.setOnAction(e -> openGitHubConfig());
            
            actionBox.getChildren().add(connectButton);
        }
        
        providerCard.getChildren().addAll(headerBox, actionBox);
        providersList.getChildren().add(providerCard);
    }
    
    /**
     * Opens the GitHub configuration dialog
     */
    private void openGitHubConfig() {
        GitHubMCPConfig githubConfig = new GitHubMCPConfig(apiService);
        githubConfig.show();
        
        // Refresh providers list when config dialog closes
        githubConfig.setOnCloseCallback(() -> {
            loadProviders(); // Refresh the providers list
        });
    }
    
    /**
     * Disconnects from GitHub by revoking all tokens
     */
    private void disconnectGitHub() {
        Alert confirmAlert = new Alert(Alert.AlertType.CONFIRMATION);
        confirmAlert.setTitle("Disconnect GitHub");
        confirmAlert.setHeaderText("Disconnect from GitHub?");
        confirmAlert.setContentText("This will revoke all GitHub OAuth tokens. You'll need to reconnect to use GitHub features.\n\nThis action cannot be undone.");

        confirmAlert.showAndWait().ifPresent(response -> {
            if (response == ButtonType.OK) {
                statusLabel.setText("🔄 Disconnecting from GitHub...");
                statusLabel.setStyle("-fx-text-fill: #6c757d;");

                // Perform actual token revocation
                CompletableFuture.supplyAsync(() -> {
                    try {
                        return apiService.revokeAllTokens("github");
                    } catch (Exception e) {
                        Platform.runLater(() -> {
                            statusLabel.setText("❌ Disconnect failed: " + e.getMessage());
                            statusLabel.setStyle("-fx-text-fill: #dc3545;");
                        });
                        return null;
                    }
                }).thenAccept(result -> {
                    Platform.runLater(() -> {
                        if (result != null && "success".equals(result.get("status"))) {
                            int revokedCount = result.get("revoked_count") instanceof Number ?
                                ((Number) result.get("revoked_count")).intValue() : 0;

                            statusLabel.setText("✅ Disconnected from GitHub - " + revokedCount + " tokens revoked");
                            statusLabel.setStyle("-fx-text-fill: #28a745;");

                            // Show success alert
                            Alert successAlert = new Alert(Alert.AlertType.INFORMATION);
                            successAlert.setTitle("GitHub Disconnected");
                            successAlert.setHeaderText("Successfully disconnected from GitHub");
                            successAlert.setContentText("Revoked " + revokedCount + " OAuth tokens.\n\nYou can reconnect anytime by clicking the Connect button.");
                            successAlert.showAndWait();

                        } else {
                            String error = result != null ? (String) result.get("error") : "Unknown error";
                            statusLabel.setText("❌ Disconnect failed: " + error);
                            statusLabel.setStyle("-fx-text-fill: #dc3545;");
                        }

                        // Refresh the providers list to show updated status
                        loadProviders();
                    });
                });
            }
        });
    }
    
    /**
     * Start periodic status refresh
     */
    private void startStatusRefresh() {
        statusTimer = new java.util.Timer(true); // daemon thread
        statusTimer.scheduleAtFixedRate(new java.util.TimerTask() {
            @Override
            public void run() {
                Platform.runLater(() -> loadProviders());
            }
        }, 5000, 10000); // Check every 10 seconds, start after 5 seconds
    }
    
    /**
     * Close the dialog and cleanup resources
     */
    public void close() {
        if (statusTimer != null) {
            statusTimer.cancel();
        }
        if (dialogStage != null) {
            dialogStage.close();
        }
    }
}
