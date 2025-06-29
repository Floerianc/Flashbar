# FlashBar - app.py -> Controls the main parts of the Application
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

"""
Controls:

Left-Click  -> Open file instantly
Right-Click -> Open context menu for file
Esc         -> Unfocusses search bar if focussed. If not focussed, it will minimize the window
Ctrl+Enter  -> Opens the top file
Alt+Enter   -> Opens the top directory
Right-Arrow -> Switches to the next right tab.
Left-Arrow  -> Switches to the next left tab.

Filters:
type=   Filters by extension
name=   HAS to include this in the file's name
size>   Size of file must be greater than... (can interpret sizes like 200kb and 450mb instead of 20000000)
size<   Size of file must be less than...
before= File mustve been last modified before... (can interpret dates: separator = "-", supported formats: year-month-day, day-month-year and month-day-year)
after=  File mustve been last modified after...
on=     File mustve been last modified on... (exact date)
"""

import random
import platform
if platform.system() == "Linux": raise RuntimeError("This app does not run on Linux. Sorry Luke & DNA, get a real OS. 😉")
import sys
import os
import queue
import keyboard
import subprocess
import datetime
import warnings
from rich.traceback import install
install()
from PyQt5.QtCore import(
    Qt,
    QTimer,
    pyqtSignal,
    QSize,
    QThread,
    QEvent,
)
from PyQt5.QtWidgets import(
    QApplication,
    QWidget,
    QListWidgetItem,
    QListWidget,
    QMenu,
    QAction,
)
from PyQt5.QtGui import(
    QIcon,
    QContextMenuEvent,
    QKeyEvent,
    QPixmap
)
from typing import (
    Union, 
    Any,
    Dict
)
from colorama import (
    Fore,
    Back,
    Style
)
import modules.FileManager as FileManager
import modules.Logger as Logger
import modules.UserData as UserData
import modules.config as Config
import modules.utils as utils
import modules.OSM as osm
from modules.Relevancy import Relevance
from modules.menus import menus
from ui.bar import Ui_Form

