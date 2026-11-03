
# Drum Sample Inventory & SFZ Generator 

A modern, GUI-based desktop utility built with Python and Tkinter for audio producers and sound designers. It automatically crawls acoustic or electronic drum sample libraries, parses complex filename conventions (including velocity layers and round-robins), generates a comprehensive inventory database (`.csv`), and compiles a fully mapped multi-track SFZ instrument file (`.sfz`) ready for Sforzando, Decent Sampler, or ARIA.

---

##  Key Features

* **Smart Folder Scanning & Parsing:** Recursively crawls library directories, recognizes audio formats (`.wav`, `.flac`, `.aif`, `.mp3`, etc.), and extracts instrument types, articulations, velocity layers, and round-robins.
* **Automated SFZ Compiler:** Generates clean SFZ markup files featuring velocity switching (`lovel`/`hivel`), round-robin sequencing (`seq_length`/`seq_position`), and multi-track routing (`output=`).
* **Interactive Settings Editor:** Easily customize MIDI note assignments, output track routing indexes, and filename keyword identifiers directly inside a clean GUI.
* **Built-in CSV Viewer:** Inspect generated inventories or external CSV databases right inside the app, complete with right-click clipboard copying for cells and rows.
* **Modern Dark UI:** Styled with a sleek developer theme (GitHub Dark inspired).

---

##  Downloading Pre-Built Binaries (Recommended)
You don't need Python installed to run this app! Head over to the **[Releases](../../releases)** page to download the standalone executable for your operating system:
* **Linux:** `DrumSFZGenerator-linux`
* **Windows:** `DrumSFZGenerator-windows.exe`
* **macOS:** `DrumSFZGenerator-macos`

---

##  Running from Source (Arch Linux / Python)

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/your-repo-name.git](https://github.com/YOUR_USERNAME/your-repo-name.git)
   cd your-repo-name

   Install dependencies:

pip install -r requirements.txt
# Or on Arch: sudo pacman -S python-pyinstaller

Run the script:

python your_script_name.py

   Filename Convention Guide

To get the best results out of the automatic parser, structure sample filenames using hyphen-separated tokens:[Library]-[SampleGroup]-[Instrument]-[Articulation]-RR[x]-Vel[y].[ext]

    Round Robin: e.g., RR1, RR2, RR3

    Velocity Layer: e.g., Vel1, Vel2

    Mic / Bus Routing: Keywords like close, overhead, room, top, bottom

 License

Distributed under the MIT License.