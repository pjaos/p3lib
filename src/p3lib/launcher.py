#!/bin/env python3

import os
import stat
import sys
import platform
from pathlib import Path
import shutil
import plistlib

class LauncherBase(object):
    """@brief The base class for the Launcher class. Defines methods and vars that are generic."""

    def __init__(self, icon_file, app_name):
        """@brief Constructor
           @param icon_file The icon file for the launcher.
           @param app_name The name of the application.
                           If not defined then the name of the program executed at startup is used.
                           This name has _ and - character replace with space characters and each
                           word starts with a capital letter."""
        self._uio = None
        self._startup_file = self._get_startup_file()
        self._set_app_name(app_name)
        self._check_icon(icon_file)

    def _set_app_name(self, app_name=None):
        """@brief Set the name of the app.
        @param app_name The name of the app or None. If None then the name of the app is the
                basename of the startup file minus it's extension."""
        if app_name:
            self._app_name = app_name

        else:
            # Get just the name of the file
            app_name = os.path.basename(self._startup_file)
            # Remove file extension
            app_name = os.path.splitext(app_name)[0]
            app_name = app_name.replace('_', ' ')
            app_name = app_name.replace('-', ' ')
            app_name = app_name.title()
            self._app_name = app_name

    def _get_startup_file(self):
        """@return Get the abs name of the program first started."""
        return os.path.abspath(sys.argv[0])

    def info(self, msg):
        """@brief Show an info level message to the user.
        @param msg The msessage text."""
        if self._uio:
            self._uio.info(msg)

    def _check_icon(self, icon_file):
        """@brief Check that the icon file exists as this is required for the gnome desktop entry.
        @param icon_file The name of the icon file.
        return None"""
        self._abs_icon_file = os.path.abspath(icon_file)
        if not os.path.isfile(self._abs_icon_file):
            startup_path = os.path.dirname(self._startup_file)
            path1 = os.path.join(startup_path, 'assets')
            self._abs_icon_file = os.path.join(path1, icon_file)
            if not os.path.isfile(self._abs_icon_file):
                startup_parent_path = os.path.join(startup_path, '..')
                path2 = os.path.join(startup_parent_path, 'assets')
                self._abs_icon_file = os.path.join(path2, icon_file)
                if not os.path.isfile(self._abs_icon_file):
                    # Try all the site packages folders we know about.
                    for path in sys.path:
                        if 'site-packages' in path:
                            site_packages_path = path
                            path3 = os.path.join(site_packages_path, 'assets')
                            self._abs_icon_file = os.path.join(path3, icon_file)
                            if os.path.isfile(self._abs_icon_file):
                                return self._abs_icon_file

                    raise Exception(f"{self._app_name} icon file ({icon_file}) not found.")

    def addLauncherArgs(self,
                        parser,
                        short_add_arg='-a',
                        long_add_arg='--add_launcher',
                        short_remove_arg='-r',
                        long_remove_arg='--remove_launcher'):
        """@brief Add the Launcher command line args to an argparse.ArgumentParser instance.
        @param parser An argparse.ArgumentParser instance.
        @parm short_add_arg Short form argument for adding a launcher icon.
        @param long_add_arg Long form argument for adding a launcher icon.
        @parm short_remove_arg Short form argument for removing a launcher icon.
        @param long_remove_arg Long form argument for removing a launcher icon.
        @return The options instance."""

        if platform.system() == 'Linux':
            parser.add_argument(short_add_arg,
                                long_add_arg,
                                action='store_true',
                                help="Add a Linux gnome desktop launcher.")
            parser.add_argument(short_remove_arg,
                                long_remove_arg,
                                action='store_true',
                                help="Remove a Linux gnome desktop launcher.")

        if platform.system() == 'Windows':
            parser.add_argument(short_add_arg,
                                long_add_arg,
                                action='store_true',
                                help="Add a startup icon to the Windows start button.")
            parser.add_argument(short_remove_arg,
                                long_remove_arg,
                                action='store_true',
                                help="Remove a startup icon from the Windows start button.")

        if platform.system() == 'Darwin':
            parser.add_argument(short_add_arg,
                                long_add_arg,
                                action='store_true',
                                help="Add a startup icon to the MacOS Desktop.")
            parser.add_argument(short_remove_arg,
                                long_remove_arg,
                                action='store_true',
                                help="Remove a startup icon from the MacOS Desktop.")

    def handleLauncherArgs(self,
                           args,
                           uio=None):
        """@brief Handle the add or remove startup icon launcher arguments.
        @param args object returned from parser.parse_args()
        @param uio A p3lib.uio.UIO instance or can be left as None.
        @return True if a launcher add or remove cmd args was found and processed."""
        self._uio = uio
        handled = False
        if hasattr(args, "add_launcher") and args.add_launcher:
            self.create()
            handled = True

        if hasattr(args, "remove_launcher") and args.remove_launcher:
            self.delete()
            handled = True

        return handled

    def create(self):
        raise NotImplementedError("create() not implemented in Launcher() class.")

    def delete(self):
        raise NotImplementedError("create() not implemented in Launcher() class.")


