import sys
import os
from p3lib.helper import getAbsFile


class WindowsApp():
    """@brief Responsible for adding and removing Windows app shortcuts to the desktop for launching applications on a Windows system."""

    def __init__(self, uio=None):
        self._uio = uio

    def info(self, msg):
        """@brief Show an info level message to the user.
           @param msg The msessage text."""
        if self._uio:
            self._uio.info(msg)

    def _get_startup_file(self):
        """@return Get the abs name of the program first started."""
        return os.path.abspath(sys.argv[0])

    def _get_app_name(self):
        """@return The name of the running program without the .py extension."""
        app_name = self._get_startup_file()
        app_name = os.path.basename(app_name)
        return app_name.replace(".py", "")

    def _get_shortcut_folder(self):
        temp_dir = os.path.join(os.getenv("TEMP"), "my_temp_shortcuts")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _get_shortcut(self):
        package_name = self._get_app_name()
        desktop = os.path.join(os.getenv("USERPROFILE"), "Desktop")
        shortcut_path = os.path.join(desktop, f"{package_name}.lnk")
        return shortcut_path

    def create(self, icon_filename=None):
        """@brief Create a start menu item to launch a program.
           @param package_name The name of the package.
           @param icon_filename The name of the icon file."""
        from win32com.client import Dispatch
        package_name = self._get_app_name()
        exe_name = f"{package_name}.exe"

        # Locate the pipx-installed executable
        pipx_venv_path = os.path.expanduser(f"~\\.local\\bin\\{exe_name}")
        if not os.path.isfile(pipx_venv_path):
            raise Exception(f"{pipx_venv_path} file not found.")

        icon_path = None
        if icon_filename:
            icon_path = getAbsFile(icon_filename)
        if icon_path:
            if os.path.isfile(icon_path):
                self.info(f"{icon_path} icon file found.")
            else:
                raise Exception(f"{icon_path} file not found.")

        shortcut_path = self._get_shortcut()

        # Create the shortcut
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = pipx_venv_path  # Path to your executable or script
        shortcut.WorkingDirectory = os.path.dirname(pipx_venv_path)
        shortcut.IconLocation = icon_path  # Optional: Set an icon
        shortcut.Save()

        if not os.path.isfile(shortcut_path):
            raise Exception(f"{shortcut_path} shortcut file missing after creation.")

        self.info(f"{shortcut_path} shortcut created.")

    def delete(self):
        shortcut_path = self._get_shortcut()

        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            self.info(f"Removed '{shortcut_path}' shortcut.")
        else:
            raise Exception(f"{shortcut_path} file not found.")
