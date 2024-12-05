async def test_run(hub):
    # Start the interactive console in a subprocess
    child = hub.lib.pexpect.spawn(
        f"{hub.lib.sys.executable} -m hub -i", encoding="utf-8", timeout=5
    )

    # Expect the banner
    child.expect("This console is running in an asyncio event loop with a hub.")

    # Send a command and expect the result
    child.sendline("await hub.lib.asyncio.sleep(0)")
    child.expect(">>>")  # Expect the prompt again

    # Send an exit command
    child.sendline("exit()")
    child.expect(hub.lib.pexpect.EOF)  # Expect the end of the output

    # Close the subprocess
    child.close()

    # Check that the subprocess exited successfully
    assert child.exitstatus == 0, "Subprocess exited with an error"
