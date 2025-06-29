# FlashBar - ./modules/FileManager/FileDBInserter.py -> Inserts stuff into the DB
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
from PyQt5.QtCore import QThread
from typing import Any
import modules.config as Config
import modules.OSM as osm
from modules.Logger import Logger

class FileDBInserter(QThread):
    """This class handles most of the work with the dataset
    
    It scans files for it's template (path) and file name and
    then sorts them depending on different factors.
    
    For more information on the whole process, check the
    code and doc-strings of each function-

    **Inherits from QThread**
    """
    def __init__(
        self, 
        windowData: dict[str, Any],
        log: Logger
    ) -> None:
        
        super().__init__()
        self.config = Config.Config('DB')
        self.log = log
        self.osm = osm.OSM()
        self.data = windowData
        self.CHUNK_SIZE = self.config.CHUNK_SIZE
    
    def scanFiles(
        self, 
        files: list
    ) -> None:
        """This scans each file in a list of files

        It does this by first splitting up the full path of the file
        into the path and the raw file name.
        
        Then it looks if the path already exists in the database and if
        it does, it will just be added to the file lists with its given ID to the corresponding path
        
        If the template (path) doesn't exist in the dataset it will save
        the template in the templates dictionary with its own ID so other files
        from that directory can be given that ID so you don't have to save
        paths twice.

        Args:
            files (list): list of files
        """
        for file in files:
            template, filename = self.osm.splitPath(file)
            
            if template not in self.data["templatesReverse"]:
                index = len(self.data["templates"])
                self.data["templates"][str(index)] = template
                self.data["templatesReverse"][template] = index
            else:
                index = self.data["templatesReverse"][template]
            
            fileKey = self.data['current']
            if len(self.data['files'][str(fileKey)]) >= self.CHUNK_SIZE:
                fileKey = fileKey + 1
                self.data['files'][str(fileKey)] = set()
                self.data['current'] = fileKey
                self.log.log.info("Reached file batch limit. Initializing new list. file key = %d", fileKey)
            
            self.data['files'][str(fileKey)].add((index, filename))
    
    def run(self) -> None:
        """The main part of the Thread
        
        It checks if the queue is empty and if it isn't it will
        scan the files in the queue.
        """
        while True:
            files = []
            
            if self.data['queue'].empty():
                if not files:
                    time.sleep(0.1)
                else:
                    self.scanFiles(files)
            else:
                files = self.data['queue'].get()
                self.scanFiles(files)
            # print(f"Inserted {len(files)} Files.")