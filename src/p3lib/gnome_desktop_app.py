#!/bin/env python3

import os
import sys
import platform

class GnomeDesktopApp(object):
    """@brief Responsible for adding and removing gnome desktop files for launching applications on a Linux system."""

    @staticmethod
    def IsLinux():
        """@return True if running on a Linux platform."""
        linux = False
        if platform.system() == "Linux":
            linux = True
        return linux

    def __init__(self, icon_file, app_name=None, comment='', categories='Utility;Application;'):
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
           @param categories The debian app categories. default='Utility;Application;'.
        """
        if not GnomeDesktopApp.IsLinux():
            raise Exception("The GnomeDesktopApp() class cannot be instantiated on a non Linux platform")
        self._startup_file = self._get_startup_file()
        self._gnome_desktop_file = None
        self._app_name = self._get_app_name()
        self._check_icon(icon_file)
        self._comment = comment
        self._categories = categories
        self._gnome_desktop_file = self._get_gnome_desktop_file()

    def _get_startup_file(self):
        """@return Get the abs name of the program first started."""
        return os.path.abspath(sys.argv[0])

    def _get_app_name(self, app_name=None):
        """@brief Get the name of the app.
           @param app_name The name of the app or None. If None then the name of the app is the
                  basename of the startup file minus it's extension.
           @return The name of the app."""
        if not app_name:
            # Get just the name of the file
            app_name = os.path.basename(self._startup_file)
            # Remove file extension
            app_name = os.path.splitext(app_name)[0]
            app_name = app_name.replace('_', ' ')
            app_name = app_name.replace('-', ' ')
            app_name = app_name.title()
        return app_name

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

    def _get_gnome_desktop_file(self):
        """@brief Determine and return the name of the gnome desktop file.
           @return The gnome desktop file."""
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

    def _create_gnome_desktop_file(self):
        """@brief Create the gnome desktop file for this app."""
        if os.path.isfile(self._gnome_desktop_file):
            raise Exception(f"{self._gnome_desktop_file} file already exists.")
        lines = []
        lines.append('[Desktop Entry]')
        lines.append('Version=1.0')
        lines.append('Type=Application')
        lines.append('Encoding=UTF-8')
        lines.append(f'Name={self._app_name}')
        lines.append(f'Comment={self._comment}')
        lines.append(f'Icon={self._abs_icon_file}')
        lines.append(f'Exec={self._startup_file}')
        lines.append('Terminal=false')
        lines.append(f'Categories={self._categories}')

        with open(self._gnome_desktop_file, "w", encoding="utf-8") as fd:
            fd.write("\n".join(lines))

    def create(self, overwrite=False):
        """@brief Create a desktop icon.
           @param overwrite If True overwrite any existing file. If False raise an error if the file is already present."""
        # If this file not found error
        if not os.path.isfile(self._startup_file):
            raise Exception(f"{self._startup_file} file not found.")
        if overwrite:
            self.delete()
        self._create_gnome_desktop_file()

    def delete(self):
        """@brief Delete the gnome desktop file if present.
           @return True if a desktop file was deleted."""
        deleted = False
        if os.path.isfile(self._gnome_desktop_file):
            os.remove(self._gnome_desktop_file)
            deleted = True
        return deleted

"""
    Example usage
    gda = GnomeDesktopApp('savings.png')
    gda.create(overwrite=True)
"""




