#!/usr/bin/env python3
"""
Streamlit UI for Agent Orchestrator
Provides a beautiful chat interface to interact with the specialized agents.
"""

import streamlit as st
import asyncio
import sys
import os
from typing import List

# Add the current directory to path to import our agents
sys.path.insert(0, '.')

# Import the orchestrator
from llm_orchestrator import llm_orchestrate_request

# Page configuration
st.set_page_config(
    page_title="IT Help Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/',
        'Report a bug': None,
        'About': '# IT Help Assistant\nA modern AI-powered support system'
    }
)

# Custom CSS for better styling with improved contrast
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-info {
        background-color: #ecf0f1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #bdc3c7;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #2c3e50;
    }
    .user-message {
        background-color: #3498db;
        border-left: 4px solid #2980b9;
        color: white;
    }
    .assistant-message {
        background-color: #ecf0f1;
        border-left: 4px solid #95a5a6;
        color: #2c3e50;
    }
    .file-search-result {
        background-color: #d5f4e6;
        border-left: 4px solid #27ae60;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #2c3e50;
    }
    .web-search-result {
        background-color: #fef9e7;
        border-left: 4px solid #f39c12;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #2c3e50;
    }
    .ticket-result {
        background-color: #fadbd8;
        border-left: 4px solid #e74c3c;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        color: #2c3e50;
    }
    /* Improve overall text readability */
    .stMarkdown {
        color: #2c3e50;
    }
    /* Make sidebar more visible */
    .css-1d391kg {
        background-color: #34495e;
    }
    /* Improve chat input visibility */
    .stTextInput > div > div > input {
        background-color: #ecf0f1;
        color: #2c3e50;
        border: 2px solid #bdc3c7;
    }
    /* Improve overall page background */
    .main .block-container {
        background-color: #ffffff;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Better button styling */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 0.25rem;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
    /* Improve sidebar text visibility */
    .css-1d391kg .css-1v0mbdj {
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "vector_store_ids" not in st.session_state:
        st.session_state.vector_store_ids = ["vs_68a48bcd776c81918c6ef3db005e1c06"]
    
    # Add conversation context tracking
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = {
            "current_agent": None,
            "waiting_for_ticket_details": False,
            "ticket_details": {},
            "conversation_history": []
        }
    
    # Add debug mode
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    
    # Add LLM parsing mode
    if "use_llm_parsing" not in st.session_state:
        st.session_state.use_llm_parsing = True

def display_header():
    """Display the main header and description."""
    st.markdown('<h1 class="main-header">🤖 IT Help Assistant</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="agent-info">
        <h3 style="color: #2c3e50; margin-bottom: 1rem;">🎯 How it works:</h3>
        <ul style="color: #2c3e50;">
            <li><strong>📁 File Search First:</strong> Searches internal knowledge repository</li>
            <li><strong>🌐 Web Search Fallback:</strong> If not found internally, searches the web</li>
            <li><strong>🎫 Ticket Creation:</strong> Creates ServiceNow tickets when explicitly requested</li>
        </ul>
        <p style="color: #2c3e50; font-style: italic; margin-top: 1rem;"><em>Ask me anything about IT support, company procedures, or general questions!</em></p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Display sidebar with configuration options."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Conversation status
        if st.session_state.conversation_context["waiting_for_ticket_details"]:
            st.warning("🎫 **Ticket Creation Mode**")
            st.info("Please provide ticket details in the chat.")
        
        # Vector store configuration
        st.subheader("📁 Knowledge Repository")
        vector_store_id = st.text_input(
            "Vector Store ID",
            value=st.session_state.vector_store_ids[0],
            help="ID of the vector store for file search"
        )
        
        if st.button("Update Vector Store"):
            st.session_state.vector_store_ids = [vector_store_id]
            st.success("Vector store updated!")
        
        # Environment check
        st.subheader("🔧 Environment")
        if os.getenv("OPENAI_API_KEY"):
            st.success("✅ OpenAI API Key configured")
        else:
            st.error("❌ OpenAI API Key not found")
            st.info("Please set OPENAI_API_KEY environment variable")
        
        if all([os.getenv("SN_INSTANCE"), os.getenv("SN_USER"), os.getenv("SN_PASS")]):
            st.success("✅ ServiceNow credentials configured")
        else:
            st.warning("⚠️ ServiceNow credentials not configured")
            st.info("Ticket creation will not work without SN_INSTANCE, SN_USER, SN_PASS")
        
        # Debug mode toggle
        st.subheader("🔧 Debug Options")
        debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            st.rerun()
        
        # LLM parsing toggle
        llm_parsing = st.checkbox("Use LLM Parsing", value=st.session_state.use_llm_parsing, 
                                 help="Use AI to intelligently parse ticket details from natural language")
        if llm_parsing != st.session_state.use_llm_parsing:
            st.session_state.use_llm_parsing = llm_parsing
            st.rerun()
        
        # Clear chat button
        st.subheader("🗑️ Chat Management")
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.conversation_context = {
                "current_agent": None,
                "waiting_for_ticket_details": False,
                "ticket_details": {},
                "conversation_history": []
            }
            st.rerun()

def format_message_for_ui(message: str) -> str:
    """Format the orchestrator response for better UI display."""
    # Remove console-style prefixes
    message = message.replace("🤖 LLM Orchestrator: Analyzing request...", "")
    message = message.replace("🤖 LLM Orchestrator: Starting with FILE_SEARCH agent...", "")
    message = message.replace("🤖 LLM Orchestrator: File Search returned no results, falling back to WEB_SEARCH...", "")
    message = message.replace("🤖 LLM Orchestrator: Routing to TICKET agent...", "")
    
    # Clean up the message
    message = message.strip()
    
    return message

def display_chat_message(role: str, content: str):
    """Display a chat message with proper styling."""
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 You:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Parse the content to identify different result types
        if "📁 File Search Agent Response:" in content:
            parts = content.split("📁 File Search Agent Response:")
            if len(parts) > 1:
                file_part = parts[1].split("🌐 Web Search Agent Response:")[0].strip()
                web_part = parts[1].split("🌐 Web Search Agent Response:")[1].strip() if "🌐 Web Search Agent Response:" in parts[1] else None
                
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant:</strong><br>
                    <div class="file-search-result">
                        <strong>📁 Internal Knowledge:</strong><br>
                        {file_part}
                    </div>
                """, unsafe_allow_html=True)
                
                if web_part:
                    st.markdown(f"""
                    <div class="web-search-result">
                        <strong>🌐 Web Search:</strong><br>
                        {web_part}
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("</div>", unsafe_allow_html=True)
        elif "🎫 Ticket Agent Response:" in content:
            ticket_content = content.split("🎫 Ticket Agent Response:")[1].strip()
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>
                <div class="ticket-result">
                    <strong>🎫 Ticket Creation:</strong><br>
                    {ticket_content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)

def display_chat_history():
    """Display the chat history."""
    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])

async def handle_conversation_context(user_input: str) -> tuple[str, bool]:
    """Handle conversation context and determine if we should continue with current agent."""
    context = st.session_state.conversation_context
    
    # If we're waiting for ticket details, treat this as ticket details
    if context["waiting_for_ticket_details"]:
        # Use LLM to intelligently parse the user input for ticket details
        details = await parse_ticket_details_llm(user_input, context["ticket_details"])
        
        # Always update with new details
        context["ticket_details"].update(details)
        
        # Check if we have enough information to create a ticket
        required_fields = ["short_description", "description", "impact", "urgency"]
        missing_fields = [field for field in required_fields if field not in context["ticket_details"]]
        
        if not missing_fields:
            # We have all required details, create the ticket
            context["waiting_for_ticket_details"] = False
            context["current_agent"] = None
            
            # Show what we're creating
            ticket_info = context["ticket_details"]
            summary = f"🎫 Creating ticket with:\n" + \
                     f"**Short Description:** {ticket_info.get('short_description', 'N/A')}\n" + \
                     f"**Description:** {ticket_info.get('description', 'N/A')}\n" + \
                     f"**Impact:** {ticket_info.get('impact', 'N/A')}\n" + \
                     f"**Urgency:** {ticket_info.get('urgency', 'N/A')}\n\n"
            
            # Create the ticket
            result = create_ticket_with_details(context["ticket_details"])
            return summary + result, True
        else:
            # Still need more details, but be more helpful
            if len(missing_fields) == 1:
                field_name = missing_fields[0].replace('_', ' ').title()
                return f"🎫 Ticket Agent: Almost there! I just need the **{field_name}**.\n" + \
                       f"Current details: {context['ticket_details']}", True
            else:
                return f"🎫 Ticket Agent: I have some details, but still need:\n" + \
                       "\n".join([f"- {field.replace('_', ' ').title()}" for field in missing_fields]) + \
                       f"\n\nCurrent details: {context['ticket_details']}", True
    
    return user_input, False

async def parse_ticket_details_llm(user_input: str, existing_details: dict = None) -> dict:
    """Use LLM to intelligently parse ticket details from natural language input."""
    # Check if LLM parsing is enabled
    if not st.session_state.use_llm_parsing:
        return parse_ticket_details_simple(user_input)
    
    try:
        from ticket_details_agent import interpret_ticket_details
        return await interpret_ticket_details(user_input, existing_details)
    except Exception as e:
        if st.session_state.debug_mode:
            st.write(f"🔍 Debug: LLM parsing failed: {e}")
        # Fallback to simple parsing
        return parse_ticket_details_simple(user_input)

def parse_ticket_details_simple(user_input: str) -> dict:
    """Simple fallback parsing when LLM is not available."""
    details = {}
    input_lower = user_input.lower()
    
    # Debug output
    if st.session_state.debug_mode:
        st.write(f"🔍 Debug: Simple parsing input: '{user_input}'")
    
    # Extract short description (usually the first meaningful phrase)
    if not details.get("short_description"):
        # Look for laptop/computer related issues
        if any(word in input_lower for word in ["laptop", "computer", "pc", "monitor", "screen"]):
            # Extract the issue description
            words = user_input.split()
            for i, word in enumerate(words):
                if any(issue in word.lower() for issue in ["broken", "not working", "won't", "doesn't", "failed"]):
                    # Get a few words around the issue
                    start = max(0, i-2)
                    end = min(len(words), i+3)
                    details["short_description"] = " ".join(words[start:end])
                    break
            if not details.get("short_description"):
                details["short_description"] = user_input[:50] + "..." if len(user_input) > 50 else user_input
        else:
            # For non-laptop issues, use the first part of the input
            details["short_description"] = user_input[:50] + "..." if len(user_input) > 50 else user_input
    
    # Extract description (the full problem description)
    if not details.get("description"):
        details["description"] = user_input
    
    # Extract impact level
    if not details.get("impact"):
        if any(word in input_lower for word in ["high impact", "high", "critical", "urgent", "emergency"]):
            details["impact"] = "1"
        elif any(word in input_lower for word in ["medium impact", "medium", "moderate"]):
            details["impact"] = "2"
        elif any(word in input_lower for word in ["low impact", "low", "minor"]):
            details["impact"] = "3"
        else:
            # Default to medium if not specified
            details["impact"] = "2"
    
    # Extract urgency level
    if not details.get("urgency"):
        if any(word in input_lower for word in ["urgent", "urgently", "asap", "immediate", "high urgency"]):
            details["urgency"] = "1"
        elif any(word in input_lower for word in ["medium urgency", "moderate"]):
            details["urgency"] = "2"
        elif any(word in input_lower for word in ["low urgency", "when convenient"]):
            details["urgency"] = "3"
        else:
            # Default to medium if not specified
            details["urgency"] = "2"
    
    # Debug output
    if st.session_state.debug_mode:
        st.write(f"🔍 Debug: Simple parsed details: {details}")
    
    return details

def create_ticket_with_details(details: dict) -> str:
    """Create a ticket with the collected details."""
    try:
        # Import the ticket creation function
        from ticket_agent import create_servicenow_incident
        
        result = create_servicenow_incident(
            short_description=details.get("short_description", "IT Support Request"),
            description=details.get("description", "Support request from chat interface"),
            urgency=details.get("urgency", "3"),
            impact=details.get("impact", "3")
        )
        
        if "error" in result:
            return f"❌ Error creating ticket: {result['error']}"
        else:
            return f"✅ Ticket created successfully!\n" + \
                   f"**Ticket Number:** {result.get('number', 'N/A')}\n" + \
                   f"**URL:** {result.get('url', 'N/A')}"
    except Exception as e:
        return f"❌ Error creating ticket: {str(e)}"

async def get_orchestrator_response(user_input: str) -> str:
    """Get response from the orchestrator with conversation context handling."""
    try:
        # Check if we're in a conversation context
        processed_input, is_context_handled = await handle_conversation_context(user_input)
        
        if is_context_handled:
            return processed_input
        
        # Normal orchestrator flow
        response = await llm_orchestrate_request(processed_input, st.session_state.vector_store_ids, ui_mode=True)
        
        # Check if this is a ticket creation request
        if "🎫 Ticket Agent Response:" in response:
            st.session_state.conversation_context["waiting_for_ticket_details"] = True
            st.session_state.conversation_context["current_agent"] = "ticket"
            st.session_state.conversation_context["ticket_details"] = {}
        
        return format_message_for_ui(response)
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    """Main application function."""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display sidebar
    display_sidebar()
    
    # Display chat history
    display_chat_history()
    
    # Chat input with context-aware placeholder
    placeholder_text = "Ask me anything about IT support, procedures, or create a ticket..."
    if st.session_state.conversation_context["waiting_for_ticket_details"]:
        placeholder_text = "Provide ticket details (short description, description, impact, urgency)..."
    
    if prompt := st.chat_input(placeholder_text):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        display_chat_message("user", prompt)
        
        # Get assistant response
        with st.spinner("🤖 Analyzing your request..."):
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(get_orchestrator_response(prompt))
            finally:
                loop.close()
        
        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Display assistant message
        display_chat_message("assistant", response)
        
        # Rerun to update the display
        st.rerun()

if __name__ == "__main__":
    main()
