# FlashBar - ./modules/UserData.py -> Saves and loads infomration regarding the behaviour of the user while using the program.
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

import json
import pprint
import zlib
from typing import Any
from modules.OSM import OSM
from modules.Relevancy import Relevance

osm = OSM()

def jsonify(userData: dict[str, list | dict]) -> dict[str, Any]:
    for key in userData:
        if key == "relevancy":
            jsonable = {key: value.toDict() for key, value in userData['relevancy'].items()} # type: ignore
            userData['relevancy'] = jsonable
    return userData

def dejsonify(userData: dict[str, list | dict]) -> dict[str, Any]:
    for key in userData:
        if key == "relevancy":
            dictable = {key: Relevance.fromDict(value) for key, value in userData['relevancy'].items()} # type: ignore
            userData['relevancy'] = dictable
    return userData

def saveData(userData: dict[str, Any]) -> None:
    with open(f"{osm.exeDir()}\\user\\data.db", "wb") as bmf:
        shellCopy = userData.copy()
        shellCopy = jsonify(shellCopy)
        
        jsonData = json.dumps(shellCopy)
        compressed = zlib.compress(jsonData.encode(), 9)
        bmf.write(compressed)

def loadData() -> dict[str, Any] | None:
    try:
        with open(f"{osm.exeDir()}\\user\\data.db", "rb") as bmf:
            compressed = bmf.read()
            decompressed = zlib.decompress(compressed)
            decodedData = decompressed.decode()
            jsonData = json.loads(decodedData)
            dictData = dejsonify(jsonData)
            pprint.pprint(dictData, indent=4)
            return dictData
    except Exception as e:
        print(e)
        return None