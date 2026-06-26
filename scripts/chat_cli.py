import asyncio
import sys
import os
import argparse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.api.dependencies import (
    metadata_store, document_store, vector_store, llm_provider, prompt_registry, runner
)
from agents.simplechat.agent import SimpleChatAgent

async def run_chat(message: str):
    agent = SimpleChatAgent(
        metadata_store=metadata_store,
        document_store=document_store,
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_registry=prompt_registry
    )

    print(f"User: {message}")
    print("Agent is thinking...")

    execution_id = await runner.run(agent, {"message": message})

    # Wait a bit for the execution to finish and metadata to be updated
    # In a real runner, it might be more synchronous or we'd wait for the event.
    execution = await metadata_store.get_execution(execution_id)

    if execution["status"] == "completed":
        print(f"Agent: {execution['output_data']['response']}")
    else:
        print(f"Execution failed or is in status: {execution['status']}")
        if execution.get("error_message"):
            print(f"Error: {execution['error_message']}")

def main():
    parser = argparse.ArgumentParser(description="Simple Chat CLI")
    parser.add_argument("message", type=str, help="The message to send to the agent")
    args = parser.parse_args()

    asyncio.run(run_chat(args.message))

if __name__ == "__main__":
    main()
