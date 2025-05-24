# FlashBar - modules/drive.py -> Handles some of the logic regarding pathing and logical drives
# Copyright (C) 2025  Florian, Floerianc on Github (https://www.github.com/floerianc)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import win32api
import os
import sys
import winreg

class OSM:
    """This class manages most of the work with the OS itself
    """
    def __init__(self) -> None:
        pass
    
    @property
    def autostart(self) -> str:
        """Returns the path to the windows autostart

        Returns:
            str: path as string
        """
        appdata = os.getenv("appdata")
        if appdata:
            return appdata+"\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        else:
            return ""
    
    @property
    def drives(self) -> list[str]:
        """Returns the list of logical drives in the system
        
        Returns:
            list[str]: list of drives
        """
        return win32api.GetLogicalDriveStrings().split("\000")[:-1] # C:\\ & E:\\
    
    def dirFiles(self, root: str) -> list:
        """Returns the full file path of each file in a directory
        
        Args:
            root (str): root path
            
        Returns:
            list: list of full paths
        """
        # root + file for each file in directory if its actually a file lol
        try:
            return [os.path.join(root, file) for file in os.listdir(root) if os.path.isfile(os.path.join(root, file))]
        except Exception as e:
            print(e)
            return []
    
    def splitPath(self, path: str) -> list:
        """Splits path up into two.
        
        - Path
        - Filename
        
        Args:
            path (str): full path to the file
        
        Returns:
            list: splitted up list
        """
        return path.rsplit("\\", 1)
    
    def _RunRegistry(self) -> None:
        """Adds the program to the autorun in Windows registry
        """
        if getattr(sys, 'frozen', False):
            path = sys.executable
        else:
            path = os.path.abspath(sys.argv[0])
        key = winreg.HKEY_CURRENT_USER
        key_value = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        
        open = winreg.OpenKey(key, key_value, 0, winreg.KEY_ALL_ACCESS)
        
        winreg.SetValueEx(open, "FlashBar", 0, winreg.REG_SZ, path)
        winreg.CloseKey(open)