class SearchBar(QWidget):
    """This is the SearchBar
    
    this application allows the user to search for any
    file on their OS.
    
    Loading every file into the program takes about 40 Seconds
    when having around 1.7 million files on their system.
    
    Blame Python for the performance, alright? I tried my best
    """
    toggleSignal = pyqtSignal()
    
    def __init__(
        self,
        form
    ) -> None:
        """Initializes the SearchBar

        Args:
            form (QApplication): Application Form
        """
        
        #####   BASE SETUP   #####
        
        self.config = Config.Config("UI", "Control")
        self.osm = osm.OSM()
        # self.osm._RunRegistry()
        
        #####   WINDOW SETUP   ######
        
        super().__init__()
        self.form = form
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint) # type: ignore  
        self.setFixedSize(1600, 384)
        
        keyboard.add_hotkey("+".join([self.config.KEY1, self.config.KEY2]), self.toggleSignal.emit) # type: ignore
        
        #####   DATABASE SETUP   ######
        
        self.dataset = {
            'hash': random.uniform(1, 2),
            'current': 0,
            'templates': {},
            'templatesReverse': {},
            'queue': queue.Queue(),
            'files': {
                "0": set()
            },
        }
        self.userData: Dict[str, Any] = {
            'bookmarks':    [],
            'recent':       [],
            'relevancy':    {}
        }
        
        self.logger = Logger.Logger(self)
        
        db = FileManager.FileDBLoader(self.logger).loadJSON()
        if db:
            self.dataset = db
            self.logger.finishedScan = True
        else:
            del db
            self.backgroundTask = FileManager.FileSpider(self.dataset, self.logger)
            self.FileQueue = FileManager.FileDBInserter(self.dataset, self.logger)
            
            self.backgroundTask.start(QThread.Priority.HighestPriority)
            self.FileQueue.start(QThread.Priority.HighPriority)
        
        data = UserData.loadData()
        if data:
            self.userData = data
        
        #####   THREAD SETTINGS   ######
        
        self.reconstructWorker = FileManager.FileSearcher(self.dataset, self.logger)
        self.fileAmountHelper = FileAmountUpdater(self)
        self.reconstructThread = QThread()
        
        self.reconstructWorker.moveToThread(self.reconstructThread)
        self.reconstructWorker.reconstruct.connect(self.filesFromPaths)
        
        self.reconstructThread.start(QThread.Priority.NormalPriority)
        self.fileAmountHelper.start(QThread.Priority.LowestPriority)
        self.logger.start(QThread.Priority.LowestPriority)
        
        self.toggleSignal.connect(self.toggleVisibility) # type: ignore
        
        #####   UI    ######
        
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.textEdit.textChanged.connect(self.inputManager)
        
        self.ui.searchResults.itemClicked.connect(self.openFile)
        self.ui.searchResults.itemEntered.connect(self.displayPreview)
        
        self.ui.bookmarks.itemClicked.connect(self.openFile)
        self.ui.bookmarks.itemEntered.connect(self.displayPreview)
        
        self.ui.recentFiles.itemClicked.connect(self.openFile)
        self.ui.recentFiles.itemEntered.connect(self.displayPreview)
        
        self.ui.tabs.currentChanged.connect(self.tabChangeEvent)
        self.ui.tabs.installEventFilter(self)
        
        #####   TIMERS   ######
        
        self.fadeTimer = QTimer()
        self.debounceTimer = QTimer()
        
        self.fadeTimer.setInterval(self.config.FADE_TIMER)
        self.debounceTimer.setSingleShot(True)
        self.debounceTimer.setInterval(self.config.DEBOUNCE)
        self.debounceTimer.timeout.connect(self._emit_checkPaths)
        
        self.setupUi()
        self.fadeIn()
    
    @property
    def files(self) -> int:
        """Returns amount of files

        Returns:
            int: Amount of files
        """
        return sum(len(files) for files in list(self.dataset['files'].values()))
    
    @property
    def templates(self) -> int:
        """Returns amount of templates

        Returns:
            int: amount of templates
        """
        return len(self.dataset['templates'])
    
    def setupUi(self) -> None:
        """Sets a few settings and connections for the UI widgets
        """
        with open(f"{self.osm.exeDir()}\\ui\\style.css", "r") as css:
            self.UIStyle = css.read()
        
        self.ui.searchResults.setMouseTracking(True)
        self.ui.searchResults.setIconSize(QSize(self.config.ICON_WIDTH, self.config.ICON_HEIGHT))
        self.ui.searchResults.installEventFilter(self)
        
        self.ui.bookmarks.setMouseTracking(True)
        self.ui.bookmarks.setIconSize(QSize(self.config.ICON_WIDTH, self.config.ICON_HEIGHT))
        self.ui.bookmarks.installEventFilter(self)
        
        self.ui.recentFiles.setMouseTracking(True)
        self.ui.recentFiles.setIconSize(QSize(self.config.ICON_WIDTH, self.config.ICON_HEIGHT))
        self.ui.recentFiles.installEventFilter(self)
        
        self.ui.relevantFiles.setMouseTracking(True)
        self.ui.relevantFiles.setIconSize(QSize(self.config.ICON_WIDTH, self.config.ICON_HEIGHT))
        self.ui.relevantFiles.installEventFilter(self)
        
        self.setStyleSheet(self.UIStyle)
    
    def tabChangeEvent(self) -> None:
        """Calls a function for the next tab to initialize items and shit
        """
        tab = self.ui.tabs.currentIndex()
        if tab == 1:
            self.refreshBookmarks()
        elif tab == 2:
            self.refreshRecent()
        elif tab == 3:
            self.refreshRelevance()
        else:
            warnings.warn(f"{Fore.LIGHTRED_EX}No function for tab index '{tab}' found.{Fore.RESET}")
    
    def rebuildPath(
        self, 
        data: Union[tuple[str, str], str],
        strict: bool = True
    ) -> str:
        """Rebuilds paths if the given string is not a path but rather a display-name.
        
        There are multiple formats that can be transformed into a real path.

        Args:
            data (Union[tuple[str, str], str]): Can be for example ("1293", "hello.txt")
            strict (bool, optional): If strict it automatically raises error if format can't be found. Defaults to True.

        Raises:
            NotImplementedError: If format is not supported yet it will raise an error.
            TypeError: If type is not supported

        Returns:
            str: Full path to file
        """
        if type(data) is tuple:
            template = data[0]
            filename = data[1]
            path = self.dataset['templates'][template]
        elif type(data) is str:
            if "(" in data:
                split = data.split(" ")
                filename = split[0]
                path = " ".join(split[1:len(split)])
                path = path.strip("()")
            else:
                if strict:
                    raise NotImplementedError("Couldn't find appropriate path-rebuilding.")
                else:
                    return data
        else:
            raise TypeError("Type not supported by rebuildPath()\tSupported types:\ttuple\tstr")
        
        return os.path.join(path, filename)
    
    def setRelevance(
        self, 
        path: str, 
        saveRelevance: bool = False
    ) -> None:
        """Updates the relevance of a file.

        Args:
            path (str): Full path to the file
            saveRelevance (bool, optional): If the function should save it in the userData dict. Defaults to False.
        """
        if not path in self.userData['relevancy']:
            obj = Relevance(path)
            self.userData['relevancy'][path] = obj
        else:
            obj: Relevance = self.userData['relevancy'][path]
            now = datetime.datetime.today()
            obj.clicks.append(now)
        
        if saveRelevance:
            UserData.saveData(self.userData)
    
    def getRelevance(
        self, 
        path: str
    ) -> int:
        """Returns the relevance of a file's path

        Args:
            path (str): Full path to the file

        Returns:
            int: Relevance score
        """
        try:
            obj: Relevance = self.userData['relevancy'][path]
            return obj.relevanceScore
        except KeyError:
            warnings.warn(
                (
                    f"There's {Fore.LIGHTRED_EX}no Relevance object{Style.RESET_ALL}"
                    f" for path {Fore.LIGHTBLUE_EX}'{path}'{Style.RESET_ALL} yet.\n"
                    f"It was either {Fore.LIGHTRED_EX}never initialized {Style.RESET_ALL} or {Fore.LIGHTRED_EX}it's the wrong type{Style.RESET_ALL}"
                )
            )
            return -1
    
    def sortRelevance(self) -> list[Relevance]:
        """Sorts all the files saved in the relevance dictionary 
        by their relevance score.

        Returns:
            list[Relevance]: Sorted list of 'Relevance' objects.
        """
        try:
            relevances: dict[str, Relevance] = self.userData['relevancy']
            l = list(relevances.values())
            l.sort(key=lambda r: r.relevanceScore, reverse=True)
            return l
        except:
            warnings.warn(
                (
                    f"Sorting by relevance {Fore.LIGHTRED_EX}failed{Style.RESET_ALL}, "
                    f"possibly due to a {Fore.LIGHTRED_EX}TypeError{Style.RESET_ALL}. "
                    f"Try debugging function instead.\n{Fore.LIGHTGREEN_EX}Returning empty list.{Style.RESET_ALL}"
                )
            )
            return []
    
    def refreshRelevance(self) -> None:
        """Refreshes the ListWidget with the most relevant files.
        """
        self.ui.relevantFiles.clear()
        
        sortedRelevance = self.sortRelevance()
        for relevance in sortedRelevance:
            self.addFileItem(relevance.path, self.ui.relevantFiles)
    
    def addToRecent(
        self, 
        path: str, 
        saveRecent: bool = False
    ) -> None:
        """Adds the file to the most recently opened files.

        Args:
            path (str): Full path to the file
            saveRecent (bool, optional): If it should save the file to the userData dict. Defaults to False.
        """
        if not type(path) is str:
            warnings.warn(f"'path' {path} is {Fore.RED}not{Style.RESET_ALL} a string. Might cause weird behaviour.")
        
        if len(self.userData['recent']) >= 20:
            expired = self.userData['recent'].pop()
            del expired
        
        if path in self.userData['recent']:
            self.userData['recent'].remove(path)
        self.userData['recent'].insert(0, path)
        
        if saveRecent:
            UserData.saveData(self.userData)
    
    def refreshRecent(self) -> None:
        """Refreshes ListWidget with the most recently opened files.
        """
        self.ui.recentFiles.clear()
        
        recents = self.userData['recent']
        if recents:
            for recent in recents:
                if os.path.exists(recent):
                    self.addFileItem(recent, self.ui.recentFiles)
                else:
                    warnings.warn(f"File '{recent}' does {Fore.LIGHTRED_EX}not exist{Style.RESET_ALL} anymore: {Fore.LIGHTGREEN_EX}skipping file.{Style.RESET_ALL}")
                    continue
        else:
            warnings.warn(f"Recent files list does {Fore.LIGHTRED_EX}not exist or is empty.{Style.RESET_ALL}")
            return
    
    def addToBookmarks(
        self, 
        item: QListWidgetItem, 
        saveBookmarks: bool = False
    ) -> None:
        """Adds the file to the bookmarked files.

        Args:
            item (QListWidgetItem): Selected item
            saveBookmarks (bool, optional): If it should be saved to the bookmarks. Defaults to False.
        """
        fullPath = self.rebuildPath(item.text())
        if fullPath in self.userData['bookmarks']:
            pass
        else:
            self.userData['bookmarks'].append(fullPath)
        
        if saveBookmarks:
            UserData.saveData(self.userData)
        else:
            return
    
    def removeFromBookmarks(
        self, 
        item: QListWidgetItem, 
        saveBookmarks: bool = False
    ) -> None:
        """Removes file from bookmarked files.

        Args:
            item (QListWidgetItem): Selected item
            saveBookmarks (bool, optional): If it should be saved to the bookmarks. Defaults to False.
        """
        fullPath = self.rebuildPath(item.text())
        self.userData['bookmarks'].remove(fullPath)
        
        if saveBookmarks:
            UserData.saveData(self.userData)
        else:
            pass
        self.refreshBookmarks()
    
    def refreshBookmarks(self) -> None:
        """Refreshes ListWidget with all bookmarked files.
        """
        self.ui.bookmarks.clear()
        
        bookmarks = self.userData['bookmarks']
        if bookmarks:
            for path in bookmarks:
                if os.path.exists(path):
                    self.addFileItem(path, self.ui.bookmarks)
                else:
                    warnings.warn(f"File '{path}' does {Fore.LIGHTRED_EX}not exist{Style.RESET_ALL} anymore: {Fore.LIGHTGREEN_EX}skipping file.{Style.RESET_ALL} (Bookmarks)")
                    continue
        else:
            warnings.warn(f"Bookmarks list does {Fore.LIGHTRED_EX}not exist or is empty.{Style.RESET_ALL}")
            return
    
    def addFileItem(
        self, 
        path: str, 
        listWidget: QListWidget
    ) -> None:
        """Adds item for file to a certain ListWidget.
        
        This includes:
        - A proper display name
        - A little icon to show file extension
        - A tool-tip which contains:
            - File extension
            - Filename
            - File size
            - File relevance

        Args:
            path (str): Full path to file
            listWidget (QListWidget): ListWidget the item should be added to.
        """
        if not os.path.exists(path):
            warnings.warn(f"File '{path}' does {Fore.LIGHTRED_EX}not exist{Style.RESET_ALL}. Can't add file item.")
            return
        
        template, filename = self.osm.splitPath(path)
        displayText = filename + f" ({template})"
        item = QListWidgetItem(displayText)
        
        icon = QIcon(utils.getIcon(path))
        item.setIcon(icon)
        item.setToolTip(self.getToolTip(path))
        
        listWidget.addItem(item)
    
    def openFile(
        self, 
        item: Union[QListWidgetItem, None] = None,
        addToData: bool = True
    ) -> None:
        """Opens file of given item or currently selected item and saves it to
        userData dict if `addToData = True`

        Args:
            item (Union[QListWidgetItem, None], optional): Listwidget item. Defaults to None.
            addToData (bool): If the file should be added to the userData. Defaults to True.
        """
        if not item:
            item = self.ui.searchResults.currentItem()
        
        if item is not None:
            path = self.rebuildPath(item.text())
            try:
                if platform.system() == 'Windows':
                    os.startfile(path)
                elif platform.system() == 'Linux':
                    subprocess.run(['xdg-open', path], check=False)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', path], check=False)
            except Exception as e:
                self.logger.log.error(f"Failed to open {path}: {e}")
            self.fadeOut()
        else:
            return
        
        if addToData:
            self.addToRecent(path)
            self.setRelevance(path)
            UserData.saveData(self.userData)
        else:
            pass
    
    def openDirectory(self, item: Union[QListWidgetItem, None] = None, addToData: bool = True) -> None:
        """Opens the directory with the path of the current
        item in the listWidget or a given item and saves it to
        userData dict if `addToData = True`

        Args:
            item (Union[QListWidgetItem, None], optional): Listwidget item. Defaults to None.
            addToData (bool): If the file should be added to the userData. Defaults to True.
        """
        if not item:
            item = self.ui.searchResults.currentItem()
        
        if item is not None:
            path = self.rebuildPath(item.text())
            folder, filename = self.osm.splitPath(path)
            del filename
            try:
                subprocess.run(['explorer', folder], check=False)
            except subprocess.CalledProcessError as e:
                print(e)
            self.fadeOut()
        else:
            return
        
        if addToData:
            self.addToRecent(path)
            self.setRelevance(path)
            UserData.saveData(self.userData)
        else:
            pass
    
    def copyPath(
        self, 
        path: str
    ) -> None:
        """Inserts path into the clipboard

        Args:
            path (str): path
        """
        clip = QApplication.clipboard()
        if clip:
            clip.setText(path)
        else:
            return
        self.fadeOut()
    
    def switchTab(
        self, 
        change: int
    ) -> None:
        """Switches the tab if you use your arrow-keys (usually)
        It takes the integer `change` and adds it to your currently
        selected tab index.
        
        If it exceeds the maximum index it will just start over again.

        Args:
            change (int): How many tabs you cycle through (2 --> 2 in right direction, -2 --> 2 in left direction)
        """
        tabN = self.ui.tabs.currentIndex() + change
        tabs = self.ui.tabs.count() - 1
        if tabN > tabs:
            tabN = (tabN % tabs) - 1
        elif tabN < 0:
            tabN = tabs
        
        self.ui.tabs.setCurrentIndex(tabN)
    
    def keyPressEvent( # type: ignore
        self, 
        event: QKeyEvent
    ) -> None:
        """Calls certain functions and methods depending on
        pressed hotkeys.
        
        - Esc           -> Unfocusses Searchbar -> Window fades out
        - Ctrl + Enter  -> Open top file
        - Alt  + Enter  -> Open top directory
        - Arrow-Right   -> Switch to next tab
        - Arrow-Left   -> Switch to next left tab

        Args:
            event (QKeyEvent): Keyboard event
        """
        if event.key() == Qt.Key.Key_Escape:
            if self.ui.textEdit.hasFocus():
                self.ui.textEdit.clearFocus()
            else:
                self.fadeOut()
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Return:
            try:
                topItem = self.ui.searchResults.item(0)
                self.openFile(topItem)
            except:
                return
        elif event.modifiers() == Qt.KeyboardModifier.AltModifier and event.key() == Qt.Key.Key_Return:
            try:
                topItem = self.ui.searchResults.item(0)
                self.openDirectory(topItem)
            except:
                return
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Backspace:
            self.ui.searchResults.clear()
        elif event.key() == Qt.Key.Key_Right:
            self.switchTab(1)
        elif event.key() == Qt.Key.Key_Left:
            self.switchTab(-1)
    
    def eventFilter( # type: ignore
        self, 
        source: QListWidget, 
        event: QContextMenuEvent
    ) -> bool:
        """Handles right-clicking in this Window
        
        If you right-click on the listWidget it will open
        a context menu where you can open the file, directory and
        copy the path

        Args:
            source (QListWidget): The listWidget you clicked on
            event (QContextMenuEvent): Click event

        Returns:
            bool: True if clicked on listWidget
        """
        # eventfilter does not support left-click so it's as a connection in the __init__
        if event.type() == QEvent.Type.ContextMenu and source is self.ui.searchResults:
            menus.Templates.searchResultsMenu(menus.Templates(), self, event)
        elif event.type() == QEvent.Type.ContextMenu and source is self.ui.bookmarks:
            menus.Templates.bookmarksMenu(menus.Templates(), self, event)
        elif event.type() == QEvent.Type.ContextMenu and source is self.ui.recentFiles:
            menus.Templates.recentMenu(menus.Templates(), self, event)
        return super().eventFilter(source, event)
    
    def fadeIn(self) -> None:
        """Lets the window quickly fade in
        
        It does that by utilizing the self.fadeTimer
        and _nextFadeStep() function to change the
        windows opacity with each time the timer times out.
        """
        self.setWindowOpacity(0.0)
        try:
            self.fadeTimer.timeout.disconnect()
        except:
            pass # no prior connections
        
        self.fadeTimer.timeout.connect(lambda: self._nextFadeStep(0.2))
        self.fadeTimer.start()
    
    def fadeOut(self) -> None:
        """Lets the window quickly fade out
        
        It does that by utilizing the self.fadeTimer
        and _nextFadeStep() function to change the
        windows opacity with each time the timer times out.
        """
        self.setWindowOpacity(1.0)
        try:
            self.fadeTimer.timeout.disconnect()
        except:
            pass # no prior connections
        
        self.fadeTimer.timeout.connect(lambda: self._nextFadeStep(-0.2))
        self.fadeTimer.start()
    
    def _emit_checkPaths(self) -> None:
        """Checks for possible paths the user is looking for
        if the input is longer than 2 characters
        """
        text = self.ui.textEdit.toPlainText()
        
        
        self.ui.searchResults.clear()
        self.ui.searchResults.addItem("Loading...")
        self.reconstructWorker.checkPaths.emit(text)
    
    def inputManager(self) -> None:
        """Starts the debounce timer, mostly to reduce CPU usage
        """
        self.debounceTimer.start()
    
    def filesFromPaths(
        self, 
        paths: list
    ) -> None:
        """Adds each file from the list of paths to the listWidget
        
        First, it clears the listWidget to ensure the items added to
        the listWidget are only the ones for the corresponding SearchBar input
        
        it creates a QListWidgetItem and a QIcon and then adds
        them to the listWidget

        Args:
            paths (list): _description_
        """
        self.ui.searchResults.clear()
        
        if len(paths) <= 0:
            self.ui.searchResults.addItem("No results found.")
        else:
            for path in paths:
                self.addFileItem(path, self.ui.searchResults)
    
    def formattedSize(
        self, 
        fileSize: Union[int, float]
    ) -> str:
        """Formats the size of the file
        
        Supported are bytes (B), kilobytes (KB), megabytes (MB),
        gigabytes (GB) and terrabytes (TB)
        
        It takes the amount of bytes of a file as input
        
        and returns the string of the formatted file size.

        Args:
            fileSize (int): amount of bytes

        Returns:
            str: formatted file size
        """
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
        index = 0
        while (fileSize / 1024 > 1):
            index += 1
            fileSize /= 1024
        return f"{round(fileSize, 3)}{suffixes[index]}"
    
    def displayPreview(
        self, 
        item: QListWidgetItem
    ) -> None:
        """Displays a preview of an image if the extension is in
        the list of image extensions

        Args:
            item (QListWidgetItem): _description_
        """
        path = self.rebuildPath(item.text(), False)
        if path.endswith(tuple(utils.imageExts)):
            pixmap = QPixmap(path).scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio)
            self.ui.previewLabel.setPixmap(pixmap)
        else:
            self.ui.previewLabel.setPixmap(QPixmap())
    
    def getToolTip(
        self, 
        path: str
    ) -> str:
        """Creates the tool-tip for a listWidget's item
        and its corresponding file

        Args:
            path (str): path to the file

        Returns:
            str: tool-tip string
        """
        extSplit = path.split(".")
        if len(extSplit) == 1:
            extension = "No extension given."
        else:
            extension = extSplit[-1]
        
        template, name = self.osm.splitPath(path)
        del template
        fileSize = self.formattedSize(os.path.getsize(path))
        relevance = self.getRelevance(path)
        return f"Extension:\t{extension}\nFilename:\t{name}\nFile size:\t{fileSize}\nRelevance:\t{relevance}"
    
    def _nextFadeStep(
        self, 
        change: float
    ) -> None:
        """Changes the alpha and potentially stops the fadeTimer
        with a given float number to manipulate the windows opacity

        Args:
            change (float): number to change the opacity (between -1 and 1)
        """
        alpha = self.windowOpacity() + change
        self.setWindowOpacity(alpha)
        
        if change > 0:
            if alpha >= 1.0:
                self.fadeTimer.stop()
                self.show()
        else:
            if alpha <= 0.0:
                self.fadeTimer.stop()
                self.hide()
    
    def toggleVisibility(self) -> None:
        """Toggles the visibility of the window
        """
        self.ui.textEdit.clear()
        self.ui.searchResults.clear()
        self.ui.previewLabel.clear()
        
        if self.isVisible():
            self.logger.log.debug("Hiding window")
            self.fadeOut()
            self.ui.textEdit.clearFocus()
        else:
            self.logger.log.debug("Showing window")
            self.fadeIn()
            self.ui.textEdit.setFocus()
    
    def displayFileAmount(self) -> None:
        self.ui.fileLabel.setText(f"{self.files:,} Files")

