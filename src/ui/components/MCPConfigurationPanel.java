package ui.components;

import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import api.IChatApiService;

/**
 * MCP Configuration Panel - UI for configuring MCP (Model Context Protocol) providers
 */
public class MCPConfigurationPanel extends JPanel {
    
    private final IChatApiService apiService;
    private JComboBox<String> providerComboBox;
    private JPanel configFieldsPanel;
    private JButton configureButton;
    private JButton authenticateButton;
    private JTextArea statusArea;
    private Map<String, JTextField> configFields;
    
    // GitHub OAuth configuration fields
    private JTextField clientIdField;
    private JPasswordField clientSecretField;
    private JTextField redirectUriField;
    private JTextField scopeField;
    
    public MCPConfigurationPanel() {
        this.apiService = new IChatApiService();
        this.configFields = new HashMap<>();
        
        initializeComponents();
        setupLayout();
        setupEventHandlers();
        loadProviders();
    }
    
    private void initializeComponents() {
        // Provider selection
        providerComboBox = new JComboBox<>();
        providerComboBox.addItem("Select MCP Provider...");
        providerComboBox.addItem("github");
        
        // Configuration fields panel
        configFieldsPanel = new JPanel(new GridBagLayout());
        configFieldsPanel.setBorder(new TitledBorder("Configuration"));
        
        // Buttons
        configureButton = new JButton("Configure Provider");
        configureButton.setEnabled(false);
        
        authenticateButton = new JButton("Start Authentication");
        authenticateButton.setEnabled(false);
        
        // Status area
        statusArea = new JTextArea(5, 40);
        statusArea.setEditable(false);
        statusArea.setBackground(getBackground());
        statusArea.setBorder(new TitledBorder("Status"));
        
        // Initialize GitHub fields
        clientIdField = new JTextField(30);
        clientSecretField = new JPasswordField(30);
        redirectUriField = new JTextField(30);
        redirectUriField.setText("http://localhost:8080/api/mcp/oauth/github/callback");
        scopeField = new JTextField(30);
        scopeField.setText("repo,read:user");
    }
    
    private void setupLayout() {
        setLayout(new BorderLayout());
        
        // Top panel - Provider selection
        JPanel topPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        topPanel.add(new JLabel("MCP Provider:"));
        topPanel.add(providerComboBox);
        
        // Center panel - Configuration fields
        JScrollPane configScrollPane = new JScrollPane(configFieldsPanel);
        configScrollPane.setPreferredSize(new Dimension(500, 200));
        
        // Bottom panel - Buttons and status
        JPanel bottomPanel = new JPanel(new BorderLayout());
        
        JPanel buttonPanel = new JPanel(new FlowLayout());
        buttonPanel.add(configureButton);
        buttonPanel.add(authenticateButton);
        
        bottomPanel.add(buttonPanel, BorderLayout.NORTH);
        bottomPanel.add(new JScrollPane(statusArea), BorderLayout.CENTER);
        
        add(topPanel, BorderLayout.NORTH);
        add(configScrollPane, BorderLayout.CENTER);
        add(bottomPanel, BorderLayout.SOUTH);
    }
    
    private void setupEventHandlers() {
        providerComboBox.addActionListener(e -> {
            String selectedProvider = (String) providerComboBox.getSelectedItem();
            if (selectedProvider != null && !selectedProvider.startsWith("Select")) {
                showConfigurationFields(selectedProvider);
                configureButton.setEnabled(true);
            } else {
                configFieldsPanel.removeAll();
                configFieldsPanel.revalidate();
                configFieldsPanel.repaint();
                configureButton.setEnabled(false);
                authenticateButton.setEnabled(false);
            }
        });
        
        configureButton.addActionListener(e -> configureProvider());
        authenticateButton.addActionListener(e -> startAuthentication());
    }
    
    private void showConfigurationFields(String provider) {
        configFieldsPanel.removeAll();
        
        if ("github".equals(provider)) {
            showGitHubConfigurationFields();
        }
        
        configFieldsPanel.revalidate();
        configFieldsPanel.repaint();
    }
    
