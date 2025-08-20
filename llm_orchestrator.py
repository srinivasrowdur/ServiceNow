#!/usr/bin/env python3
"""
LLM-Powered Agent Orchestrator
Uses LLM intelligence to determine which specialized agent to route to.
"""

import os
import sys
import json
import asyncio
from typing import Optional, List

# --- Optional .env loader (safe if python-dotenv isn't installed) ---
try:
    if os.path.exists(".env"):
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
except Exception:
    pass

# Import the Agents SDK
try:
    from agents import Agent, Runner  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Could not import your 'agents' SDK. Ensure the 'agents' package "
        "is installed and provides Agent, Runner."
    ) from e

# Import the individual agents
from web_search_agent import run_web_search, run_web_search_streaming
from file_search_agent import run_file_search, run_file_search_streaming
from ticket_agent import run_ticket_creation, run_ticket_creation_streaming

# -----------------------------
#            POLICY
# -----------------------------
LLM_ORCHESTRATOR_INSTRUCTIONS = """
You are an intelligent Agent Orchestrator for a UK audience.

You have access to three specialized agents:

1. **TICKET_AGENT**: Creates ServiceNow tickets for IT support requests
   - Use ONLY when user explicitly asks to create a ticket
   - Keywords: "create a ticket", "create ticket", "make a ticket", "open a ticket"
   - Do NOT route to ticket agent for general IT questions

2. **FILE_SEARCH_AGENT**: Searches internal knowledge repository
   - Use for: "How to reset password", "company policy", "internal procedures"
   - Handles: Internal documentation, company policies, technical procedures

3. **WEB_SEARCH_AGENT**: Searches the web for current information
   - Use for: "What's the weather", "latest Python version", "current events"
   - Handles: External information, current events, general knowledge

ROUTING RULES:
- If user explicitly asks for ticket creation → TICKET_AGENT
- For all other questions → FILE_SEARCH_AGENT (will fallback to WEB_SEARCH_AGENT if not found)

RESPOND with ONLY one of these exact strings:
- "TICKET_AGENT" - ONLY for explicit ticket creation requests
- "FILE_SEARCH_AGENT" - for all other questions (default)

Do not provide any explanation or additional text - just the agent name.
"""

# -----------------------------
#        LLM Orchestrator
# -----------------------------

def build_llm_orchestrator():
    """Build the LLM orchestrator agent."""
    agent = Agent(
        name="LLMOrchestrator",
        tools=[],  # No tools needed - just LLM reasoning
    )
    return agent

async def llm_route_request(user_question: str) -> str:
    """Use LLM to intelligently route the request to appropriate agent."""
    agent = build_llm_orchestrator()
    full_prompt = f"{LLM_ORCHESTRATOR_INSTRUCTIONS}\n\nUser Request: {user_question}\n\nWhich agent should handle this request?"
    
    result = await Runner.run(agent, full_prompt)
    
    # Extract the agent decision
    out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
    response = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)
    
    # Clean up the response to get just the agent name
    response = response.strip().upper()
    
    # Map to our agent types
    if "TICKET" in response:
        return "TICKET"
    elif "FILE_SEARCH" in response or "FILE" in response:
        return "FILE_SEARCH"
    elif "WEB_SEARCH" in response or "WEB" in response:
        return "FILE_SEARCH"  # Route to file search first, will fallback to web search
    else:
        # Default to file search for all other questions (will fallback to web search if needed)
        return "FILE_SEARCH"

