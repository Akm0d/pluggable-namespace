import asyncio

import cpop


def main():
    # Initialize the event loop
    loop = asyncio.new_event_loop()
    # Set the event loop
    asyncio.set_event_loop(loop)

    # Start the async code
    asyncio.run(amain())


async def amain():
    # Create the hub within an async context
    async with cpop.Hub(cli="rend") as hub:
        # Start the hub cli
        await hub.rend.init.cli()


if __name__ == "__main__":
    main()
