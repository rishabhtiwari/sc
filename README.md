# iChat Assistant - System Tray Integration with API

A JavaFX-based chat assistant that runs in your system tray/dock and connects to your iChat server API.

## 🏗️ Project Structure

```
src/
├── Main.java                          # Application entry point
├── app/
│   └── IChatApplication.java         # Main JavaFX application class
├── ui/
│   ├── components/
│   │   ├── AskButton.java            # Floating button component (legacy)
│   │   └── ChatSidebar.java          # Chat interface component
│   └── styles/
│       ├── ButtonStyles.java         # Centralized button styling
│       └── SidebarStyles.java        # Centralized sidebar styling
├── system/
│   └── SystemTrayManager.java        # System tray/dock integration
├── api/
│   └── IChatApiService.java          # API service for server communication
├── config/
│   └── IChatConfig.java              # Configuration management
└── run-ichat.sh                      # Launch script
```

## 🎯 Refactoring Improvements

### **1. Package Organization**
- **`app/`** - Application-level classes and coordination
- **`ui/components/`** - Reusable UI components
- **`ui/styles/`** - Centralized styling definitions

### **2. Separation of Concerns**
- **Styling extracted** from components into dedicated style classes
- **Business logic separated** from presentation logic
- **Clear component responsibilities** with focused functionality

### **3. Code Quality Improvements**
- **Comprehensive documentation** with JavaDoc comments
- **Method extraction** for better readability and maintainability
- **Consistent naming conventions** throughout the codebase
- **Logical method organization** within each class

## 📋 Component Overview

### **Main.java**
- Clean entry point with proper imports
- Launches the JavaFX application

### **IChatApplication.java**
- Main application coordinator
- Manages application lifecycle
- Handles component initialization and cleanup

### **AskButton.java**
- Floating circular button with drag functionality
- Uses centralized styling from `ButtonStyles`
- Organized into logical private methods:
  - `createButton()` - Button creation and styling
  - `setupDragFunctionality()` - Drag event handling
  - `createButtonScene()` - Scene setup with circular clipping
  - `configureStage()` - Stage configuration

### **ChatSidebar.java**
- Modern chat interface with three main sections
- Uses centralized styling from `SidebarStyles`
- Organized into logical private methods:
  - `createHeaderSection()` - Title and subtitle
  - `createChatArea()` - Scrollable chat display
  - `createInputSection()` - Message input and controls
  - `createActionButtons()` - Clear and close buttons

### **ButtonStyles.java**
- Centralized button styling constants
- Easy to maintain and modify
- Consistent styling across components

### **SidebarStyles.java**
- Complete CSS stylesheet for sidebar
- Modern gradient designs and shadows
- Responsive layout styling

## ✅ Maintained Functionality

All original functionality has been preserved:

- **Floating Ask Button** - Circular button with drag functionality
- **Always-on-top behavior** - Button and sidebar stay above other windows
- **Chat Interface** - Full-featured chat sidebar with modern styling
- **Smooth Transitions** - Button hides when sidebar opens, shows when closed
- **Interactive Elements** - Send messages, clear chat, close sidebar
- **Demo Responses** - Random engaging responses for demonstration

## 🚀 Benefits of Refactoring

### **Maintainability**
- **Easy styling updates** - Change colors/fonts in one place
- **Component reusability** - Components can be used independently
- **Clear code structure** - Easy to understand and modify

### **Scalability**
- **Add new components** easily in `ui/components/`
- **Extend styling** by adding new style classes
- **Plugin architecture ready** - Clean separation allows for extensions

### **Developer Experience**
- **Better IDE support** - Proper package structure and imports
- **Easier debugging** - Clear method boundaries and responsibilities
- **Team collaboration** - Well-documented and organized code

## 🔧 Usage

The refactored application works exactly the same as before:

1. **Run the application** - Floating button appears
2. **Drag the button** - Move it anywhere on screen
3. **Click the button** - Opens the chat sidebar
4. **Use the chat** - Send messages and interact
5. **Close sidebar** - Button reappears automatically

## 🌐 **API Integration**

The application now connects to your iChat server to send and receive real chat messages.

### **API Configuration**

**Default API URL:** `http://localhost:8080/api/chat`

**Configure API URL (choose one method):**

1. **System Property:**
   ```bash
   java -Dichat.api.url=https://your-server.com/api/chat -cp "." Main
   ```

2. **Environment Variable:**
   ```bash
   export ICHAT_API_URL=https://your-server.com/api/chat
   java -cp "." Main
   ```

3. **IntelliJ Run Configuration:**
   - Go to Run → Edit Configurations
   - Add VM Option: `-Dichat.api.url=https://your-server.com/api/chat`

### **API Request Format**

The client sends POST requests with JSON payload:
```json
{
  "message": "User's message text",
  "timestamp": 1640995200000,
  "client": "desktop"
}
```

### **Expected API Response**

Your server should respond with JSON:
```json
{
  "message": "Assistant's response text",
  "timestamp": 1640995201000,
  "status": "success"
}
```

### **API Features**

- **Asynchronous calls** - Non-blocking UI experience
- **Typing indicators** - Shows "💭 Thinking..." while waiting for response
- **Error handling** - Graceful fallback for connection issues
- **Configurable timeouts** - 10s connection, 30s read timeout
- **Debug logging** - Detailed console output for troubleshooting

## 📝 Next Steps

The refactored codebase is now ready for:
- **Server integration** - Connect to your iChat API endpoint
- **Feature additions** - New components and functionality
- **Styling customization** - Easy theme changes
- **Testing implementation** - Clean structure for unit tests
