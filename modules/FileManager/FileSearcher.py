# FlashBar - ./modules/FileManager/FileSearcher.py -> Search engine for your filesystem.
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
import math
import warnings
import pprint
from PyQt5.QtCore import(
    QThread, 
    pyqtSignal,
    pyqtSlot
)
from datetime import datetime
from rapidfuzz import fuzz
from typing import Any
import modules.config as Config
import modules.utils as utils
from modules.Logger import Logger
from modules.OSM import OSM

class SearchFilter:
    def __init__(self) -> None:
        self.osm = OSM()
    
    @property
    def date(self) -> tuple[property, property, property]:
        """Returns the current day, month and year

        Returns:
            tuple[property, property, property]: tuple of day, month and year
        """
        return (datetime.year, datetime.month, datetime.day)
    
    def interpretDate(
        self, 
        query: str, 
        separator: str = "-"
    ) -> datetime | None:
        """Tries to convert a string representing a date to a datetime object

        Args:
            query (str): The string (usually user-input) that we'll convert to a datetime object.
            separator (str, optional): The seperator between day, month and year. Defaults to "-".

        Returns:
            datetime | None: _description_
        """
        knownFormats = [
            f"%d{separator}%m{separator}%Y",  # 25-06-2025
            f"%Y{separator}%m{separator}%d",  # 2025-06-25
            f"%m{separator}%d{separator}%Y",  # 06-25-2025
        ]
        
        for dateFormat in knownFormats:
            try:
                return datetime.strptime(query, dateFormat)
            except:
                continue
        warnings.warn(f"Unable to parse query: '{query}'. Supported formats: d{separator}m{separator}Y, Y{separator}m{separator}d, m{separator}d{separator}Y")
        return None
    
    def fileDate(
        self, 
        path: str
    ) -> datetime | None:
        """Returns a datetime object for when a certain file was
        last modified if the file exists. If the file doesn't exist
        it'll return None.

        Args:
            path (str): Full path to file.

        Returns:
            datetime | None: Datetime object for when the file was last modified or None if file does not exist anymore.
        """
        if os.path.exists(path):
            fileDate = os.path.getmtime(path)
            return datetime.fromtimestamp(fileDate)
        else:
            warnings.warn(f"File doesn't exist anymore: {path}")
            return None
    
    def extensions(
        self, 
        paths: list[tuple[int, str]], 
        value: str
    ) -> list[tuple[int, str]]:
        """Filters files by a given extension they must have.

        Args:
            paths (list[tuple[int, str]]): List of many full file paths
            value (str): The extension we are looking for.

        Returns:
            list[tuple[int, str]]: Filtered list.
        """
        if not "." in value:
            value = f".{value}"
        return [(score, path) for score, path  in paths if path.endswith(value)]
    
    def size(
        self, 
        paths: list[tuple[int, str]], 
        minSize: str | None, 
        maxSize: str | None
    ) -> list[tuple[int, str]]:
        """Filters files by size

        Args:
            paths (list[tuple[int, str]]): List of full paths to files
            minSize (str | None): Minimum size of the file
            maxSize (str | None): Maximum size of the file.

        Returns:
            list[tuple[int, str]]: Filtered Files
        """
        if (minSize and maxSize) and (minSize > maxSize):
            warnings.warn("Minimum Size filter can't be greater than the maximum size filter")
            return paths
        
        minimum = utils.interpretSize(minSize) if minSize else -math.inf
        maximum = utils.interpretSize(maxSize) if maxSize else math.inf
        
        return [(score, path) for score, path in paths if self.osm.fileSize(path) > minimum and self.osm.fileSize(path) < maximum]
    
    def name(
        self, 
        paths: list[tuple[int, str]], 
        query: str
    ) -> list[tuple[int, str]]:
        """Filters files by a specific query

        Args:
            paths (list[tuple[int, str]]): List of full paths to files
            query (str): Query the file name MUST include.

        Returns:
            list[tuple[int, str]]: Filtered list
        """
        return [(score, path) for score, path in paths if query in path]
    
    def compareDates(
        self, 
        fileDate: datetime, 
        queryDate: datetime, 
        mode: str
    ) -> bool:
        """Compares the file's date and the given date by the user
        and filters the files by a given mode.

        Args:
            fileDate (datetime): Date of the file.
            queryDate (datetime): Date given by the user.
            mode (str): Either before=, on= or after=.

        Returns:
            bool: True if the mode applies to the file and False if not.
        """
        if mode == "before=":
            if fileDate < queryDate:
                return True
            else:
                return False
        elif mode == "after=":
            if fileDate > queryDate:
                return True
            else:
                return False
        elif mode == "on=":
            if fileDate.year == queryDate.year and fileDate.month == queryDate.month and fileDate.day < queryDate.day:
                return True
            else:
                return False
        else:
            warnings.warn(f"Mode does not exist: '{mode}'")
            return False
    
    def filterByDate(
        self, 
        paths: list[tuple[int, str]], 
        query: str, 
        mode: str
    ) -> list[tuple[int, str]]:
        """Filters files by a given date.

        Args:
            paths (list[tuple[int, str]]): List of full paths to files
            query (str): Date given by the user.
            mode (str): Mode given by the user.

        Returns:
            list[tuple[int, str]]: Filtered list of file paths.
        """
        filteredPaths = []
        queryDate = self.interpretDate(query)
        
        for path in paths:
            score, file = path
            del score
            fileDate = self.fileDate(file)
            
            if fileDate and queryDate:
                if self.compareDates(fileDate, queryDate, mode):
                    filteredPaths.append(path)
                else:
                    warnings.warn(f"Error: {fileDate} is not {mode} {queryDate}")
                    continue
            else:
                continue
        return filteredPaths

