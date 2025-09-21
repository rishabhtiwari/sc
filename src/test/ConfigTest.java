package test;

import config.IChatConfig;
import api.IChatApiService;

/**
 * Simple test class to verify configuration and API connectivity
 */
public class ConfigTest {
    
    public static void main(String[] args) {
        System.out.println("🧪 iChat Configuration Test");
        System.out.println("==================================================");
        
        // Test configuration
        System.out.println("\n📋 Configuration Test:");
        IChatConfig.printConfig();
        
        // Test API server health
        System.out.println("\n❤️ API Server Health Test:");
        boolean isHealthy = IChatConfig.isApiServerHealthy();
        
        if (isHealthy) {
            System.out.println("✅ API server is healthy and ready!");
            
            // Test API service
            System.out.println("\n📡 API Service Test:");
            IChatApiService apiService = new IChatApiService();
            
            try {
                // Test connection
                apiService.testConnection().thenAccept(success -> {
                    if (success) {
                        System.out.println("✅ API service connection test passed!");
                        
                        // Test sending a message
                        apiService.sendMessage("Hello from Java config test!")
                            .thenAccept(response -> {
                                System.out.println("📨 Test message response: " + response);
                                System.out.println("🎉 All tests passed!");
                                apiService.shutdown();
                                System.exit(0);
                            })
                            .exceptionally(throwable -> {
                                System.err.println("❌ Message test failed: " + throwable.getMessage());
                                apiService.shutdown();
                                System.exit(1);
                                return null;
                            });
                    } else {
                        System.err.println("❌ API service connection test failed!");
                        apiService.shutdown();
                        System.exit(1);
                    }
                }).exceptionally(throwable -> {
                    System.err.println("❌ Connection test error: " + throwable.getMessage());
                    apiService.shutdown();
                    System.exit(1);
                    return null;
                });
                
                // Wait for async operations
                Thread.sleep(5000);
                
            } catch (Exception e) {
                System.err.println("❌ Test error: " + e.getMessage());
                apiService.shutdown();
                System.exit(1);
            }
            
        } else {
            System.err.println("❌ API server is not healthy. Please check:");
            System.err.println("   1. Docker container is running: docker ps");
            System.err.println("   2. API server is accessible: curl " + IChatConfig.getHealthCheckUrl());
            System.err.println("   3. Port 8080 is not blocked by firewall");
            System.exit(1);
        }
    }
}