class FileAmountUpdater(QThread):
    """Updates the amount of files in a seperate thread

    **Inherits from QThread**
    """
    def __init__(
        self, 
        parent: SearchBar
    ) -> None:
        super().__init__(parent)
        self.parentObject = parent
        self.running = True
    
    def run(self):
        while self.running:
            if self.parentObject.isVisible():
                self.parentObject.displayFileAmount()
            else:
                self.msleep(500)
            self.msleep(50)  # update every 0.05 seconds
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    form = QApplication(sys.argv)
    ui = SearchBar(form)
    sys.exit(form.exec_())

# Current benchmarks on my own PC:
#   First 10 Seconds:               910,000 Files
#   1,000,000 Files:                ~13 Seconds
#   Full scan:                      32 Seconds (1,642,000 Files)
#   Average Speed:                  51.200 Files/s

#       Add documentation                                                                   (IN PROGRESS)
#       Code clean-up                                                                       (IN PROGRESS)
#       Add dimmed background?                                                              (CANCELLED)
#       More efficiency?            (current speed: 1,642,000 Files in 34 Seconds.)         (DONE)
            # Reverse hashmaps literally saved my life (thanks GPT, I was so close to figuring it out by myself lol)
            # Another idea: Individual threads for each drive with reverse look-up hashmaps i think that goes hard af
            # so we have:
                # main thread   -> GUI                                                      (DONE)
                # Manager1      -> walking through the OS, putting files into the queue     (DONE)
                #                   -> for each drive it creates another thread
                # Manager2      -> adding files to the database                             (DONE)
                # Manager3      -> reconstructing paths                                     (DONE)
                # Helper1       -> Displays fileAmount repeatedly                           (DONE)
                # Split up files into multiple sublists [each list has max. 50,000 files]   (DONE)