class FileSearcher(QThread):
    """Searches for the files from the users input

    **Inherits from QThread**
    """
    checkPaths = pyqtSignal(str)
    reconstruct = pyqtSignal(list)
    
    def __init__(
        self, 
        windowData: dict[str, Any],
        log: Logger
    ) -> None:
        """Initializes the FileSearcher

        Args:
            windowData (Union[dict[str, Any], &#39;SearchBar&#39;]): Window data
        """
        super().__init__()
        self.pp = pprint.PrettyPrinter(4)
        self.data = windowData
        self.log = log
        self.config = Config.Config('Search')
        self.MIN_MATCH = self.config.MIN_MATCH
        self.osm = OSM()
        self.filter = SearchFilter()
        self.supportedFilters = [
            'type=',
            'size>',
            'size<',
            'name=',
            'after=',
            'before=',
            'on='
        ]
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
        paths: list[tuple[int, str]]
    ) -> list[tuple[int, str]]:
        """Reconstructs the paths of the possible files
        
        It does that by checking the ID of the tuple and then
        adding the corresponding template and name together

        Args:
            filename (str): File name the user is looking for

        Returns:
            list[str]: Returns a list of full paths to the files
        """
        results = []
        
        return [(score, (os.path.join(self.data['templates'][str(template)], name))) for score, (template, name) in paths]
        for i in range(self.config.MAX_RESULTS) if len(paths) >= self.config.MAX_RESULTS else range(len(paths)):
            template, name = paths[i][1]
            try:
                results.append(os.path.join(self.data['templates'][str(template)], name))
            except Exception as e:
                self.log.log.error("Couldn't find file (%s). Template:\t %s (type: %s), name:\t %s (type: %s)", str(e), str(template), str(type(template)), str(name), str(type(name)))
        return results
    
    def isAdvancedSearch(
        self, 
        query: str
    ) -> bool:
        """Returns if the search query includes filters.

        Args:
            query (str): The user's input

        Returns:
            bool: True if includes filters. False if the query doesn't.
        """
        for param in self.supportedFilters:
            if param in query:
                return True
        return False
    
    def getFilters(
        self, 
        query: str
    ) -> dict[str, str | None]:
        """Returns all the filters in the query.

        Args:
            query (str): The user's input.

        Returns:
            dict[str, str | None]: Dictionary where the keys are the filters and the values are the value of the filters. 
            If a filter is not given, the value will automatically be None.
        """
        # readme.txt type=md size>10mb
        filters = dict.fromkeys(self.supportedFilters, None)
        split = query.split()
        for sfilter in self.supportedFilters:
            for word in split:
                if sfilter in word:
                    key = sfilter
                    value = word.removeprefix(key)
                    filters[key] = value
        self.pp.pprint(filters)
        return filters
    
    def applyAdvancedFilters(
        self, 
        paths: list[tuple[int, str]], 
        query: str
    ) -> list[tuple[int, str]]:
        """Applies all the advanced filters in the user's query

        Args:
            paths (list[tuple[int, str]]): List of full paths to files.
            query (str): The user's input.

        Returns:
            list[tuple[int, str]]: Filtered list of full paths to files.
        """
        filters = self.getFilters(query)
        
        # If you use one filter multiple times the last one will overwrite
        # any previous ones.
        
        if filters['type=']:
            paths = self.filter.extensions(paths, filters['type='])
        if filters['size>'] or filters['size<']:
            paths = self.filter.size(paths, filters['size>'], filters['size<'])
        if filters['name=']:
            paths = self.filter.name(paths, filters['name='])
        if filters['after=']:
            paths = self.filter.filterByDate(paths, filters['after='], "after=")
        if filters['before=']:
            paths = self.filter.filterByDate(paths, filters['before='], "before=")
        if filters['on=']:
            paths = self.filter.filterByDate(paths, filters['on='], "on=")
        return paths
    
    def filterQuery(
        self, 
        query: str
    ) -> str:
        """Removes all filters from the query and just leaves the raw search query.

        Args:
            query (str): The user's input.

        Returns:
            str: The raw query without all the filters.
        """
        split = query.split()
        allowed = split.copy()
        for sfilter in self.supportedFilters:
            for word in split:
                if sfilter in word:
                    allowed.remove(word)
                    continue
        return " ".join(allowed)
    
    def returnBest(
        self, 
        paths: list[tuple[int, str]], 
        amount: int
    ) -> list[str]:
        """Returns the files that fit the query the best.

        Args:
            paths (list[tuple[int, str]]): List of full paths to files.
            amount (int): Amount of files returned. (amount=5 --> top 5 files)

        Returns:
            list[str]: _description_
        """
        amount = amount if len(paths) >= self.config.MAX_RESULTS else len(paths)
        return [paths[i][1] for i in range(amount)]
    
    @pyqtSlot(str)
    def search(
        self, 
        query: str
    ) -> None:
        """Lets the program try to reconstruct paths with a given file name

        Args:
            query (str): The query is the file name the user is looking for
        """
        advanced: bool | None = None
        if self.isAdvancedSearch(query):
            filteredQuery = self.filterQuery(query)
            advanced = True
        else:
            filteredQuery = query
            advanced = False
        
        sortedPaths = self.getSortedFiles(filteredQuery)
        results = self.reconstructPaths(sortedPaths)
        if advanced:
            results = self.applyAdvancedFilters(results, query)
        finalResults = self.returnBest(results, self.config.MAX_RESULTS)
        
        self.pp.pprint(finalResults)
        self.reconstruct.emit(finalResults)