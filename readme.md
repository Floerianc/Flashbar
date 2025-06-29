<img src="assets/banner.png">

<br>
<br>
<h1 align="center">Flashbar</h1>
<p align="center">By Floerianc</p>

<p align="center"> ⚡ Ultra-fast offline file search tool with a clean UI built using Python/PyQt5.<br>
Index 3,078,000+ files in a minute.
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

- **Near-instant indexing**: Over **900,000 files in 10 seconds**
- **Fuzzy search** with live, ranked results
- Fully **offline** with a lightweight, compressed DB
- **Multithreaded scanning** across drives
- File **relevancy tracking** (frequency, recency, score)
- Smart filters: `size>`, `name=`, `after=`, `type=`, etc.
- **Dark-themed PyQt5 GUI** with icon previews
- **Custom keybinds** and responsive hotkey toggle (default: `Alt+F12`)
- Safe, user-adjustable config — no code editing required

<hr>

## 🖥️ Usage

1. Launch the app.
2. Let FlashBar scan your system. *(Typically 30–60 seconds on first run.)*
3. Press your hotkey (default: `Alt+F12`) to open the search bar anytime.
4. Type your query — results appear instantly.
5. `Left-click` or `Ctrl+Enter` to open file, `Alt+Enter` to open directory, `Right-click` for context menu.

> 💡 You can search while scanning is in progress — results will improve as indexing completes.

## 🎛️ Controls & Search Filters

FlashBar is designed to be lightning-fast and **keyboard-optimized**. Here's a breakdown of all available controls and filters:

### 🕹️ Controls

| Key / Action    | Description                                           |
| --------------- | ----------------------------------------------------- |
| `Left-Click`    | Open the selected file instantly                      |
| `Right-Click`   | Open context menu for the selected file               |
| `Esc`           | Unfocus search bar *(if focused)*, or minimize window |
| `Ctrl+Enter`    | Open the **top-most** result (file)                   |
| `Alt+Enter`     | Open the **directory** of the top result              |
| `Right Arrow →` | Switch to the next tab (must unfocus searchbar)       |
| `Left Arrow ←`  | Switch to the previous tab                            |

---

### 🔍 Search Filters

FlashBar supports advanced **inline filtering** inside your search bar:

| Filter    | Description                                                        |
| --------- | ------------------------------------------------------------------ |
| `type=`   | Match file extensions (e.g. `type=pdf`, `type=jpg`)                |
| `name=`   | File name **must include** this string (exact match required)      |
| `size>`   | Files larger than specified size (e.g. `size>200kb`)               |
| `size<`   | Files smaller than specified size                                  |
| `before=` | Only files modified **before** a specific date                     |
| `after=`  | Only files modified **after** a specific date                      |
| `on=`     | Only files modified **on** a specific date                         |

**🗓️ Date Format Support:**

* Separator: `-` (e.g. `2024-01-05`)
* Supported formats:

  * `YYYY-MM-DD`
  * `DD-MM-YYYY`
  * `MM-DD-YYYY`

> ⚠️ Filters can be **combined** for even more accurate searches. Example:
> `type=pdf size>2mb after=2023-01-01`

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

## 📋 TODO / Roadmap

* [X] Add to Autostart
* [X] File type filters (e.g., `.pdf`, `>10MB`)
* [X] Context menu actions
* [X] Bookmarks
* [X] Export/import search DB
* [ ] Show directories too
* [ ] Instant look-up version
* [ ] More customization

---

<p align="center">
Made with ♥️ by <a href="https://github.com/Floerianc/">Florian.<br><a href="./LICENSE">» License «</a>
<br><br>
<img src="assets/icon.png" width=128>
</p>