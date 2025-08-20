#!/usr/bin/env python3
"""
Test script for Streamlit UI components
"""

import asyncio
import sys
import os

# Add the current directory to path
sys.path.insert(0, '.')

# Test imports
try:
    from llm_orchestrator import llm_orchestrate_request
    print("✅ Successfully imported llm_orchestrator")
except Exception as e:
    print(f"❌ Failed to import llm_orchestrator: {e}")

try:
    import streamlit as st
    print(f"✅ Successfully imported streamlit (version: {st.__version__})")
except Exception as e:
    print(f"❌ Failed to import streamlit: {e}")

# Test environment variables
print("\n🔧 Environment Check:")
if os.getenv("OPENAI_API_KEY"):
    print("✅ OPENAI_API_KEY is set")
else:
    print("❌ OPENAI_API_KEY is not set")

if all([os.getenv("SN_INSTANCE"), os.getenv("SN_USER"), os.getenv("SN_PASS")]):
    print("✅ ServiceNow credentials are set")
else:
    print("⚠️ ServiceNow credentials are not fully set")

# Test async function
async def test_orchestrator():
    """Test the orchestrator function."""
    try:
        print("\n🧪 Testing orchestrator...")
        result = await llm_orchestrate_request("test message", ui_mode=True)
        print(f"✅ Orchestrator test successful: {result[:100]}...")
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")

if __name__ == "__main__":
    print("🚀 Streamlit UI Test Suite")
    print("=" * 50)
    
    # Run async test
    asyncio.run(test_orchestrator())
    
    print("\n✅ All tests completed!")
    print("\nTo run the Streamlit UI:")
    print("streamlit run streamlit_ui.py")
