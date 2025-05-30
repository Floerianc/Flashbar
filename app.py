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

import random
import platform
if platform.system() == "Linux": raise RuntimeError("This app does not run on Linux. Sorry Luke & DNA, get a real OS. 😉")
import sys
import os
import queue
import keyboard
import subprocess
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
    Any
)
import modules.FileManager as FileManager
import modules.Logger as Logger
import config as Config
import utils
import modules.osm as osm
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
        super().__init__()
        self.config = Config.Config("UI", "Control")
        self.osm = osm.OSM()
        self.osm._RunRegistry()
        self.form = form
        
        self.dataset = {
            'hash': random.uniform(1, 2),
            'current': 0,
            'templates': {},
            'templatesReverse': {},
            'queue': queue.Queue(),
            'files': {
                "0": set()
            }
        }
        self.logger = Logger.Logger(self)
        db = FileManager.FileDBLoader(self.logger).loadJSON()
        if db:
            self.dataset = db
        else:
            del db
            self.backgroundTask = FileManager.FileSpider(self.dataset, self.logger)
            self.FileQueue = FileManager.FileDBInserter(self.dataset, self.logger)
            
            self.backgroundTask.start(QThread.Priority.HighestPriority)
            self.FileQueue.start(QThread.Priority.HighPriority)
        
        self.reconstructWorker = FileManager.FileSearcher(self.dataset, self.logger)
        self.fileAmountHelper = FileAmountUpdater(self)
        self.reconstructThread = QThread()
        
        self.reconstructWorker.moveToThread(self.reconstructThread)
        self.reconstructWorker.reconstruct.connect(self.filesFromPaths)
        
        self.reconstructThread.start(QThread.Priority.NormalPriority)
        self.fileAmountHelper.start(QThread.Priority.LowestPriority)
        self.logger.start(QThread.Priority.LowestPriority)
        
        self.toggleSignal.connect(self.toggleVisibility) # type: ignore
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint) # type: ignore  
        self.setFixedSize(1600, 384)
        
        keyboard.add_hotkey("+".join([self.config.KEY1, self.config.KEY2]), self.toggleSignal.emit) # type: ignore
        
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.textEdit.textChanged.connect(self.inputManager)
        self.ui.listWidget.itemClicked.connect(self.openFile)
        self.ui.listWidget.itemEntered.connect(self.displayPreview)
        
        self.fadeTimer = QTimer()
        self.debounceTimer = QTimer()
        
        self.fadeTimer.setInterval(self.config.FADE_TIMER)
        self.debounceTimer.setSingleShot(True)
        self.debounceTimer.setInterval(500)
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
        self.ui.listWidget.setMouseTracking(True)
        self.ui.listWidget.setIconSize(QSize(self.config.ICON_WIDTH, self.config.ICON_HEIGHT))
        self.ui.listWidget.installEventFilter(self)
        self.setStyleSheet(self.UIStyle)
    
    def openFile(
        self, 
        item: Union[QListWidgetItem, None] = None
    ) -> None:
        """Opens file of given item or currently selected item

        Args:
            item (Union[QListWidgetItem, None], optional): Listwidget item. Defaults to None.
        """
        if not item:
            item = self.ui.listWidget.currentItem()
        
        if item is not None:
            path = item.text()
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
    
    def openDirectory(self, item: Union[QListWidgetItem, None] = None) -> None:
        """Opens the directory with the path of the current
        item in the listWidget or a given item.

        Args:
            item (Union[QListWidgetItem, None], optional): Listwidget item. Defaults to None.
        """
        if not item:
            item = self.ui.listWidget.currentItem()
        
        if item is not None:
            path = item.text()
            folder, filename = self.osm.splitPath(path)
            del filename
            try:
                subprocess.run(['explorer', folder], check=False)
            except subprocess.CalledProcessError as e:
                print(e)
            self.fadeOut()
    
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
        self.fadeOut()
    
    def keyPressEvent( # type: ignore
        self, 
        event: QKeyEvent
    ) -> None:
        """Calls certain functions and methods depending on
        pressed hotkeys.
        
        - Esc           -> Window fades out
        - Ctrl + Enter  -> Open top file
        - Alt  + Enter  -> Open top directory

        Args:
            event (QKeyEvent): Keyboard event
        """
        if event.key() == Qt.Key.Key_Escape:
            self.fadeOut()
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Return:
            try:
                topItem = self.ui.listWidget.item(0)
                self.openFile(topItem)
            except:
                return
        elif event.modifiers() == Qt.KeyboardModifier.AltModifier and event.key() == Qt.Key.Key_Return:
            try:
                topItem = self.ui.listWidget.item(0)
                self.openDirectory(topItem)
            except:
                return
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Backspace:
            self.ui.listWidget.clear()
    
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
        if event.type() == QEvent.Type.ContextMenu and source is self.ui.listWidget:
            menu = QMenu()
            openFile = QAction("Open File", menu)
            openDir = QAction("Open Directory", menu)
            copyPath = QAction("Copy Path", menu)
            
            curItem = self.ui.listWidget.currentItem()
            if curItem:
                openFile.triggered.connect(lambda: self.openFile(curItem))
                openDir.triggered.connect(lambda: self.openDirectory(curItem))
                copyPath.triggered.connect(lambda: self.copyPath(curItem.text()))
            
            menu.addActions([openFile, openDir, copyPath])
            menu.exec_(event.globalPos())
            return True
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
        if len(text) > 2:
            self.ui.listWidget.clear()
            self.ui.listWidget.addItem("Loading...")
            self.reconstructWorker.checkPaths.emit(text)
        else:
            return
    
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
        self.ui.listWidget.clear()
        
        if len(paths) <= 0:
            self.ui.listWidget.addItem("No results found.")
        
        for path in paths:
            item = QListWidgetItem(path)
            icon = QIcon(utils.getIcon(path))
            item.setIcon(icon)
            item.setToolTip(self.getToolTip(path))
            self.ui.listWidget.addItem(item)
    
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
        path = item.text()
        if path.endswith(tuple(utils.imageExts)):
            pixmap = QPixmap(path).scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio)
            self.ui.previewLabel.setPixmap(pixmap)
    
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
        extension = path.split(".")[-1]
        template, name = self.osm.splitPath(path)
        del template
        fileSize = self.formattedSize(os.path.getsize(path))
        return f"Extension:\t{extension}\nFilename:\t{name}\nFile size:\t{fileSize}"
    
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
        self.ui.listWidget.clear()
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
            self.msleep(10)  # update every 0.5 seconds
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = QApplication(sys.argv)
    
    ui = SearchBar(form)
    
    sys.exit(app.exec_())

