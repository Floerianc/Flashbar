# FlashBar - utils.py -> Offers different little utilities
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
from modules.osm import OSM

def rangespace(
    start: float, 
    stop: float, 
    steps: int = 32
) -> list:
    """Creates a list of numbers between start and stop with a
    regular distance to each other

    Args:
        start (float): start number
        stop (float): end number
        steps (int, optional): amount of steps between start and end. Defaults to 32.

    Returns:
        list: list of numbers
    """
    step_size = (stop - start) / steps
    return [start + (step_size * iteration) for iteration in range(steps + 1)]

def getIcon(filename: str) -> str:
    """Returns the path to an icon for a certain extension
    
    It takes the file's name and then looks for the extension
    of the file.
    
    It then looks at the extensionToIcon dictionary and looks
    for a fitting icon for the specific extension.

    Args:
        filename (str): name of the file

    Returns:
        str: path to the icon
    """
    extension = os.path.splitext(filename)[1].lower()
    extensionToIcon = {
        '.bmp': 'bmp',
        '.csv': 'csv',
        '.doc': 'doc',
        '.docx': 'doc',
        '.gif': 'gif',
        '.html': 'html',
        '.jpg': 'jpg',
        '.jpeg': 'jpg',
        '.json': 'json',
        '.mp3': 'mp3',
        '.mp4': 'mp4',
        '.odt': 'odt',
        '.pdf': 'pdf',
        '.png': 'png',
        '.tiff': 'tiff',
        '.txt': 'txt',
        '.xls': 'xls',
        '.zip': 'zip',
        ".exe": "exe",
    }

    icon_name = extensionToIcon.get(extension, 'txt')  # fallback to 'txt' if not found
    return f"{OSM().exeDir()}\\icons\\{icon_name}.png"

imageExts = [
    '.png', 
    '.jpg', 
    '.jpeg'
]