_platform = platform.system()
if _platform == 'Linux':

    class Launcher(LauncherBase):
        """@brief Responsible for adding and removing gnome desktop files for launching applications on a Linux system."""

        def __init__(self, icon_file, app_name=None, comment='', categories='Utility'):
            """@brief Constructor.
            @param icon_file  The name of the icon file. This can be an absolute file name the filename on it's own.
                                If just a filename is passed then the icon file must sit in a folder named 'assets'.
                                This assets folder must be in the same folder as the startup file, it's parent or
                                the python3 site packages folder.
            @param app_name   The name of the application.
                                If not defined then the name of the program executed at startup is used.
                                This name has _ and - character replace with space characters and each
                                word starts with a capital letter.
            @param comment    This comment should detail what the program does and is stored
                                in the gnome desktop file that is created.
            @param categories The debian app categories. default='Utility;'.
                              Options
                                Utility
                                Development
                                Graphics
                                AudioVideo
                                Network
                                Office
                                Game
                                Settings
                                System
            """
            super().__init__(icon_file, app_name)
            self._gnome_desktop_file = None
            self._comment = comment
            self._categories = categories
            self._gnome_desktop_file = self._get_gnome_desktop_file()

        def _get_gnome_desktop_file(self):
            """@brief Determine and return the name of the gnome desktop file.
            @return The gnome desktop file."""
            # Get just the name of the file
            desktop_file_name = os.path.basename(self._startup_file)
            # Remove file extension
            desktop_file_name = os.path.splitext(desktop_file_name)[0]
            # Get just the name of the file
            desktop_file_name = os.path.basename(self._startup_file)
            # Remove file extension
            desktop_file_name = os.path.splitext(desktop_file_name)[0]
            if not desktop_file_name.endswith('.desktop'):
                desktop_file_name = desktop_file_name + '.desktop'
            home_folder = os.path.expanduser("~")
            gnome_desktop_apps_folder = os.path.join(home_folder, '.local/share/applications')
            gnome_desktop_file = os.path.join(gnome_desktop_apps_folder, desktop_file_name)
            return gnome_desktop_file

        def _update_permissions(self, path):
            path = os.path.expanduser(path)
            # Make the file executable
            mode = os.stat(path).st_mode
            os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        def _create_gnome_desktop_file(self):
            """@brief Create the gnome desktop file for this app."""
            if os.path.isfile(self._gnome_desktop_file):
                raise Exception(f"{self._gnome_desktop_file} file already exists.")
            lines = []
            lines.append('[Desktop Entry]')
            lines.append('Version=1.0')
            lines.append('Type=Application')
            lines.append(f'Name={self._app_name}')
            lines.append(f'Comment={self._comment}')
            lines.append(f'Icon={self._abs_icon_file}')
            lines.append(f'Exec={self._startup_file}')
            lines.append('Terminal=false')
            if not self._categories.endswith(';'):
                self._categories = self._categories + ';'
            lines.append(f'Categories={self._categories}')

            with open(self._gnome_desktop_file, "w", encoding="utf-8") as fd:
                fd.write("\n".join(lines))

            self._update_permissions(self._gnome_desktop_file)

        def create(self, overwrite=True):
            """@brief Create a desktop icon.
               @param overwrite If True overwrite any existing file. If False raise an error if the file is already present."""
            # If this file not found error
            if not os.path.isfile(self._startup_file):
                raise Exception(f"{self._startup_file} file not found.")
            if overwrite:
                self.delete()
            self._create_gnome_desktop_file()
            self.info(f"Created {self._gnome_desktop_file} file.")
            self.info(f"The {self._app_name} gnome launcher was successfully created.")

        def delete(self):
            """@brief Delete the gnome desktop file if present.
            @return True if a desktop file was deleted."""
            deleted = False
            if os.path.isfile(self._gnome_desktop_file):
                os.remove(self._gnome_desktop_file)
                deleted = True
            if deleted:
                self.info(f"Removed {self._gnome_desktop_file} file.")
            return deleted

