import asyncio
from pydantic_ai import Agent

async def main():
    agent = Agent('gemini-2.5-flash', output_type=str)
    res = await agent.run("Ship tôi 2 lọ", system_prompt="Luôn trả lời có chữ DẠ.")
    print("OUTPUT:", repr(res.data))

asyncio.run(main())
