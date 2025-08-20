# Streamlit UI for IT Help Assistant

A beautiful web interface for the IT Help Assistant using Streamlit's latest chat interface.

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
pip install -r requirements_streamlit.txt
```

### **2. Set Environment Variables**
```bash
export OPENAI_API_KEY="your_openai_api_key"
export SN_INSTANCE="your_servicenow_instance"
export SN_USER="your_servicenow_user"
export SN_PASS="your_servicenow_password"
```

### **3. Run the UI**
```bash
streamlit run streamlit_ui.py
```

The UI will open at `http://localhost:8501`

## 🎨 **Features**

### **Modern Chat Interface**
- Latest Streamlit chat UI components
- Real-time conversation flow
- Message history persistence
- Beautiful styling with custom CSS

### **Intelligent Agent Routing**
- **📁 File Search First**: Searches internal knowledge repository
- **🌐 Web Search Fallback**: Automatically searches web if not found internally
- **🎫 Ticket Creation**: Creates ServiceNow tickets when explicitly requested

### **Configuration Panel**
- Vector store ID configuration
- Environment variable status check
- Chat history management
- Real-time configuration updates

### **Visual Message Types**
- **👤 User Messages**: Blue-themed with clear user identification
- **📁 File Search Results**: Green-themed for internal knowledge
- **🌐 Web Search Results**: Orange-themed for external information
- **🎫 Ticket Creation**: Pink-themed for ServiceNow tickets

## 🎯 **Usage Examples**

### **Internal Procedure Query**
```
User: "How do I reset my password?"
Result: File Search → Internal password reset procedure
```

### **External Information Query**
```
User: "What's the latest Python version?"
Result: File Search → Not found → Web Search → Latest version info
```

### **Ticket Creation**
```
User: "I need to create a ticket for my laptop not working"
Result: Direct to Ticket Agent → Ticket creation prompt
```

## 🔧 **Configuration Options**

### **Sidebar Configuration**
- **Vector Store ID**: Configure the knowledge repository
- **Environment Check**: Verify API keys and credentials
- **Chat Management**: Clear conversation history

### **Environment Variables**
- `OPENAI_API_KEY`: Required for all AI operations
- `SN_INSTANCE`: ServiceNow instance (for ticket creation)
- `SN_USER`: ServiceNow username (for ticket creation)
- `SN_PASS`: ServiceNow password (for ticket creation)

## 🎨 **UI Components**

### **Header Section**
- Main title with robot emoji
- How-it-works explanation
- Clear user guidance

### **Chat Interface**
- Modern chat input at bottom
- Message history with proper styling
- Real-time response generation
- Loading spinners during processing

### **Sidebar**
- Configuration options
- Environment status
- Chat management tools

## 🔄 **Message Flow**

1. **User Input** → Chat input field
2. **LLM Analysis** → Determines best agent
3. **Agent Execution** → File Search → Web Search (if needed)
4. **Response Formatting** → Clean UI-friendly messages
5. **Display** → Styled chat messages with proper theming

## 🎨 **Styling Features**

### **Custom CSS**
- Professional color scheme
- Message type differentiation
- Responsive design
- Clean typography

### **Message Types**
- **User Messages**: Blue theme with left border
- **Assistant Messages**: Purple theme with left border
- **File Search**: Green background for internal knowledge
- **Web Search**: Orange background for external information
- **Ticket Creation**: Pink background for ServiceNow operations

## 🚀 **Deployment**

### **Local Development**
```bash
streamlit run streamlit_ui.py --server.port 8501
```

### **Production Deployment**
```bash
# Set production environment variables
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run with production settings
streamlit run streamlit_ui.py
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   - Ensure all agent files are in the same directory
   - Check Python path includes current directory

2. **Environment Variables**
   - Verify all required variables are set
   - Check sidebar for environment status

3. **Async Issues**
   - Ensure proper asyncio event loop handling
   - Check for background task completion

### **Debug Mode**
```bash
streamlit run streamlit_ui.py --logger.level debug
```

## 📱 **Responsive Design**

The UI is designed to work on:
- Desktop browsers
- Tablet devices
- Mobile phones
- Different screen sizes

## 🔮 **Future Enhancements**

1. **File Upload**: Upload documents to knowledge base
2. **Voice Input**: Speech-to-text capabilities
3. **Export Chat**: Download conversation history
4. **Multi-language**: Internationalization support
5. **Dark Mode**: Theme switching option

## 🎯 **Best Practices**

1. **Clear Prompts**: Ask specific questions for better results
2. **Use Keywords**: Include relevant terms for better routing
3. **Check Status**: Monitor environment status in sidebar
4. **Clear History**: Reset chat when switching topics

The Streamlit UI provides a modern, user-friendly interface to interact with the intelligent agent orchestrator!
