#!/usr/bin/env python3.7

import iterm2


async def launch_system(window, directory, command):
    tab = await window.async_create_tab()
    session = tab.current_session
    if directory:
        await session.async_send_text(f"cd {directory};{command}\n")
    else:
        await session.async_send_text(f"{command}\n")
    await tab.async_set_title(command)


async def main(connection):
    app = await iterm2.async_get_app(connection)
    window = await iterm2.Window.async_create(connection, profile="wide")
    if window is not None:
        await launch_system(window, "~/code/lola-server", "serverweb")
        await launch_system(window, "~/code/lola-server", "serverworkers")
        await launch_system(window, "~/code/lola-travel-service", "travelweb")
        await launch_system(window, "~/code/lola-travel-service", "travelworkers")
        await launch_system(window, "~/code/python-services", "threev")
        await launch_system(window, "~/code/python-services", "priceline")
        await launch_system(window, "~/code/python-services", "pricelinecars")
        await launch_system(window, "~/code/python-services", "ean")
        await launch_system(window, "~/code/python-services", "spend")
        await launch_system(window, "~/code/secrets", "secretsweb")
        await launch_system(window, "~/code/wallet", "wallet")
        await launch_system(window, "~/code/lola-desktop", "desktoplocal")
        await launch_system(window, "~/code/email-template-service", "emailtemplate")
        await launch_system(window, None, "ngrokSpend")
    else:
        print("No current window")


iterm2.run_until_complete(main)
