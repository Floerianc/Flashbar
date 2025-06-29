# FlashBar - ./modules/menus/menus.py -> Saves templates for the context menus used by the GUI
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

from typing import TYPE_CHECKING
from PyQt5.QtWidgets import (
    QMenu, 
    QAction
)
from PyQt5.QtGui import QContextMenuEvent

if TYPE_CHECKING:
    from app import SearchBar

class Templates:
    def searchResultsMenu(self, cls: 'SearchBar', event: QContextMenuEvent) -> bool:
        menu = QMenu()
        openFile = QAction("Open File", menu)
        openDir = QAction("Open Directory", menu)
        copyPath = QAction("Copy Path", menu)
        bookmark = QAction("Add to Bookmarks", menu)
        
        curItem = cls.ui.searchResults.currentItem()
        if curItem:
            openFile.triggered.connect(lambda: cls.openFile(curItem))
            openDir.triggered.connect(lambda: cls.openDirectory(curItem))
            copyPath.triggered.connect(lambda: cls.copyPath(cls.rebuildPath(curItem.text())))
            bookmark.triggered.connect(lambda: cls.addToBookmarks(curItem))
        
        menu.addActions([openFile, openDir, copyPath, bookmark])
        menu.exec_(event.globalPos())
        return True
    
    def bookmarksMenu(self, cls: 'SearchBar', event: QContextMenuEvent) -> bool:
        menu = QMenu()
        openFile = QAction("Open File", menu)
        openDir = QAction("Open Directory", menu)
        copyPath = QAction("Copy Path", menu)
        rmBookmark = QAction("Remove Bookmark", menu)
        
        curItem = cls.ui.bookmarks.currentItem()
        if curItem:
            openFile.triggered.connect(lambda: cls.openFile(curItem))
            openDir.triggered.connect(lambda: cls.openDirectory(curItem))
            copyPath.triggered.connect(lambda: cls.copyPath(cls.rebuildPath(curItem.text())))
            rmBookmark.triggered.connect(lambda: cls.removeFromBookmarks(curItem, True))
        
        menu.addActions([openFile, openDir, copyPath, rmBookmark])
        menu.exec_(event.globalPos())
        return True
    
    def recentMenu(self, cls: 'SearchBar', event: QContextMenuEvent) -> bool:
        menu = QMenu()
        openFile = QAction("Open File", menu)
        openDir = QAction("Open Directory", menu)
        copyPath = QAction("Copy Path", menu)
        bookmark = QAction("Add to Bookmarks", menu)
        
        curItem = cls.ui.recentFiles.currentItem()
        if curItem:
            openFile.triggered.connect(lambda: cls.openFile(curItem))
            openDir.triggered.connect(lambda: cls.openDirectory(curItem))
            copyPath.triggered.connect(lambda: cls.copyPath(cls.rebuildPath(curItem.text())))
            bookmark.triggered.connect(lambda: cls.addToBookmarks(curItem))
        
        menu.addActions([openFile, openDir, copyPath, bookmark])
        menu.exec_(event.globalPos())
        return True