# TODO:     Add documentation                                                               (IN PROGRESS)
# TODO:     Code clean-up                                                                   (IN PROGRESS)
# TODO:     Add dimmed background?                                                          ()
# TODO:     More efficiency?            (current speed: 1,630,000 Files in 38 Seconds.)     (DONE)
            # Reverse hashmaps literally saved my life (thanks GPT, I was so close to figuring it out by myself lol)
            # Another idea: Individual threads for each drive with reverse look-up hashmaps i think that goes hard af
            # so we have:
                # main thread   -> GUI                                                      (DONE)
                # Manager1      -> walking through the OS, putting files into the queue     (DONE)
                # Manager2      -> adding files to the database                             (DONE)
                # Manager3      -> reconstructing paths                                     (DONE)
                # Helper1       -> Displays fileAmount repeatedly                           (DONE)
                # Split up files into multiple sublists [each list has max. 50,000 files]   (DONE)
# TODO:     Option to open file/directory                                                   (DONE)
# TODO:     Configs                                                                         (DONE)
# TODO:     Improve modules structure (object oriented?)                                    (DONE)

# TODO: Coming up Features
#       - Autostart                                                                         (DONE)
#       - Keyboard Shortcuts                                                                (DONE)
#       - Search Filters (type: .extension, size=>10MB etc)                                 
#       - Debounce timer                                                                    (DONE)
#       - Right-click Context menu instead                                                  (DONE)
#       - Better UI/UX (Accent Colors or smth idek)                                         (DONE)
#       - Bookmark files                                                                    
#       - Save and Load drives                                                              (DONE)
#           - Find way to convert JSON to dict with sets and queues and all                 (DONE)
#           - FIND A WAY TO NOT MAKE IT LOAD 2 DIFFERENT DICTIONARIES HELP???               (DONE)
#           - CURRENT PROBLEM: JSON SAVES ANY KEY AS A STRING NOT INT??                     (DONE)
#       - Convert drive.py to osm.py                                                        (DONE)
#       - Compress JSON obj with zlib (8.13x smaller)                                       (DONE)
#       - IMG Preview                                                                       (DONE)
#       - Refresh DB after 1 Day                                                            (DONE)
#       - Convert keys in dictionaries to integers for Runtime                              