async def llm_orchestrate_request(user_question: str, vector_store_ids: List[str] = None, ui_mode: bool = False) -> str:
    """Orchestrate the request using LLM intelligence with File Search → Web Search fallback."""
    if vector_store_ids is None:
        vector_store_ids = ["vs_689ca12932cc8191a0223ebc3a1d6116"]
    
    if not ui_mode:
        print(f"🤖 LLM Orchestrator: Analyzing request...")
    
    # Use LLM to determine which agent to use
    agent_type = await llm_route_request(user_question)
    
    try:
        if agent_type == "TICKET":
            if not ui_mode:
                print(f"🤖 LLM Orchestrator: Routing to TICKET agent...")
            result = await run_ticket_creation(user_question)
            return f"🎫 Ticket Agent Response:\n{result}"
        
        elif agent_type == "FILE_SEARCH":
            if not ui_mode:
                print(f"🤖 LLM Orchestrator: Starting with FILE_SEARCH agent...")
            
            # Try File Search first
            file_result = await run_file_search(user_question, vector_store_ids)
            
            # Check if File Search found something useful
            if "Not found in repository" in file_result or "not found" in file_result.lower():
                if not ui_mode:
                    print(f"🤖 LLM Orchestrator: File Search returned no results, falling back to WEB_SEARCH...")
                
                # Fallback to Web Search
                web_result = await run_web_search(user_question)
                return f"📁 File Search Agent Response:\n{file_result}\n\n🌐 Web Search Agent Response:\n{web_result}"
            else:
                # File Search found something useful
                return f"📁 File Search Agent Response:\n{file_result}"
        
        else:
            return "❌ Error: Unknown agent type"
    
    except Exception as e:
        return f"❌ Error routing to {agent_type} agent: {str(e)}"

async def llm_orchestrate_request_streaming(user_question: str, vector_store_ids: List[str] = None, ui_mode: bool = False, stream_callback=None) -> str:
    """Orchestrate the request with streaming support."""
    if vector_store_ids is None:
        vector_store_ids = ["vs_689ca12932cc8191a0223ebc3a1d6116"]
    
    if stream_callback:
        stream_callback("🤖 Analyzing your request...")
    
    # Use LLM to determine which agent to use
    agent_type = await llm_route_request(user_question)
    
    try:
        if agent_type == "TICKET":
            if stream_callback:
                stream_callback("🎫 Routing to Ticket Agent...")
            result = await run_ticket_creation_streaming(user_question, stream_callback)
            return f"🎫 Ticket Agent Response:\n{result}"
        
        elif agent_type == "FILE_SEARCH":
            if stream_callback:
                stream_callback("📁 Starting with File Search Agent...")
            
            # Try File Search first
            file_result = await run_file_search_streaming(user_question, vector_store_ids, stream_callback)
            
            # Check if File Search found something useful
            if "Not found in repository" in file_result or "not found" in file_result.lower():
                if stream_callback:
                    stream_callback("🌐 File Search returned no results, falling back to Web Search...")
                
                # Fallback to Web Search
                web_result = await run_web_search_streaming(user_question, stream_callback)
                return f"📁 File Search Agent Response:\n{file_result}\n\n🌐 Web Search Agent Response:\n{web_result}"
            else:
                # File Search found something useful
                return f"📁 File Search Agent Response:\n{file_result}"
        
        else:
            error_msg = "❌ Error: Unknown agent type"
            if stream_callback:
                stream_callback(error_msg)
            return error_msg
    
    except Exception as e:
        error_msg = f"❌ Error routing to {agent_type} agent: {str(e)}"
        if stream_callback:
            stream_callback(error_msg)
        return error_msg

async def llm_orchestrator_repl(vector_store_ids: List[str] = None):
    """Interactive REPL for the LLM orchestrator."""
    if vector_store_ids is None:
        vector_store_ids = ["vs_689ca12932cc8191a0223ebc3a1d6116"]
    
    print("🤖 LLM-Powered Agent Orchestrator (UK) — type 'exit' to quit.")
    print("Available agents: WebSearch, FileSearch, TicketCreation")
    print("The LLM will intelligently route your requests to the best agent.")
    
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Bye!")
            return

        result = await llm_orchestrate_request(question, vector_store_ids)
        print(f"\n{result}")

# -----------------------------
#              CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM-Powered Agent Orchestrator - uses AI to route requests intelligently.")
    parser.add_argument("question", nargs="*", help="The question to route to appropriate agent.")
    parser.add_argument(
        "--vector-store-id",
        action="append",
        default=["vs_689ca12932cc8191a0223ebc3a1d6116"],
        help="Vector store ID(s) for FileSearch (can repeat).",
    )
    args = parser.parse_args()

    user_question = " ".join(args.question).strip()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Please export it or add to .env")
        sys.exit(1)

    if user_question:
        result = asyncio.run(llm_orchestrate_request(user_question, args.vector_store_id))
        print(result)
    else:
        asyncio.run(llm_orchestrator_repl(args.vector_store_id))
