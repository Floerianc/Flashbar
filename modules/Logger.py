# FlashBar - modules/Logger.py -> Logs information
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

import logging
import sys
import time
import config as Config
from PyQt5.QtCore import QThread
from typing import(
    Any,
    TYPE_CHECKING
)
from modules.osm import OSM

if TYPE_CHECKING:
    from app import SearchBar

osm = OSM()
exePath = osm.exeDir()

logging.basicConfig(
    filename=f"{exePath}\\log.log",
    format='%(asctime)s %(message)s',
    filemode='w'
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.info("Working directory: %s", exePath)

class Logger(QThread):
    """Logger class logs information regarding the program

    **Inherits from QThread**
    """
    def __init__(
        self, 
        window: 'SearchBar'
    ) -> None:
        """Initializes the program by loading the config,
        its constants and the window data

        Args:
            windowData (dict[str, any]): data of the window
        """
        super().__init__()
        self.log = logger
        self.config = Config.Config('Logging')
        self.window = window
        self.data = window.dataset
        self.filesAmount = 0
    
    def getFileAmount(self) -> int:
        """Returns the amount of files in the dataset

        Returns:
            int: Amount of files
        """
        return sum(len(files) for files in list(self.data['files'].values()) if type(files) is set)
    
    def run(self) -> None:
        """Sleeps for a while (declared in config)
        and then logs the amount of files and templates.
        """
        while True:
            time.sleep(self.config.INTERVAL)
            files = self.getFileAmount()
            self.log.info("%d Files, %d Templates", self.window.files, len(self.data['templates']))