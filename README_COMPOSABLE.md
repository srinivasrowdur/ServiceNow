# Composable Agent Architecture

This project now implements a **composable agent architecture** where each agent specializes in a single task, making the system more modular and maintainable.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                AGENT ORCHESTRATOR                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Request Analyzer                       │    │
│  │  (Routes requests to appropriate specialized agent) │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              SPECIALIZED AGENTS                    │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │  │WebSearchAgent│ │FileSearchAgent│ │TicketAgent │   │    │
│  │  │(Web Search) │ │(Repository) │ │(ServiceNow) │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Individual Agents

### 1. **Web Search Agent** (`web_search_agent.py`)
- **Purpose**: Searches the web for current information
- **Tool**: `WebSearchTool`
- **Use Case**: Current events, external information, technology trends
- **Usage**: `python web_search_agent.py "What is the latest Python version?"`

### 2. **File Search Agent** (`file_search_agent.py`)
- **Purpose**: Searches the knowledge repository
- **Tool**: `FileSearchTool`
- **Use Case**: Internal documentation, procedures, company policies
- **Usage**: `python file_search_agent.py "How to install Python?"`

### 3. **Ticket Agent** (`ticket_agent.py`)
- **Purpose**: Creates ServiceNow tickets
- **Tool**: `FunctionTool` (ServiceNow API)
- **Use Case**: IT support requests, incident creation
- **Usage**: `python ticket_agent.py "I need to create a ticket for my laptop not working"`

## 🎯 Agent Orchestrator (`agent_orchestrator.py`)

The orchestrator analyzes user requests and routes them to the appropriate specialized agent.

### Routing Logic:
- **Ticket Creation**: Keywords like "create ticket", "laptop not working", "need help"
- **File Search**: Technical questions, "how to", procedures, internal documentation
- **Web Search**: General knowledge, current events, external information

### Usage:
```bash
# Route to appropriate agent automatically
python agent_orchestrator.py "I need to create a ticket for my laptop not working"
python agent_orchestrator.py "What is the latest Python version?"
python agent_orchestrator.py "How to install Python?"

# Interactive mode
python agent_orchestrator.py
```

## 🔧 Key Benefits

### **Modularity**
- Each agent has a single responsibility
- Easy to modify, test, and maintain individual agents
- Can deploy agents independently

### **Scalability**
- Add new specialized agents without affecting existing ones
- Scale individual agents based on demand
- Independent resource allocation

### **Flexibility**
- Use agents individually or through orchestrator
- Easy to swap out implementations
- Clear separation of concerns

### **Maintainability**
- Smaller, focused codebases
- Easier debugging and testing
- Clear interfaces between components

## 🚀 Usage Examples

### Individual Agent Usage:
```bash
# Web search for current information
python web_search_agent.py "What is the latest Python version?"

# Search internal repository
python file_search_agent.py "How to reset password?"

# Create a support ticket
python ticket_agent.py "My laptop won't turn on"
```

### Orchestrated Usage:
```bash
# Let orchestrator decide which agent to use
python agent_orchestrator.py "I need help with my laptop"
python agent_orchestrator.py "What's the weather like?"
python agent_orchestrator.py "How do I access the VPN?"
```

## 🔧 Configuration

### Environment Variables:
```bash
OPENAI_API_KEY=your_openai_api_key
SN_INSTANCE=your_servicenow_instance
SN_USER=your_servicenow_user
SN_PASS=your_servicenow_password
```

### Vector Store IDs:
- Default: `vs_689ca12932cc8191a0223ebc3a1d6116`
- Can be overridden with `--vector-store-id` parameter

## 📊 Comparison: Monolithic vs Composable

| Aspect | Monolithic (`newapp.py`) | Composable (Individual Agents) |
|--------|-------------------------|--------------------------------|
| **Architecture** | Single agent with multiple tools | Multiple specialized agents |
| **Responsibility** | One agent does everything | Each agent has single purpose |
| **Maintenance** | Harder to modify individual features | Easy to modify specific functionality |
| **Testing** | Complex integration testing | Simple unit testing per agent |
| **Deployment** | All-or-nothing deployment | Independent deployment |
| **Scaling** | Scale entire system | Scale individual agents |
| **Flexibility** | Fixed tool combination | Dynamic agent selection |

## 🔮 Future Enhancements

1. **New Specialized Agents**:
   - Email Agent (for email composition)
   - Calendar Agent (for scheduling)
   - Analytics Agent (for data analysis)

2. **Advanced Orchestration**:
   - Multi-agent conversations
   - Agent chaining (one agent's output feeds another)
   - Load balancing between agents

3. **Monitoring & Observability**:
   - Agent performance metrics
   - Request routing analytics
   - Error tracking per agent

This composable architecture provides a solid foundation for building scalable, maintainable AI agent systems!
