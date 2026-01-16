#!/bin/env python3

import os
import stat
import sys
import platform
from pathlib import Path
import shutil
import plistlib
from PIL import Image
import subprocess
from time import sleep
from p3lib.helper import get_assets_file

class LauncherBase(object):
    """@brief The base class for the Launcher class. Defines methods and vars that are generic."""

    def __init__(self, icon_file, app_name, module_name=None):
        """@brief Constructor
           @param icon_file The icon file for the launcher.
           @param app_name The name of the application.
                           If not defined then the name of the program executed at startup is used.
                           This name has _ and - character replace with space characters and each
                           word starts with a capital letter.
           @param module_name The name of the python module containing the assets folder.
                              The get_assets_file() method uses this to find the assets folder containing
                              the launcher icon file. Attempts are made to determine this from the python
                              startup env but this is dependant upon the startup env. It is more reliable
                              to set this when creating the Launcher instance."""
        self._uio = None
        self._module_name = module_name
        self._startup_file = self._get_startup_file()
        self._set_app_name(app_name)
        self._check_icon(icon_file)

    def _set_app_name(self, app_name=None):
        """@brief Set the name of the app.
           @param app_name The name of the app or None. If None then the name of the app is the
                           basename of the startup file minus it's extension."""
        if app_name:
            app_name = app_name.replace(' ', '_')
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

    def _get_exec_cmd(self):
        """@brief Get the command to execute the app."""
        # We use this exec cmd if we can't find others installed in platform local paths
        exec_cmd = self._get_startup_file()
        exec_cmd_path = Path(exec_cmd)
        filename = exec_cmd_path.name.replace('.py','')
        module_name = exec_cmd_path.parent.name
        _platform = platform.system()
        home_folder = os.path.expanduser("~")
        if _platform == 'Linux':
            local_folder = os.path.join(home_folder, ".local")
            local_bin_folder = os.path.join(local_folder, "bin")
            local_bin_exec_cmd = os.path.join(local_bin_folder, filename)
            if os.path.isfile(local_bin_exec_cmd):
                exec_cmd = local_bin_exec_cmd

        elif _platform == 'Windows':
            local_appdata = os.environ["LOCALAPPDATA"]
            programs_dir = os.path.join(local_appdata, 'Programs')
            module_dir = os.path.join(programs_dir, module_name)
            module_bin_dir = os.path.join(module_dir, 'bin')
            local_bin_exec_cmd = os.path.join(module_bin_dir, filename)
            if os.path.isfile(local_bin_exec_cmd):
                exec_cmd = local_bin_exec_cmd

        elif _platform == 'Darwin':
            app_support_folder = os.path.join(home_folder, "Application Support")
            module_dir = os.path.join(app_support_folder, module_name)
            module_bin_dir = os.path.join(module_dir, 'bin')
            local_bin_exec_cmd = os.path.join(module_bin_dir, filename)
            if os.path.isfile(local_bin_exec_cmd):
                exec_cmd = local_bin_exec_cmd

        return exec_cmd

    def info(self, msg):
        """@brief Show an info level message to the user.
        @param msg The msessage text."""
        if self._uio:
            self._uio.info(msg)

    def _check_icon(self, icon_file):
        """@brief Check that the icon file exists as this is required for the gnome desktop entry.
        @param icon_file The name of the icon file.
        return None"""
        if not icon_file.endswith('.png'):
            raise Exception(f"{icon_file} icon file must have .png extension.")
        # Search for the file
        self._abs_icon_file = get_assets_file(icon_file, module_name=self._module_name)
        if self._abs_icon_file is None:
            raise Exception(f"{self._app_name} icon file ({icon_file}) not found.")
        return self._abs_icon_file

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

        def __init__(self, icon_file, app_name=None, comment='', categories='Utility', module_name=None):
            """@brief Constructor.
            @param icon_file  The name of the icon file (must be a png file).
                              This can be an absolute file name the filename on it's own.
                              If just a filename is passed then the icon file must sit in a folder named 'assets'.
                              This assets folder must be in the same folder as the startup file, it's parent or
                              the python3 site packages folder where it is deployed when a python wheel is built.
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
            @param module_name The name of the python module containing the assets folder.
                              The get_assets_file() method uses this to find the assets folder containing
                              the launcher icon file. Attempts are made to determine this from the python
                              startup env but this is dependant upon the startup env. It is more reliable
                              to set this when creating the Launcher instance.
            """
            super().__init__(icon_file, app_name, module_name=module_name)
            self._comment = comment
            self._categories = categories
            self._gnome_desktop_files = self._get_gnome_desktop_files()

        def _get_gnome_desktop_files(self):
            """@brief Determine and return a list of the gnome desktop files.
               @return A list of gnome desktop files."""
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
            gnome_desktop_apps_folder1 = os.path.join(home_folder, '.local/share/applications')
            gnome_desktop_file1 = os.path.join(gnome_desktop_apps_folder1, desktop_file_name)

            gnome_desktop_apps_folder2 = os.path.join(home_folder, 'Desktop')
            if os.path.isdir(gnome_desktop_apps_folder2):
                gnome_desktop_file2 = os.path.join(gnome_desktop_apps_folder2, desktop_file_name)
                gnome_desktop_files = (gnome_desktop_file1, gnome_desktop_file2)
            else:
                gnome_desktop_files = (gnome_desktop_file1)

            return gnome_desktop_files

        def _update_permissions(self, path):
            path = os.path.expanduser(path)
            # Make the file executable
            mode = os.stat(path).st_mode
            os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        def _create_gnome_desktop_files(self):
            """@brief Create the gnome desktop file for this app."""
            exec_cmd = self._get_exec_cmd()
            for gnome_desktop_file in self._gnome_desktop_files:
                if os.path.isfile(gnome_desktop_file):
                    raise Exception(f"{gnome_desktop_file} file already exists.")
                lines = []
                lines.append('[Desktop Entry]')
                lines.append('Version=1.0')
                lines.append('Type=Application')
                lines.append(f'Name={self._app_name}')
                lines.append(f'Comment={self._comment}')
                lines.append(f'Icon={self._abs_icon_file}')
                lines.append(f'Exec={exec_cmd}')
                lines.append('Terminal=false')
                if not self._categories.endswith(';'):
                    self._categories = self._categories + ';'
                lines.append(f'Categories={self._categories}')

                with open(gnome_desktop_file, "w", encoding="utf-8") as fd:
                    fd.write("\n".join(lines))

                self._update_permissions(gnome_desktop_file)
                self.info(f"Created {gnome_desktop_file} file.")

        def create(self, overwrite=True):
            """@brief Create a desktop icon.
               @param overwrite If True overwrite any existing file. If False raise an error if the file is already present."""
            # If this file not found error
            if not os.path.isfile(self._startup_file):
                raise Exception(f"{self._startup_file} file not found.")
            if overwrite:
                self.delete()
            self._create_gnome_desktop_files()
            self.info(f"The {self._app_name} gnome launcher was successfully created.")

        def delete(self):
            """@brief Delete the gnome desktop files if present.
               @return True if a desktop files were deleted."""
            del_count = 0
            for gnome_desktop_file in self._gnome_desktop_files:
                if os.path.isfile(gnome_desktop_file):
                    os.remove(gnome_desktop_file)
                    self.info(f"Removed {gnome_desktop_file} file.")
                    del_count += 1

            deleted = False
            if del_count == len(self._gnome_desktop_files):
                deleted = True
            return deleted

