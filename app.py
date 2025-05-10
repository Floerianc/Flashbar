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
    QEvent
)
from PyQt5.QtWidgets import(
    QApplication,
    QWidget,
    QListWidgetItem,
    QListWidget
)
from PyQt5.QtGui import(
    QIcon,
    QContextMenuEvent
)
import modules.FileManager as FileManager
import modules.Logger as Logger
import config as Config
import utils
import modules.drive as _drive
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
        self.style = """
        QWidget{
            background: rgb(30, 30, 40);
        }
        QPlainTextEdit#textEdit{
            background-color: rgb(30, 30, 40);
            color: white;
            font-weight: bold;
            font-size: 64pt;
            border-radius: 16px;
            padding: 8px;
        }
        QListWidget#listWidget{
            background-color: rgb(50, 50, 60);
            border-radius: 16px;
            padding: 8px;
            color: white;
            font-size: 24pt;
        }
        QListWidget::item {
            height: 48px; 
            padding: 8px; 
        }
        QListWidget::item:hover {
            background-color: rgb(90, 90, 100);
        }
        QListWidget::item:selected {
            background-color: rgb(70, 70, 80);
        }
        QScrollBar:vertical{
            background: rgb(60, 60, 70);
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar:horizontal{
            background: rgb(60, 60, 70);
            height: 16px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical,  QScrollBar::handle:horizontal{
            background: rgb(80, 80, 90);
            min-height: 16px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background: rgb(90, 90, 100);
        }
        QScrollBar::add-line:vertical, QScrollBar::add-line:horizontal
        QScrollBar::sub-line:vertical, QScrollBar::sub-line:horizontal {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::add-page:horizontal
        QScrollBar::sub-page:vertical, QScrollBar::sub-page:horizontal {
            background: rgb(10, 10, 20);
        }
        """
        
        super().__init__()
        self.config = Config.Config("UI", "Control")
        
        self.dataset = {
            'current': 0,
            'templates': {},
            'templatesReverse': {},
            'queue': queue.Queue(),
            'files': {
                0: []
            }
        }
        
        self.logger = Logger.Logger(self.dataset)
        self.logger.start(QThread.Priority.LowestPriority)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint) # | Qt.WindowType.WindowStaysOnTopHint
        self.setFixedSize(1280, 384)
        
        keyboard.add_hotkey("+".join([self.config.KEY1, self.config.KEY2]), self.toggleSignal.emit)
        
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.textEdit.textChanged.connect(self.inputManager)
        self.ui.listWidget.itemClicked.connect(self.openFile)
        self.toggleSignal.connect(self.toggleVisibility)
        
        self.fadeTimer = QTimer()
        self.fadeTimer.setInterval(self.config.FADE_TIMER)
        
        self.backgroundTask = FileManager.FileSpider(self.dataset)
        self.backgroundTask.start()
        
        self.FileQueue = FileManager.FileDBManager(self.dataset)
        self.FileQueue.start()
        
        self.reconstructThread = QThread()
        
        self.reconstructWorker = FileManager.FileSearcher(self.dataset)
        self.reconstructWorker.moveToThread(self.reconstructThread)
        self.reconstructWorker.reconstruct.connect(self.filesFromPaths)
        
        self.reconstructThread.start()
        
        self.setupUi()
        self.fadeIn()
    
    def setupUi(self) -> None:
        """Sets a few settings and connections for the UI widgets
        """
        self.ui.listWidget.setIconSize(QSize(self.config.ICON_WIDTH, self.config.ICON_HEIGHT))
        self.ui.listWidget.installEventFilter(self)
        self.setStyleSheet(self.style)
    
    def openFile(self) -> None:
        """Opens the file with the path of the current
        item in the listWidget.
        
        The path is the text on the listWidget
        """
        path = self.ui.listWidget.currentItem().text()
        try:
            subprocess.run(['explorer', path], check=False)
        except subprocess.CalledProcessError as e:
            print(e)
        self.fadeOut()
    
    def openDirectory(self) -> None:
        """Opens the directory with the path of the current
        item in the listWidget.
        
        The path is the text on the listWidget
        """
        path = self.ui.listWidget.currentItem().text()
        folder, filename = _drive.splitPath(path)
        del filename
        try:
            subprocess.run(['explorer', folder], check=False)
        except subprocess.CalledProcessError as e:
            print(e)
        self.fadeOut()
    
    def eventFilter(
        self, 
        source: QListWidget, 
        event: QContextMenuEvent
    ) -> None:
        """Handles right-clicking in this Window
        
        If you right-click on the listWidget it will open
        the directory of the file you clicked on.

        Args:
            source (QListWidget): The listWidget you clicked on
            event (QContextMenuEvent): Click event

        Returns:
            _type_: _description_
        """
        # eventfilter does not support left-click so it's as a connection in the __init__
        if event.type() == QEvent.Type.ContextMenu and source is self.ui.listWidget:
            self.openDirectory()
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
    
    def inputManager(self) -> None:
        """Emits a signal to the reconstructWorker to check
        paths if you type more than 3 character into the SearchBar
        """
        text = self.ui.textEdit.toPlainText()
        self.reconstructWorker.checkPaths.emit(text) if len(text) > 3 else None
    
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
        for path in paths:
            item = QListWidgetItem(path)
            icon = QIcon(utils.getIcon(path))
            item.setIcon(icon)
            item.setToolTip(self.getToolTip(path))
            self.ui.listWidget.addItem(item)
    
    def formattedSize(
        self, 
        fileSize: int
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
        template, name = _drive.splitPath(path)
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
        
        if self.isVisible():
            self.fadeOut()
            self.ui.textEdit.setFocus(False)
        else:
            self.fadeIn()
            self.ui.textEdit.setFocus(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = QWidget()
    
    ui = SearchBar(form)
    
    sys.exit(app.exec_())

# TODO:     Add documentation
# TODO:     Add dimmed background?
# TODO:     More efficiency?            (current speed: 1,630,000 Files in 38 Seconds.)
            # Reverse hashmaps literally saved my life (thanks GPT, I was so close to figuring it out lol)
            # Another idea: Individual threads for each drive with reverse look-up hashmaps i think that goes hard af
            # so we have:
                # main thread   -> GUI                                                      (DONE)
                # Manager1      -> walking through the OS, putting files into the queue     (DONE)
                # Manager2      -> adding files to the database                             (DONE)
                # Manager3      -> reconstructing paths                                     (DONE)
                # Split up files into multiple sublists [each list has max. 200,000 files]  (DONE)
# TODO:     Option to open file/directory                                                   (DONE)
# TODO:     Configs                                                                         (DONE)
# TODO:     Improve modules structure (object oriented?)                                    (DONE)

# TODO: Coming up Features
#       - Search Filters (type: .extension, size=>10MB etc)
#       - Right-click Context menu instead
#       - Better UI/UX
#       - Bookmark files
#       - Save and Load drives