    private void showGitHubConfigurationFields() {
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;
        
        // Client ID
        gbc.gridx = 0; gbc.gridy = 0;
        configFieldsPanel.add(new JLabel("GitHub Client ID:"), gbc);
        gbc.gridx = 1;
        configFieldsPanel.add(clientIdField, gbc);
        
        // Client Secret
        gbc.gridx = 0; gbc.gridy = 1;
        configFieldsPanel.add(new JLabel("GitHub Client Secret:"), gbc);
        gbc.gridx = 1;
        configFieldsPanel.add(clientSecretField, gbc);
        
        // Redirect URI
        gbc.gridx = 0; gbc.gridy = 2;
        configFieldsPanel.add(new JLabel("Redirect URI:"), gbc);
        gbc.gridx = 1;
        configFieldsPanel.add(redirectUriField, gbc);
        
        // Scope
        gbc.gridx = 0; gbc.gridy = 3;
        configFieldsPanel.add(new JLabel("OAuth Scopes:"), gbc);
        gbc.gridx = 1;
        configFieldsPanel.add(scopeField, gbc);
        
        // Help text
        gbc.gridx = 0; gbc.gridy = 4; gbc.gridwidth = 2;
        JTextArea helpText = new JTextArea(
            "To configure GitHub OAuth:\n" +
            "1. Go to GitHub Settings > Developer settings > OAuth Apps\n" +
            "2. Create a new OAuth App\n" +
            "3. Set Authorization callback URL to the Redirect URI above\n" +
            "4. Copy Client ID and Client Secret here"
        );
        helpText.setEditable(false);
        helpText.setBackground(getBackground());
        helpText.setFont(helpText.getFont().deriveFont(Font.ITALIC, 11f));
        configFieldsPanel.add(helpText, gbc);
    }
    
    private void configureProvider() {
        String provider = (String) providerComboBox.getSelectedItem();
        if (provider == null || provider.startsWith("Select")) {
            return;
        }
        
        updateStatus("Configuring " + provider + " provider...");
        
        CompletableFuture.supplyAsync(() -> {
            try {
                Map<String, String> config = new HashMap<>();
                
                if ("github".equals(provider)) {
                    config.put("client_id", clientIdField.getText().trim());
                    config.put("client_secret", new String(clientSecretField.getPassword()).trim());
                    config.put("redirect_uri", redirectUriField.getText().trim());
                    config.put("scope", scopeField.getText().trim());
                }
                
                return apiService.configureMCPProvider(provider, config);
                
            } catch (Exception e) {
                throw new RuntimeException("Configuration failed: " + e.getMessage(), e);
            }
        }).thenAccept(result -> {
            SwingUtilities.invokeLater(() -> {
                if (result != null && result.containsKey("status") && "success".equals(result.get("status"))) {
                    updateStatus("✅ Provider configured successfully!\nConfig ID: " + result.get("config_id"));
                    authenticateButton.setEnabled(true);
                } else {
                    updateStatus("❌ Configuration failed: " + result.get("error"));
                }
            });
        }).exceptionally(throwable -> {
            SwingUtilities.invokeLater(() -> {
                updateStatus("❌ Configuration failed: " + throwable.getMessage());
            });
            return null;
        });
    }
    
    private void startAuthentication() {
        String provider = (String) providerComboBox.getSelectedItem();
        if (provider == null || provider.startsWith("Select")) {
            return;
        }
        
        updateStatus("Starting " + provider + " authentication...");
        
        CompletableFuture.supplyAsync(() -> {
            try {
                return apiService.startMCPAuthentication(provider);
            } catch (Exception e) {
                throw new RuntimeException("Authentication failed: " + e.getMessage(), e);
            }
        }).thenAccept(result -> {
            SwingUtilities.invokeLater(() -> {
                if (result != null && result.containsKey("auth_url")) {
                    String authUrl = (String) result.get("auth_url");
                    updateStatus("✅ Authentication URL generated!\n\nPlease visit:\n" + authUrl + "\n\nAfter authorization, you'll be redirected back.");
                    
                    // Try to open the URL in the default browser
                    try {
                        Desktop.getDesktop().browse(java.net.URI.create(authUrl));
                    } catch (Exception e) {
                        updateStatus(statusArea.getText() + "\n\n⚠️ Could not open browser automatically. Please copy the URL above.");
                    }
                } else {
                    updateStatus("❌ Authentication failed: " + result.get("error"));
                }
            });
        }).exceptionally(throwable -> {
            SwingUtilities.invokeLater(() -> {
                updateStatus("❌ Authentication failed: " + throwable.getMessage());
            });
            return null;
        });
    }
    
    private void loadProviders() {
        // This could be enhanced to dynamically load providers from the API
        updateStatus("Ready to configure MCP providers.\nSelect a provider to begin.");
    }
    
    private void updateStatus(String message) {
        statusArea.setText(message);
        statusArea.setCaretPosition(0);
    }
}
