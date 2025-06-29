# FlashBar - ./modules/FileManager/FileDBLoader.py -> Loads the DB
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

import time
import queue
import os
import zlib
import json
from PyQt5.QtCore import QThread
from typing import(
    Any,
    Union
)
import modules.OSM as osm
from modules.Logger import Logger

class FileDBLoader(QThread):
    """This is a seperate class to load
    a pre-existing DB into the program to regulate CPU usage

    **Inherits from QThread**
    """
    def __init__(
        self, 
        log: Union[Logger, None]
    ) -> None:
        self.log = log
        self.osm = osm.OSM()
        super().__init__()
    
    def listToSet(
        self, 
        l: list
    ) -> set:
        """Converts a list of tuples into a set of tuples

        Args:
            l (list): list of tuples

        Returns:
            set: set of tuples
        """
        return set((template, filename) for template, filename in l)
    
    def deJsonifyDB(
        self, 
        jsonDB: dict[str, Any]
    ) -> dict[str, Any]:
        """Converts a JSON object into a dict object

        Args:
            jsonDB (dict[str, Any]): JSON

        Returns:
            dict[str, Any]: converted JSON
        """
        jsonDB['queue'] = queue.Queue()
        oldFileList = list(jsonDB['files'].values())   # snapshot
        
        newFiles = {}
        for i, fileList in enumerate(oldFileList):
            fileSet = self.listToSet(fileList)
            newFiles[i] = fileSet
        
        newTemplates = {}
        for key in jsonDB['templates']:
            newTemplates[key] = jsonDB['templates'][key]
        
        jsonDB['files'] = newFiles
        jsonDB['templates'] = newTemplates
        return jsonDB
    
    def DBIsOlderThan(
        self, 
        hours: int
    ) -> bool:
        """Checks if the database is older than a 
        set amount of hours

        Args:
            hours (int): pretty self explaining, no?

        Returns:
            bool: True if the DB is older than `hours`
        """
        path = os.path.join(self.osm.exeDir(), "user\\user.db")
        dbTime = os.path.getmtime(path)
        curTime = time.time()
        difference = curTime - dbTime
        differenceHours = round(difference/3600, 1)
        
        if differenceHours >= hours:
            return True
        else:
            return False
    
    def loadJSON(self) -> Union[dict[str, Any], None]:
        """Tries to load the saved DB in ./user/
        will return None if it's either a very recent image
        or if there's no pre-existing DB.

        Returns:
            Union[dict[str, Any], None]: Converted JSON to dict
        """
        try:
            with open(f"{self.osm.exeDir()}\\user\\user.db", "rb") as db:
                if self.DBIsOlderThan(24):
                    return None
                else:
                    byte = zlib.decompress(db.read())
                    decodedDB = byte.decode()
                    jsonDB = json.loads(rf"{decodedDB}")
        
        except Exception as e:
            self.log.log.error("Couldn't find DB") #type: ignore
            return None
        return self.deJsonifyDB(jsonDB)