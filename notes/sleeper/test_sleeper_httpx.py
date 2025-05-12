import asyncio
import httpx

# this was just to test httpx cancelation logic before merging it into /proxy

async def make_request():
    async with httpx.AsyncClient() as client:
        return await client.get("http://localhost:9000/upstream", timeout=None)  # disable timeout for demo

async def main():
    task = asyncio.create_task(make_request())

    # comment out these two to see request complete and print resopnse
    await asyncio.sleep(2)  # simulate early client disconnect
    task.cancel()

    try:
        # this never happens if task is cancelled 
        response = await task
        print(response.text)
    except asyncio.CancelledError:
        print("Request cancelled")

asyncio.run(main())



