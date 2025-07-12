import argparse
from time import sleep
from p3lib.launcher import Launcher
from p3lib.uio import UIO
from nicegui import ui, app

# A GUI that is launched by the launcher file
# This provides a mechanism to test the Launchers ability to startup
# the GUI on all supported platforms.
counter = 0
def show_running_gui():
    global counter
    ui.label(f'Counter should increment while program is running.')
    label = ui.label(f'Counter: {counter}')

    def update_counter():
        global counter
        counter += 1
        label.text = f'Counter: {counter}'

    # Update the counter every second
    ui.timer(interval=1.0, callback=update_counter)

    def shutdown():
        print("Shutting down...")
        ui.timer(0.1, lambda: app.shutdown())

    with ui.row():
        ui.button('Quit', on_click=shutdown)

    ui.run(reload=False)


def main():
    uio = UIO()
    parser = argparse.ArgumentParser(description="Example to create and delete app launcher.",
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    launcher = Launcher("icon.ico")
    launcher.addLauncherArgs(parser)
    args = parser.parse_args()
    handled = launcher.handleLauncherArgs(args, uio=uio)
    if not handled:
        # Typically you would handle other cmd line options here...

        # For purposes of this example we show a gui that shows an incrementing count to indicate it is running
        # The GUI can be closed by the user selecting the Quit button.
        show_running_gui()

if __name__ in {"__main__", "__mp_main__"}:
    main()