elif _platform == 'Windows':

    class Launcher(LauncherBase):
        """@brief Responsible for adding and removing Windows app shortcuts to the desktop for launching applications on a Windows system."""

        def __init__(self, icon_file, app_name=None):
            """@brief Constructor.
            @param icon_file  The name of the icon file. This can be an absolute file name the filename on it's own.
                                If just a filename is passed then the icon file must sit in a folder named 'assets'.
                                This assets folder must be in the same folder as the startup file, it's parent or
                                the python3 site packages folder.
            @param app_name   The name of the application.
                                If not defined then the name of the program executed at startup is used.
                                This name has _ and - character replace with space characters and each
                                word starts with a capital letter.
            """
            super().__init__(icon_file, app_name)

        """PJA rationalise this"""
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

        def create(self, overwrite=True):
            """@brief Create a start menu item to launch a program.
               @param overwrite If True overwrite any existing file. If False raise an error if the file is already present."""
            from win32com.client import Dispatch
            package_name = self._get_app_name()
            exe_name = f"{package_name}.exe"

            # Locate the pipx-installed executable
            pipx_venv_path = os.path.expanduser(f"~\\.local\\bin\\{exe_name}")
            if not os.path.isfile(pipx_venv_path):
                raise Exception(f"{pipx_venv_path} file not found.")

            if overwrite:
                self.delete()

            icon_path = self._abs_icon_file
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
            shortcut.IconLocation = icon_path
            shortcut.Save()

            if not os.path.isfile(shortcut_path):
                raise Exception(f"{shortcut_path} shortcut file missing after creation.")

            self.info(f"{shortcut_path} shortcut created.")

        def delete(self):
            shortcut_path = self._get_shortcut()

            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                self.info(f"Removed '{shortcut_path}' shortcut.")

elif _platform == 'Darwin':

    class Launcher(LauncherBase):
        """@brief Responsible for adding and removing shortcuts to the desktop for launching applications on a MacOS system."""

        def __init__(self, icon_file, app_name=None):
            """@brief Constructor.
            @param icon_file  The name of the icon file. This can be an absolute file name the filename on it's own.
                                If just a filename is passed then the icon file must sit in a folder named 'assets'.
                                This assets folder must be in the same folder as the startup file, it's parent or
                                the python3 site packages folder.
            @param app_name   The name of the application.
                                If not defined then the name of the program executed at startup is used.
                                This name has _ and - character replace with space characters and each
                                word starts with a capital letter."""
            super().__init__(icon_file, app_name)
            self._app_name
            desktop = Path.home() / "Desktop"
            self._app_path = desktop / f"{self._app_name}.app"
            self._contents = self._app_path / "Contents"
            self._macos = self._contents / "MacOS"
            self._resources = self._contents / "Resources"

        def _create_app(self):
            """@brief Create a MacOS app folder with the required files to launch an app."""
            self.delete()
            # Create app structure
            self._macos.mkdir(parents=True)
            self._resources.mkdir()

            # Executable script
            exec_path = self._macos / self._app_name
            exec_path.write_text(f"#!/bin/bash\nopen {self._startup_file}\n")
            exec_path.chmod(0x755)

            # Info.plist
            plist = {
                'CFBundleName': self._app_name,
                'CFBundleIdentifier': f'com.example.{self._app_name.lower()}',
                'CFBundleVersion': '1.0',
                'CFBundlePackageType': 'APPL',
                'CFBundleExecutable': self._app_name,
                'CFBundleIconFile': 'app_icon.icns',
            }
            with open(self._contents / 'Info.plist', 'wb') as f:
                plistlib.dump(plist, f)

            # Copy icon (must be .icns format)
            shutil.copy(self._abs_icon_file, self._resources / 'app_icon.icns')
            self.info(f"Created {self._app_path}")

        def create(self, overwrite=False):
            """@brief Create a desktop icon.
            @param overwrite If True overwrite any existing file. If False raise an error if the file is already present."""
            self._create_app()

        def delete(self):
            """@brief Delete the gnome desktop file if present.
            @return True if a desktop file was deleted."""
            # Clean old app if exists
            if self._app_path.exists():
                shutil.rmtree(self._app_path)
                self.info(f"Removed '{self._app_path}'")

else:
    raise Exception("{_platform} platform is not supported by Launcher.")

