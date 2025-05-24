# FlashBar - modules/FileManager.py -> Handles all the database and OS logic
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

import os
import zlib
import time
import json
import queue
import config as Config
from threading import Lock
from PyQt5.QtCore import(
    QThread,
    pyqtSignal,
    pyqtSlot
)
from typing import(
    TYPE_CHECKING,
    Union,
    Any,
)
from rapidfuzz import fuzz
from modules.Logger import Logger
import modules.osm as osm

if TYPE_CHECKING:
    from app import SearchBar


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
        
        with open("user\\user.db", "wb") as dbf:
            jsonData = json.dumps(db)
            compressedBytes = zlib.compress(jsonData.encode(), 9)
            dbf.write(compressedBytes)
    
    def run(self) -> None:
        """This is the main part of the Thread
        
        It iterates through every folder and file and
        adds them to a queue. Then seperates them with
        templates and file names
        """
        startTime = time.time()
        
        drives = self.osm.drives
        buffer = []
        BATCH_SIZE = self.config.BATCH_SIZE
        
        for drive in drives:
            for root, _, files in os.walk(drive):
                try:
                    for file in files:
                        buffer.append(os.path.join(root, file))
                        if len(buffer) >= BATCH_SIZE:
                            self.queueFiles(buffer)
                            buffer = []
                except (PermissionError, OSError) as e:
                    self.log.log.info(f"Skipped: {root} ({e})")
                    continue
        endTime = time.time()
        self.log.log.debug("Finished full-scan in %d seconds.", int(endTime-startTime))
        self.queueFiles(buffer)
        self.saveJSON()

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
            newTemplates[int(key)] = jsonDB['templates'][key]
        
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
        path = os.path.join(os.path.curdir, os.path.relpath("user\\user.db"))
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
            with open("user\\user.db", "rb") as db:
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
            if not self.data['queue'].empty():
                files = self.data['queue'].get()
                self.scanFiles(files)
            else:
                time.sleep(0.1)

class FileSearcher(QThread):
    """Searches for the files from the users input

    **Inherits from QThread**
    """
    checkPaths = pyqtSignal(str)
    reconstruct = pyqtSignal(list)
    
    def __init__(
        self, 
        windowData: dict[str, Any]
    ) -> None:
        """Initializes the FileSearcher

        Args:
            windowData (Union[dict[str, Any], &#39;SearchBar&#39;]): Window data
        """
        super().__init__()
        self.data = windowData
        self.config = Config.Config('Search')
        self.MIN_MATCH = self.config.MIN_MATCH
        self.checkPaths.connect(self.search)
    
    def getSortedFiles(
        self, 
        filename: str
    ) -> list[tuple[int, str]]:
        """Checks for matches in the file names and the users input.
        
        Depending on how much they overlap we get a score calculated by fuzz.
        If the score exceeds the minimum match requirement we add it to the list.

        Args:
            filename (str): File name

        Returns:
            list[tuple[int, str]]: List of possible files the user could be looking for in decending order
        """
        possibleFiles = []
        
        for fileList in list(self.data['files'].values()):
            for tpl in fileList:
                score = fuzz.ratio(tpl[1], filename)
                if score >= self.MIN_MATCH:
                    possibleFiles.append((score, tpl))
        
        possibleFiles.sort(reverse=True, key=lambda x: x[0])
        return possibleFiles
    
    def reconstructPaths(
        self, 
        filename: str
    ) -> list[str]:
        """Reconstructs the paths of the possible files
        
        It does that by checking the ID of the tuple and then
        adding the corresponding template and name together

        Args:
            filename (str): File name the user is looking for

        Returns:
            list[str]: Returns a list of full paths to the files
        """
        paths = []
        l = self.getSortedFiles(filename)
        
        for i in range(self.config.MAX_RESULTS) if len(l) >= self.config.MAX_RESULTS else range(len(l)):
            template, name = l[i][1]
            paths.append(os.path.join(self.data['templates'][template], name))
        return paths
    
    @pyqtSlot(str)
    def search(
        self, 
        query: str
    ) -> None:
        """Lets the program try to reconstruct paths with a given file name

        Args:
            query (str): The query is the file name the user is looking for
        """
        results = self.reconstructPaths(query)
        self.reconstruct.emit(results)


if __name__ == "__main__":
    a = FileSearcher(None)              # type: ignore
    print(a.reconstructPaths("readme"))