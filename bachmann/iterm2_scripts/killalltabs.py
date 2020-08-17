#!/usr/bin/env python3.7

import iterm2


async def kill_tab_command(tab, cmd_tab):
    pid = await tab.current_session.async_get_variable("pid")
    await cmd_tab.current_session.async_send_text(f"kill {pid}\n")


async def main(connection):
    app = await iterm2.async_get_app(connection)
    window = app.current_terminal_window
    new_window = await iterm2.Window.async_create(connection, profile="wide")
    cmd_tab = new_window.current_tab
    if window is not None:
        for tab in window.tabs:
            await kill_tab_command(tab, cmd_tab)
        await kill_tab_command(cmd_tab, cmd_tab)
    else:
        print("No current window")


iterm2.run_until_complete(main)
