import httpx
import asyncio
import json

async def test_pulse():
    print("Connecting to Agent Pulse SSE...")
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", "http://localhost:8000/api/v1/pulse/stream") as response:
            print(f"Status: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(f"Received Pulse: {data['event']} -> {data['payload']}")
                elif line.startswith(": ping"):
                    print("Heartbeat received.")

if __name__ == "__main__":
    try:
        asyncio.run(test_pulse())
    except KeyboardInterrupt:
        print("Test stopped.")
