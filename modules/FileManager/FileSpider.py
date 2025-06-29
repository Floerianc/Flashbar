# FlashBar - ./modules/FileManager/FileSpider.py -> Scans your logical hard-drives for all the files.
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
import threading
import json
import zlib
import os
from PyQt5.QtCore import QThread
from typing import Any
import modules.config as Config
import modules.OSM as osm
from modules.Logger import Logger

class FileSpider(QThread):
    """The FileSpider is the part of the program responsible
    for finding all the files in the OS.
    
    This is probably also the part of the system which has gone through
    the most changes of any part of this program.
    
    The biggest breakthrough was when GPT told me to just use a reverse-lookup dictionary lol 

    **Inherites from QThread**
    """
    def __init__(
        self, 
        windowData: dict[str, Any],
        log: Logger
    ) -> None:
        """Initializes the FileSpider by loading it's config and windowData

        Args:
            windowData (dict[str, Any]): data of all the files and templates stored
        """
        super().__init__()
        self.config = Config.Config('Spider')
        self.log = log
        self.osm = osm.OSM()
        self.data = windowData
        self.buffer = []
        self.BATCH_SIZE = self.config.BATCH_SIZE
    
    def queueFiles(
        self, 
        filePaths: list[str]
    ) -> None:
        """Queues a list of files

        Args:
            filePaths (list[str]): list of full paths of files
        """
        self.data['queue'].put(filePaths)
    
    def jsonifyDB(self) -> dict[str, Any]:
        """Turns the dictionary object into a object
        which can be dumped into a JSON without problems

        Returns:
            dict[str, Any]: modified DB
        """
        db = self.data.copy()
        del db['queue']
        
        for i, fileSet in enumerate(db['files'].values()):
            fileList = list(fileSet)
            db['files'][str(i)] = fileList
        
        return db
    
    def saveJSON(self) -> None:
        """Saves the whole data in a JSON. Using zlib compression
        """
        time.sleep(1)
        db = self.jsonifyDB()
        
        with open(f"{self.osm.exeDir()}\\user\\user.db", "wb") as dbf:
            jsonData = json.dumps(db)
            compressedBytes = zlib.compress(jsonData.encode(), 9)
            dbf.write(compressedBytes)
    
    def runThroughDrive(
        self, 
        drive: str
    ) -> None:
        """Runs through the entire drive's files and adds them to the DB.
        
        Check the called methods for more info

        Args:
            drive (str): Drive name (e.g. "C:\\")
        """
        buffer = self.buffer
        BATCH_SIZE = self.BATCH_SIZE
        
        for root, _, files in os.walk(drive):
            try:
                for file in files:
                    buffer.append(os.path.join(root, file))
                    if len(buffer) >= BATCH_SIZE:
                        self.data['queue'].put(buffer)
                        buffer = []
            except (PermissionError, OSError) as e:
                self.log.log.info(f"Skipped: {root} ({e})")
                continue
    
    def run(self) -> None:
        """This is the main part of the Thread
        
        It iterates through every folder and file and
        adds them to a queue. Then seperates them with
        templates and file names
        """
        startTime = time.time()
        drives = self.osm.drives
        
        for drive in drives:
            if "C" not in drive:
                newT = threading.Thread(target=self.runThroughDrive, args=[drive,])
                newT.start()
        self.runThroughDrive(drives[0])
        endTime = time.time()
        self.log.log.debug("Finished full-scan in %d seconds.", int(endTime-startTime))
        self.queueFiles(self.buffer)
        self.saveJSON()