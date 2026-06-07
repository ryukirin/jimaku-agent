# Create server parameters for stdio connection
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

load_dotenv()

server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(Path(__file__).with_name("search_mcp.py"))],
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

            hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
            if not hf_token:
                raise RuntimeError(
                    "请先设置 HF_TOKEN 或 HUGGINGFACEHUB_API_TOKEN 环境变量。"
                )

            llm = HuggingFaceEndpoint(
                repo_id="Qwen/Qwen2.5-7B-Instruct",
                task="text-generation",
                temperature=0.1,
                max_new_tokens=512,
                huggingfacehub_api_token=hf_token,
            )
            model = ChatHuggingFace(llm=llm)

            # Create and run the agent
            agent = create_agent(model, tools)
            agent_response = await agent.ainvoke(
                {"messages": [{"role": "user", "content": "搜索莲之空"}]}
            )
            print(agent_response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
