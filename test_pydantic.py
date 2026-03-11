import asyncio
from pydantic_ai import Agent

agent = Agent("gemini-1.5-pro", system_prompt="Hello")

async def main():
    res = await agent.run("test")
    print(dir(res))

asyncio.run(main())
