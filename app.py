from agents import Agent, FileSearchTool, Runner, WebSearchTool
import os

try:
    # Lazy import so script still works if python-dotenv not installed
    if os.path.exists('.env'):
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
except Exception:
    pass
agent = Agent(
    name="Assistant",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_689ca12932cc8191a0223ebc3a1d6116"]
        ),
    ],
)

STRICT_INSTRUCTIONS = (
    "You must first try to answer ONLY using the contents returned by the file search tool. "
    "If the answer is not explicitly contained in those search results, reply exactly with: Not found in repository. "
    " Follow that up with using the WebSearchTool only when File search has failed and mention that in the response."
)


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ask a question answered only from repository file search results.")
    parser.add_argument("question", nargs="*", help="The question to ask.")
    args = parser.parse_args()
    user_question = " ".join(args.question).strip() or "What is TetraPack?"
    full_prompt = f"{STRICT_INSTRUCTIONS}\n\nQuestion: {user_question}"  # embed constraints directly
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Please export it before running: export OPENAI_API_KEY=your_key")
        return
    result = await Runner.run(agent, full_prompt)
    print(result.final_output)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())