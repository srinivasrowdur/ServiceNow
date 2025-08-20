#!/usr/bin/env python3
"""
Web Search Agent
Specialized agent that only performs web searches using the agents SDK.
"""

import os
import sys
import json
import asyncio
from typing import Optional

# --- Optional .env loader (safe if python-dotenv isn't installed) ---
try:
    if os.path.exists(".env"):
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
except Exception:
    pass

# Import the Agents SDK
try:
    from agents import Agent, WebSearchTool, Runner  # type: ignore
except Exception as e:
    raise RuntimeError(
        "Could not import your 'agents' SDK. Ensure the 'agents' package "
        "is installed and provides Agent, WebSearchTool, Runner."
    ) from e

# -----------------------------
#            POLICY
# -----------------------------
WEB_SEARCH_INSTRUCTIONS = """
You are a specialized Web Search Agent for a UK audience.

POLICY:
1) Use WebSearchTool to find current information from the web
2) Always clearly state that you used web search before providing information
3) Provide concise, relevant answers based on web search results
4) Cite sources when possible
5) Write in UK English (spelling, tone). Be clear and polite.
6) If no relevant information is found, clearly state this

When using tools, pass strictly valid JSON that matches the tool schema.
"""

# -----------------------------
#        Agent + Runner
# -----------------------------

def build_web_search_agent():
    """Build the web search agent with only web search capabilities."""
    ws_tool = WebSearchTool()
    
    agent = Agent(
        name="WebSearchAgent",
        tools=[ws_tool],
    )
    return agent

async def run_web_search(question: str) -> str:
    """Run a web search for the given question."""
    agent = build_web_search_agent()
    full_prompt = f"{WEB_SEARCH_INSTRUCTIONS}\n\nQuestion: {question}"
    result = await Runner.run(agent, full_prompt)

    # Be flexible about result shape
    out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
    return out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)

async def run_web_search_streaming(question: str, stream_callback=None):
    """Run a web search with streaming support."""
    agent = build_web_search_agent()
    full_prompt = f"{WEB_SEARCH_INSTRUCTIONS}\n\nQuestion: {question}"
    
    if stream_callback:
        # Send initial status
        stream_callback("🔍 Searching the web...")
    
    try:
        result = await Runner.run(agent, full_prompt)
        
        if stream_callback:
            stream_callback("📝 Processing results...")
        
        # Be flexible about result shape
        out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
        final_result = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)
        
        if stream_callback:
            # Stream the final result in chunks
            chunk_size = 50
            for i in range(0, len(final_result), chunk_size):
                chunk = final_result[i:i + chunk_size]
                stream_callback(chunk)
                await asyncio.sleep(0.05)  # Small delay for streaming effect
        
        return final_result
        
    except Exception as e:
        error_msg = f"❌ Error during web search: {str(e)}"
        if stream_callback:
            stream_callback(error_msg)
        return error_msg

async def web_search_repl():
    """Interactive REPL for web search agent."""
    print("Web Search Agent (UK) — type 'exit' to quit.")
    agent = build_web_search_agent()
    
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

        full_prompt = f"{WEB_SEARCH_INSTRUCTIONS}\n\nQuestion: {question}"
        result = await Runner.run(agent, full_prompt)
        out = getattr(result, "final_output", None) or getattr(result, "output_text", None) or result
        try:
            print("\nWebSearchAgent:", out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2))
        except Exception:
            print("\nWebSearchAgent:", str(out))

# -----------------------------
#              CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Web Search Agent - specialized for web searches.")
    parser.add_argument("question", nargs="*", help="The question to search for on the web.")
    args = parser.parse_args()

    user_question = " ".join(args.question).strip()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Please export it or add to .env")
        sys.exit(1)

    if user_question:
        result = asyncio.run(run_web_search(user_question))
        print(result)
    else:
        asyncio.run(web_search_repl())
