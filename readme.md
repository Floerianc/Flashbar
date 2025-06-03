<img src="assets/banner.png">

<br>
<br>
<h1 align="center">Flashbar</h1>
<p align="center">By Floerianc</p>

<p align="center"> ⚡ Ultra-fast offline file search tool with a clean UI built using Python/PyQt5.<br>
Index 2,690,000+ files in a minute.
</p>

<p align="center">
    <a href="https://github.com/Floerianc/Flashbar/releases">
        <img src="https://img.shields.io/github/v/release/Floerianc/Flashbar?label=Latest%20Release&style=flat-square" alt="Latest Release">
    </a>
    <a href="https://github.com/Floerianc/FlashBar/issues">
        <img src="https://img.shields.io/github/issues/Floerianc/FlashBar?style=flat-square" alt="Issues">
    </a>
    <a href="https://github.com/Floerianc/FlashBar/stargazers">
        <img src="https://img.shields.io/github/stars/Floerianc/FlashBar?style=flat-square" alt="Stars">
    </a>
</p>

<hr>

## ℹ️ Features
- **Blazingly** fast file indexing (multi-threaded)
- **Fuzzy search** with **live** results
- **Customizable** keybinds and clean GUI
- Reverse **path reconstruction**
- Configurable batch sizes
- **Clean** dark-themed UI
- **Lightweight** JSON database (15 MB for 1,000,000 files)
- File **preview** for images

<hr>

## 🖥️ Usage

- Start program
- Wait for the program to scan every directory _(Takes about 0.5 - 2 Minutes)_
    - If there's no pre-existing image of your hard drive of course
  - You can also use the searchbar while the program is still loading but not every file can be found 
- Press custom keybind (Default: `Alt+F12`)
- Search for file
- `Left-click` or `Ctrl+Enter` to open the file, `Alt+Enter` to open the directory. `Right-click` to open context menu.

<p align="center">
    <img src="assets/preview.gif">
</p>

<hr>

## 📦 Installation

```bash
git clone https://github.com/floerianc/flashbar.git
cd flashbar
pip install -r requirements.txt
python app.py
```

<hr>

## ⚒️ Configuration

All user settings are in `user/settings.cfg`.

| Setting      | Description                                                            |
| ------------ | -----------------------------------------------------------------------|
| `ICON_WIDTH` | Width of the icon displayed when searching                             |
| `ICON_HEIGHT`| Height of the icon displayed when searching                            |
| `KEY1`       | Main key (e.g. `ctrl`)                                                 |
| `KEY2`       | Secondary key (e.g. `space`)                                           |
| `BATCH_SIZE` | Size of batch loaded into queue                                        |
| `CHUNK_SIZE` | Size of chunks loaded into the program                                 |
| `FADE_TIMER` | UI fade speed                                                          |
| `MIN_MATCH`  | Minimum amount of match of user input and file name                    |
| `MAX_RESULTS`| Maximum amount of results                                              |
| `INTERVAL`   | Amount of time in seconds the program waits before writing info logs   |

---

## 🧑‍💼 Architecture Overview

* `SearchBar.py`: Main UI logic + file interaction
* `config.py`: Loads settings using `ConfigParser`
* `utils.py`: Helpers
* `osm.py`: Helpers & Logical Drives
* `FileManager.py`: Main File & OS logic
* `Logger.py`: Logs info for user  
* `user/settings.cfg`: User-tweakable preferences
* `user/user.db`: Saved database containing each file

---

## 📋 TODO / Roadmap

* [X] Add to Autostart
* [ ] File type filters (e.g., `.pdf`, `>10MB`)
* [X] Context menu actions
* [ ] Bookmarks
* [X] Export/import search DB

---

<p align="center">
Made with ♥️ by <a href="https://github.com/Floerianc/">Florian.<br><a href="./LICENSE">» License «</a>
<br><br>
<img src="assets/icon.png" width=128>
</p>