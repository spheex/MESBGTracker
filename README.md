# ⚔️ MESBG Hero Tracker

A clean, two-sided tactical army tracker built for the **Middle-Earth Strategy Battle Game**. This desktop application allows Player A and Player B to independently track critical stats (**Might, Will, Fate, and Wounds**) for heroes in their chosen factions during a match.

It fetches real-time, up-to-date stat and faction data automatically from the community data source, with full support for fielding multiple copies of non-unique (repeatable) heroes like Captains or Shaman.

---

## ✨ Features

* **Dual-Side Tracking:** Separate panels for Side 1 and Side 2 (e.g., Good vs. Evil).
* **Live Data Fetching:** Automatically syncs profiles, modern faction lists, and Legendary Legions.
* **Repeatable Heroes:** Add multiple copies of non-unique profiles (e.g., *Moria Goblin Captain*). The app automatically tracks them as `#1`, `#2`, etc., and cleanly re-indexes them if one is removed.
* **Visual Stat Bars:** Easy-to-read, color-coded progress bars for quick glance-value during intense tabletop matches:
  * 🟡 **Might**
  * 🔵 **Will**
  * 🟣 **Fate**
  * 🔴 **Wounds**
* **One-Click Resets:** Instantly reset a specific hero's stats back to their baseline profile or clear an entire side's roster.

---

## 🚀 Installation & Setup

Follow these straightforward steps to get the app running on your computer.

### 1. Prerequisites
Make sure you have **Python 3.10** or newer installed on your machine. You can download it from [python.org](https://www.python.org/).

### 2. Clone or Download the Project
Download the script file (`main.py`) directly, or clone this repository if you are using Git:
```bash
git clone git@github.com:spheex/MESBGTracker.git
cd MESBGTracker
```

### 3. Install Dependencies
This application relies on **PyQt6** for its visual desktop interface. Install it seamlessly using `pip`:
```bash
pip install PyQt6
```

💡 Note: No other external dependencies are required! The network data fetching uses Python's built-in libraries.

### 🎮 How to Run and Use
Running the Application
Launch the app from your terminal or command prompt by executing:

```bash
python main.py
```

### Step-by-Step Usage:
1. **Select an Army:** Click the dropdown menu under Side 1 or Side 2 to choose a faction.
2. **Choose Heroes:** Click **"Choose Heroes…"** to open the selection overlay.
3. **Set Quantities:**
   * Click the spin box next to a **Unique** hero to toggle them into your roster (0 or 1).
   * Adjust the counter for **Non-unique** heroes to bring multiple copies (e.g., 3 *Corsair Captains*).
4. **Confirm:** Click **"Confirm Selection"** to deploy their dynamic tracker cards to the table layout.
5. **Track Progress:** Use the spin boxes on the battlefield cards to reduce or increase stats as the game progresses.

---

## 🛠️ Requirements

The project uses a minimal system footprint. Requirements are tracked in standard format below:

* **Python** `>= 3.10`
* **PyQt6** `>= 6.4.0`
* **An active internet connection** *(Required on startup to pull the latest JSON dataset)*

---

## 📄 License

This project is licensed under the **GNU General Public License v3 (GPLv3)**. 

Because this application relies directly on the free tier of the **PyQt6** framework, it inherits GPL obligations. This ensures that the code remains free, open-source, and accessible to the entire tabletop gaming community forever. See the `LICENSE` file for full parameters.

---

## 🤝 Acknowledgments
* Data dynamically sourced from the comprehensive community project hosted at [nowforwrath.github.io](https://nowforwrath.github.io/data2024.json).