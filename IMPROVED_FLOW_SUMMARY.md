# Improved Agent Flow: File Search → Web Search Fallback

## 🎯 **New Flow Overview**

The orchestrator now implements an intelligent flow that prioritizes internal knowledge and provides web search as a fallback:

```
User Request → LLM Analysis → Routing Decision → Agent Execution
                                                    ↓
                                              File Search First
                                                    ↓
                                              Found? → Yes → Return Answer
                                                    ↓ No
                                              Web Search Fallback
                                                    ↓
                                              Return Both Results
```

## 🔄 **Flow Logic**

### **1. LLM Analysis**
The LLM analyzes the user's request and determines the routing strategy:
- **Explicit ticket requests** → Route directly to Ticket Agent
- **All other questions** → Start with File Search Agent

### **2. File Search First**
For most questions, the system starts by searching the internal knowledge repository:
- Searches company documentation, policies, procedures
- Looks for internal guides and technical information
- Provides company-specific answers when available

### **3. Web Search Fallback**
If File Search returns "Not found in repository":
- Automatically falls back to Web Search
- Provides current, external information
- Clearly indicates that web search was used

### **4. Ticket Creation**
Only routes to Ticket Agent when user explicitly requests ticket creation:
- "I need to create a ticket"
- "Create a ticket for my laptop"
- "Open a ticket for this issue"

## 📊 **Flow Examples**

### **Example 1: Internal Procedure Found**
```
User: "How do I reset my password?"
Flow: File Search → Found in repository → Return answer
Result: Internal password reset procedure
```

### **Example 2: Internal + External Information**
```
User: "What is the latest Python version?"
Flow: File Search → Not found → Web Search → Return both
Result: 
📁 File Search: "Not found in repository."
🌐 Web Search: "Latest Python version is 3.13.7..."
```

### **Example 3: Explicit Ticket Request**
```
User: "I need to create a ticket for my laptop not working"
Flow: Direct to Ticket Agent
Result: Ticket creation prompt
```

### **Example 4: General IT Question**
```
User: "My computer is slow"
Flow: File Search → Not found → Web Search → Return both
Result:
📁 File Search: "Not found in repository."
🌐 Web Search: "Here are some tips to speed up your computer..."
```

## 🎯 **Key Benefits**

### **1. Prioritizes Internal Knowledge**
- Company-specific information takes precedence
- Ensures users get internal procedures when available
- Maintains company knowledge base relevance

### **2. Seamless Fallback**
- No dead ends - always provides an answer
- Transparent about information sources
- Combines internal and external knowledge

### **3. Clear User Communication**
- Explicitly states when web search is used
- Shows both File Search and Web Search results
- Users know the source of information

### **4. Intelligent Routing**
- LLM determines the best approach
- Only creates tickets when explicitly requested
- Handles ambiguous requests intelligently

## 🔧 **Technical Implementation**

### **Routing Logic**
```python
async def llm_orchestrate_request(user_question: str, vector_store_ids: List[str] = None) -> str:
    agent_type = await llm_route_request(user_question)
    
    if agent_type == "TICKET":
        # Direct ticket creation
        return await run_ticket_creation(user_question)
    
    elif agent_type == "FILE_SEARCH":
        # File Search → Web Search fallback
        file_result = await run_file_search(user_question, vector_store_ids)
        
        if "Not found in repository" in file_result:
            web_result = await run_web_search(user_question)
            return f"📁 File Search: {file_result}\n\n🌐 Web Search: {web_result}"
        else:
            return f"📁 File Search: {file_result}"
```

### **LLM Instructions**
```python
ROUTING RULES:
- If user explicitly asks for ticket creation → TICKET_AGENT
- For all other questions → FILE_SEARCH_AGENT (will fallback to WEB_SEARCH_AGENT if not found)
```

## 📈 **User Experience Improvements**

### **Before (Pattern Matching)**
- Brittle keyword matching
- Inconsistent routing
- No fallback mechanism
- Poor handling of edge cases

### **After (LLM + Fallback)**
- Intelligent intent recognition
- Consistent File Search → Web Search flow
- Always provides an answer
- Clear information source attribution

## 🚀 **Usage Examples**

```bash
# Internal procedure (File Search only)
python llm_orchestrator.py "How do I access the VPN?"

# External information (File Search → Web Search)
python llm_orchestrator.py "What's the weather today?"

# IT question (File Search → Web Search)
python llm_orchestrator.py "My computer is slow"

# Explicit ticket request (Ticket Agent only)
python llm_orchestrator.py "I need to create a ticket for my laptop"
```

## 🎯 **Best Practices**

1. **Always start with File Search** for non-ticket requests
2. **Provide clear fallback messaging** when switching to Web Search
3. **Maintain context** about information sources
4. **Only route to Ticket Agent** for explicit ticket requests
5. **Combine results** when both sources provide value

This improved flow ensures users get the most relevant information while maintaining transparency about information sources!