elif _platform == 'Windows':

    class Launcher(LauncherBase):
        """@brief Responsible for adding and removing Windows app shortcuts to the desktop for launching applications on a Windows system."""

        def __init__(self, icon_file, app_name=None, module_name=None):
            """@brief Constructor.
            @param icon_file  The name of the icon file. This can be an absolute file name the filename on it's own.
                                If just a filename is passed then the icon file must sit in a folder named 'assets'.
                                This assets folder must be in the same folder as the startup file, it's parent or
                                the python3 site packages folder.
            @param app_name   The name of the application.
                                If not defined then the name of the program executed at startup is used.
                                This name has _ and - character replace with space characters and each
                                word starts with a capital letter.
            @param module_name The name of the python module containing the assets folder.
                              The get_assets_file() method uses this to find the assets folder containing
                              the launcher icon file. Attempts are made to determine this from the python
                              startup env but this is dependant upon the startup env. It is more reliable
                              to set this when creating the Launcher instance.
            """
            super().__init__(icon_file, app_name, module_name=module_name)

        def _get_exe_name(self):
            """@return The name of the running program with a .exe extension."""
            app_name = self._get_startup_file()
            app_name = os.path.basename(app_name)
            app_name = app_name.replace(".py", "")
            return app_name + ".exe"

        def _get_python_module_file(self):
            """@return The name of the python module and filename without the .py extension."""
            app_name = self._get_startup_file()
            p = Path(app_name)
            filename = p.name
            filename = filename.replace('.py', '')
            module = p.parent.name
            module_file = module + '.' + filename
            return module_file

        def _get_shortcut_folder(self):
            temp_dir = os.path.join(os.getenv("TEMP"), "my_temp_shortcuts")
            os.makedirs(temp_dir, exist_ok=True)
            return temp_dir

        def _get_shortcut(self):
            package_name = self._app_name
            desktop = os.path.join(os.getenv("USERPROFILE"), "Desktop")
            shortcut_path = os.path.join(desktop, f"{package_name}.lnk")
            return shortcut_path

        def _convert_png_to_ico(self):
            """@brief Convert the iniital png file to a windows ico file.
            @return The abs path of the converted ico file."""
            # Convert the png file to an ico file for use in the Windows shortcut
            img = Image.open(self._abs_icon_file)
            ico_icon_file = self._abs_icon_file.lower().replace(".png", '.ico')
            img.save(ico_icon_file, sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
            self.info(f"Converted png file to ico file: {ico_icon_file}")
            return ico_icon_file

        def create(self, overwrite=True):
            """@brief Create a start menu item to launch a program.
               @param overwrite If True overwrite any existing file. If False raise an error if the file is already present."""
            from win32com.client import Dispatch
            args = None
            exe_name = self._get_exe_name()

            # Locate the pipx-installed executable
            pipx_venv_path = os.path.expanduser(f"~\\.local\\bin\\{exe_name}")
            if not os.path.isfile(pipx_venv_path):
                # Get the full path to the python.exe that we launched ths file from
                python_exe = sys.executable
                if os.path.isfile(python_exe):
                    # Use this python file.
                    pipx_venv_path = python_exe
                    #Set the args required
                    args = f'-m {self._get_python_module_file()}'
                else:
                    raise Exception(f"{pipx_venv_path} and {python_exe} files not found .")

            if overwrite:
                self.delete()

            # Convert the png file to an ico file for use in the Windows shortcut
            ico_icon_file = self._convert_png_to_ico()

            shortcut_path = self._get_shortcut()

            # Create the shortcut
            shell = Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = pipx_venv_path  # Path to your executable or script
            if args:
                shortcut.Arguments = args
            shortcut.WorkingDirectory = os.path.dirname(pipx_venv_path)
            shortcut.IconLocation = ico_icon_file
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

        def __init__(self, icon_file, app_name=None, module_name=None):
            """@brief Constructor.
            @param icon_file  The name of the icon file. This can be an absolute file name the filename on it's own.
                                If just a filename is passed then the icon file must sit in a folder named 'assets'.
                                This assets folder must be in the same folder as the startup file, it's parent or
                                the python3 site packages folder.
            @param app_name   The name of the application.
                                If not defined then the name of the program executed at startup is used.
                                This name has _ and - character replace with space characters and each
                                word starts with a capital letter.
            @param module_name The name of the python module containing the assets folder.
                              The get_assets_file() method uses this to find the assets folder containing
                              the launcher icon file. Attempts are made to determine this from the python
                              startup env but this is dependant upon the startup env. It is more reliable
                              to set this when creating the Launcher instance."""
            super().__init__(icon_file, app_name, module_name=module_name)
            self._app_name
            desktop = Path.home() / "Desktop"
            self._app_path = desktop / f"{self._app_name}.app"
            self._contents = self._app_path / "Contents"
            self._macos = self._contents / "MacOS"
            self._resources = self._contents / "Resources"

        def _convert_png_to_icns(self):
            """@brief Convert the iniital png file to an isnc file for use on MacOS.
                    This method can only be called on MacOS
            @return The abs path of the converted icns file."""
            base = Image.open(self._abs_icon_file)
            sizes = [16, 32, 128, 256, 512, 1024]

            icon_folder = os.path.dirname(self._abs_icon_file)
            iconset = Path(icon_folder, 'my.iconset')
            iconset.mkdir(exist_ok=True)

            for size in sizes:
                img = base.resize((size, size))
                filename = iconset / f'icon_{size}x{size}.png'
                img.save(filename)

            # use iconutil MacOS util program to create the icns files
            subprocess.run(['iconutil', '--convert', 'icns', iconset])

            # Clean the png files created
            if iconset.exists():
                shutil.rmtree(iconset)

            return str(iconset).replace('.iconset', '.icns')

        def _get_python_path(self):
            """@brief Get the python file inside the venv."""
            pos = self._startup_file.find('/venv/')
            if pos:
                python_path = self._startup_file[:pos+6] + 'bin/python'
                if not os.path.isfile(python_path):
                    raise Exception(f"{python_path} file not found.")
                return python_path
            else:
                raise Exception(f"Failed to find the venv in {self._startup_file}")

        def _get_main_module(self):
            """@brief Get the python module to run."""
            path = Path(self._startup_file)
            filename = path.name
            return f"{path.parent.name}.{filename.replace('.py','')}"

        def _create_app(self):
            """@brief Create a MacOS app folder with the required files to launch an app."""
            self.delete()
            # Create app structure
            self._macos.mkdir(parents=True)
            self._resources.mkdir()

            # Executable script
            exec_path = self._macos / self._app_name
            python_path = self._get_python_path()
            main_module = self._get_main_module()
            exec_path.write_text(f"#!/bin/bash\nexec {python_path} -m {main_module}\n")
            exec_path.chmod(0x755)

            # Info.plist
            plist = {
                'CFBundleName': self._app_name,
                'CFBundleIdentifier': f'com.example.{self._app_name.lower()}',
                'CFBundleVersion': '1.0',
                'CFBundlePackageType': 'APPL',
                'CFBundleExecutable': self._app_name,
                'CFBundleIconFile': 'app_icon',
            }
            with open(self._contents / 'Info.plist', 'wb') as f:
                plistlib.dump(plist, f)

            # Convert the png file to an icns file for use on MacOS
            icns_file = self._convert_png_to_icns()

            # Copy icon (must be .icns format)
            destfile = self._resources / 'app_icon.icns'
            shutil.copy(icns_file, destfile)
            # Finder does not update the icon unless we update the folder once created.
            sleep(.1)
            subprocess.run(['touch', self._app_path])
            # Stop finder, it will relaunch as sometimes it shows two icons on the desktop
            subprocess.run(['killall', 'Finder'])
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