#       Option to open file/directory                                                       (DONE)
#       Configs                                                                             (DONE)
#       Improve modules structure (object oriented?)                                        (DONE)

# Coming up Features
#       - Autostart                                                                         (DONE)
#       - Keyboard Shortcuts                                                                (DONE)
#       - Search Filters (type=md, size>1mb, size<3mb)                                      (DONE)
#       - Debounce timer                                                                    (DONE)
#       - Right-click Context menu instead                                                  (DONE)
#       - Better UI/UX (Accent Colors or smth idek)                                         (DONE)
#       - Bookmark files                                                                    (DONE)
#       - Save and Load drives                                                              (DONE)
#           - Find way to convert JSON to dict with sets and queues and all                 (DONE)
#           - FIND A WAY TO NOT MAKE IT LOAD 2 DIFFERENT DICTIONARIES HELP???               (DONE)
#           - CURRENT PROBLEM: JSON SAVES ANY KEY AS A STRING NOT INT??                     (DONE)
#       - Convert drive.py to osm.py                                                        (DONE)
#       - Compress JSON obj with zlib (8.13x smaller)                                       (DONE)
#       - IMG Preview                                                                       (DONE)
#       - Refresh DB after 1 Day                                                            (DONE)
#       - Convert keys in dictionaries to integers for Runtime                              (CANCELLED)
#       - Save Recent and Bookmarks in same file.                                           (DONE)
#       - Create dataclasses for a few things                                               (CANCELLED)
#       - Sort by relevancy                                                                 (DONE)
#       - Create more error handling like warnings for console and shit                     (IN PROGRESS)
#       - Add colored warnings                                                              (IN PROGRESS)
#       - Make everything controlled by keyboard (switch tabs...)                           (DONE)
#       - Change Settings within the program                                                (IN PROGRESS)
#       - Put most systems into seperate files so it's easier to change stuffs              (DONE)
#           - Menus are now in seperate file lol                                            (DONE)
#       - More settings                                                                     (IN PROGRESS)
#       NEXT MAJOR UPDATE:  
#           - Show directories too, not just files
#           - Show overlap and relevancy of files
#           - Lite Mode: Instant look-up
#           - Also do a look-up thing for the filenames?    <-- I have no clue what I meant with this

# 29.06.25:     2519 lines lol