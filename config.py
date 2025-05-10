# FlashBar - config.py -> Loads the user config
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

from configparser import ConfigParser

class Config(ConfigParser):
    """Loads the configs from the user/settings.cfg config file
    
    It uses the ConfigParser class to read the configs and a dict
    to map the different sections to different methods.
    """
    def __init__(
        self, 
        *types: str
    ) -> None:
        """Initializes the Config
        
        It creates a ConfigParser
        """
        super().__init__()
        self.read('user/settings.cfg')
        self.type = types
        
        map = {
            'UI': self.UI,
            'CONTROL': self.Control,
            'SPIDER': self.Spider,
            'DB': self.DB,
            'SEARCH': self.Search,
            'LOGGING': self.Logging
        }
        for string in types:
            map[string.upper()]()
    
    def UI(self) -> None:
        """Loads every setting from the UI section
        """
        self.FADE_TIMER = self.getint('UI', 'FADE_TIMER', fallback=20)
        self.ICON_WIDTH = self.getint('UI', 'ICON_WIDTH', fallback=32)
        self.ICON_HEIGHT = self.getint('UI', 'ICON_HEIGHT', fallback=32)
    
    def Control(self) -> None:
        """Loads every setting from the Control section
        """
        self.KEY1 = self.get("Control", "KEY1", fallback="ctrl")
        self.KEY2 = self.get("Control", "KEY2", fallback="space")
    
    def Spider(self) -> None:
        """Loads every setting from the Spider section
        """
        self.BATCH_SIZE = self.getint("Spider", "BATCH_SIZE", fallback=16384)
    
    def DB(self) -> None:
        """Loads every setting from the DB section
        """
        self.CHUNK_SIZE = self.getint("DB", "CHUNK_SIZE", fallback=50000)
    
    def Search(self) -> None:
        """Loads every setting from the Search section
        """
        self.MIN_MATCH = self.getint("Search", "MIN_MATCH", fallback=50)
        self.MAX_RESULTS = self.getint("Search", "MAX_RESULTS", fallback=10)
    
    def Logging(self) -> None:
        """Loads every setting from the Logging section
        """
        self.INTERVAL = self.getint("Logging", "INTERVAL", fallback=10)