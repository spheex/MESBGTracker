"""
Middle-Earth Strategy Battle Game – Hero Tracker
Two-sided army tracker with support for non-unique (repeatable) heroes and casualty thresholds.
"""

import sys
import json
import urllib.request
import math

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QScrollArea, QFrame,
    QMessageBox, QGridLayout, QProgressBar,
    QListWidget, QListWidgetItem, QAbstractItemView, QSpinBox,
    QGroupBox, QStatusBar, QSplitter,
)

DATA_URL = "https://nowforwrath.github.io/data2024.json"

# ── Colour palette ────────────────────────────────────────────────────────────
BG_DARK      = "#3b1d1e"
BG_MID       = "#4d2527"
BG_CARD      = "#5a2d2f"
ACCENT       = "#841912"
ACCENT_LIGHT = "#b52218"
GOLD         = "#a58650"
GOLD_LIGHT   = "#c9a96e"
TEXT_MAIN    = "#fffffe"
TEXT_DIM     = "#c8b8b9"
BTN_BG       = "#a58650"
BTN_HOVER    = "#c9a96e"

# Status colors for indicator badges
COLOR_INACTIVE = "#555555"
COLOR_BROKEN   = "#d97706"  # Amber/Orange
COLOR_QUARTERED = "#dc2626" # Deep Red

SIDE_COLOURS = ["#2a5aaa", "#aa2a2a"]
SIDE_NAMES   = ["Side 1", "Side 2"]

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_MAIN};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}
QLabel {{ color: {TEXT_MAIN}; }}
QLabel#title {{
    font-size: 20px; font-weight: bold;
    color: {GOLD_LIGHT}; letter-spacing: 1px;
}}
QLabel#subtitle {{ font-size: 11px; color: {TEXT_DIM}; }}
QLabel#section {{
    font-size: 13px; font-weight: bold;
    color: {GOLD}; margin-top: 4px;
}}
QComboBox {{
    background-color: {BG_MID}; color: {TEXT_MAIN};
    border: 1px solid {ACCENT}; border-radius: 4px;
    padding: 4px 8px; min-height: 26px;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {BG_MID}; color: {TEXT_MAIN};
    selection-background-color: {ACCENT}; border: 1px solid {ACCENT};
}}
QListWidget {{
    background-color: {BG_MID}; color: {TEXT_MAIN};
    border: 1px solid {ACCENT}; border-radius: 4px;
}}
QListWidget::item {{ padding: 4px 8px; }}
QListWidget::item:selected {{ background-color: {ACCENT}; }}
QListWidget::item:hover    {{ background-color: {BG_CARD}; }}
QPushButton {{
    background-color: {BTN_BG}; color: #1a0a0a;
    border: none; border-radius: 4px;
    padding: 6px 14px; font-weight: bold;
}}
QPushButton:hover    {{ background-color: {BTN_HOVER}; }}
QPushButton:pressed  {{ background-color: {ACCENT}; color: {TEXT_MAIN}; }}
QPushButton:disabled {{ background-color: #5a4530; color: #8a7060; }}
QPushButton#danger   {{ background-color: {ACCENT}; color: {TEXT_MAIN}; }}
QPushButton#danger:hover {{ background-color: {ACCENT_LIGHT}; }}
QScrollArea {{ border: none; background-color: transparent; }}
QScrollBar:vertical {{
    background: {BG_MID}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QGroupBox {{
    background-color: {BG_CARD}; border: 1px solid {ACCENT};
    border-radius: 6px; margin-top: 14px; padding: 8px;
    font-weight: bold; color: {GOLD};
}}
QGroupBox::title {{
    subcontrol-origin: margin; subcontrol-position: top left;
    padding: 0 6px; color: {GOLD_LIGHT}; font-size: 13px;
}}
QSpinBox {{
    background-color: {BG_MID}; color: {TEXT_MAIN};
    border: 1px solid {ACCENT}; border-radius: 3px;
    padding: 2px 4px; min-width: 52px; min-height: 22px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {ACCENT}; border: none; width: 16px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {ACCENT_LIGHT};
}}
QProgressBar {{
    background-color: {BG_MID}; border: 1px solid {ACCENT};
    border-radius: 3px; height: 8px; color: transparent;
}}
QProgressBar::chunk {{ background-color: {GOLD}; border-radius: 3px; }}
QStatusBar {{
    background-color: {BG_MID}; color: {TEXT_DIM};
    border-top: 1px solid {ACCENT};
}}
QFrame#separator {{ background-color: {ACCENT}; max-height: 1px; }}
QSplitter::handle {{ background-color: {ACCENT}; width: 2px; }}

QLabel#badge {{
    border-radius: 4px;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 11px;
    color: #ffffff;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Background data-loading thread
# ─────────────────────────────────────────────────────────────────────────────
class DataLoader(QThread):
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def run(self):
        try:
            req = urllib.request.Request(DATA_URL, headers={"User-Agent": "MESBG-Tracker/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = json.loads(resp.read().decode())
            self.finished.emit(raw)
        except Exception as exc:
            self.error.emit(str(exc))


def is_unique(hero: dict) -> bool:
    """Return True if the hero has 'Unique' in their unit_type list."""
    return "Unique" in hero.get("unitType", [])


def parse_armies(raw: dict) -> tuple[list[str], dict[str, list[dict]]]:
    """
    Returns:
        army_names  – sorted list of faction name strings
        army_heroes – { faction_name: [ hero_dict, ... ] }
    Each hero_dict contains: name, might, will, fate, wounds, unique (bool).
    """
    raw_data = raw.get("data", {})
    army_heroes: dict[str, list[dict]] = {}

    if not isinstance(raw_data, dict):
        return [], {}

    heroes = raw_data.get("heroes", [])

    for hero in heroes:
        if not isinstance(hero, dict):
            continue
        hero_name = hero.get("name", "?")
        entry = {
            "name":   hero_name,
            "might":  int(hero.get("might",  0) or 0),
            "will":   int(hero.get("will",   0) or 0),
            "fate":   int(hero.get("fate",   0) or 0),
            "wounds": int(hero.get("wounds", 1) or 1),
            "unique": is_unique(hero),
            "unit_type": hero.get("unit_type", []),
        }
        for faction_ref in hero.get("factions", []):
            fname = ""
            if isinstance(faction_ref, str):
                fname = faction_ref
            elif isinstance(faction_ref, dict):
                fname = faction_ref.get("name", "")
            if not fname:
                continue
            if fname not in army_heroes:
                army_heroes[fname] = []
            army_heroes[fname].append(dict(entry))

    for fname in army_heroes:
        army_heroes[fname].sort(key=lambda h: h["name"].casefold())

    army_names = sorted(army_heroes.keys(), key=str.casefold)
    return army_names, army_heroes


# ─────────────────────────────────────────────────────────────────────────────
# Stat row widget
# ─────────────────────────────────────────────────────────────────────────────
class StatRow(QWidget):
    COLOURS = {
        "Might":  "#e8c44a",
        "Will":   "#4ab8e8",
        "Fate":   "#a84ae8",
        "Wounds": "#e84a4a",
    }

    def __init__(self, label: str, maximum: int, parent=None):
        super().__init__(parent)
        self.maximum = maximum
        colour = self.COLOURS.get(label, GOLD)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 1, 0, 1)
        row.setSpacing(6)

        lbl = QLabel(label)
        lbl.setFixedWidth(48)
        lbl.setStyleSheet(f"color: {colour}; font-weight: bold; font-size: 11px;")
        row.addWidget(lbl)

        self.spin = QSpinBox()
        self.spin.setRange(0, maximum)
        self.spin.setValue(maximum)
        self.spin.setFixedWidth(54)
        row.addWidget(self.spin)

        self.bar = QProgressBar()
        self.bar.setRange(0, max(maximum, 1))
        self.bar.setValue(maximum)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet(
            self.bar.styleSheet() +
            f" QProgressBar::chunk {{ background-color: {colour}; }}"
        )
        row.addWidget(self.bar)

        max_lbl = QLabel(f"/ {maximum}")
        max_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
        max_lbl.setFixedWidth(30)
        row.addWidget(max_lbl)

        self.spin.valueChanged.connect(self.bar.setValue)

    def reset(self): self.spin.setValue(self.maximum)


# ─────────────────────────────────────────────────────────────────────────────
# Hero card
# ─────────────────────────────────────────────────────────────────────────────
class HeroCard(QGroupBox):
    remove_requested = pyqtSignal(str)

    def __init__(self, hero: dict, card_id: str, instance_label: str, parent=None):
        title = hero["name"] if not instance_label else f"{hero['name']}  {instance_label}"
        super().__init__(title, parent)
        self.card_id = card_id
        self._build(hero)

    def _build(self, hero: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(3)

        unit_types = hero.get("unit_type", [])
        if unit_types:
            badge_text = "  ·  ".join(unit_types)
            badge = QLabel(badge_text)
            colour = TEXT_DIM if hero.get("unique") else "#7adfaa"
            badge.setStyleSheet(f"color: {colour}; font-size: 10px; font-style: italic;")
            badge.setWordWrap(True)
            layout.addWidget(badge)

        self.stat_rows: dict[str, StatRow] = {}
        for label, key in [("Might","might"),("Will","will"),("Fate","fate"),("Wounds","wounds")]:
            sr = StatRow(label, int(hero.get(key, 0) or 0))
            layout.addWidget(sr)
            self.stat_rows[label] = sr

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("↺ Reset")
        reset_btn.setFixedHeight(26)
        reset_btn.clicked.connect(self.reset_stats)
        btn_row.addWidget(reset_btn)

        rm_btn = QPushButton("✕ Remove")
        rm_btn.setObjectName("danger")
        rm_btn.setFixedHeight(26)
        rm_btn.clicked.connect(lambda: self.remove_requested.emit(self.card_id))
        btn_row.addWidget(rm_btn)
        layout.addLayout(btn_row)

    def reset_stats(self):
        for sr in self.stat_rows.values():
            sr.reset()


# ─────────────────────────────────────────────────────────────────────────────
# Hero selector popup
# ─────────────────────────────────────────────────────────────────────────────
class HeroSelectorRow(QWidget):

    def __init__(self, hero: dict, current_count: int, parent=None):
        super().__init__(parent)
        self.hero = hero
        unique = hero.get("unique", True)

        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(8)

        name_lbl = QLabel(hero["name"])
        name_lbl.setMinimumWidth(180)
        row.addWidget(name_lbl)

        if unique:
            badge = QLabel("Unique")
            badge.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-style: italic;")
        else:
            badge = QLabel("Non-unique")
            badge.setStyleSheet("color: #7adfaa; font-size: 10px; font-style: italic;")
        badge.setFixedWidth(72)
        row.addWidget(badge)

        # Count control
        if unique:
            # Simple checkbox-style: 0 or 1
            self.spin = QSpinBox()
            self.spin.setRange(0, 1)
            self.spin.setValue(min(current_count, 1))
            self.spin.setFixedWidth(52)
            self.spin.setToolTip("Unique – can only be taken once")
        else:
            self.spin = QSpinBox()
            self.spin.setRange(0, 99)
            self.spin.setValue(current_count)
            self.spin.setFixedWidth(52)
            self.spin.setToolTip("Non-unique – set how many copies to field")
        row.addWidget(self.spin)

        copies_lbl = QLabel("cop." if not unique else "")
        copies_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px;")
        copies_lbl.setFixedWidth(28)
        row.addWidget(copies_lbl)

    def requested_count(self) -> int:
        return self.spin.value()


class HeroSelector(QWidget):
    confirmed = pyqtSignal(list)

    def __init__(self, heroes: list[dict], current_counts: dict[str, int], parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setMinimumWidth(380)
        self.setMinimumHeight(400)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        hdr = QLabel("Select heroes  ·  set count for non-unique")
        hdr.setStyleSheet(f"color: {GOLD}; font-weight: bold; font-size: 11px;")
        root.addWidget(hdr)

        col_hdr = QHBoxLayout()
        for txt, w in [("Name", 180), ("Type", 72), ("Count", 52)]:
            l = QLabel(txt)
            l.setFixedWidth(w)
            l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-weight: bold;")
            col_hdr.addWidget(l)
        col_hdr.addStretch()
        root.addLayout(col_hdr)

        sep = QFrame(); sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        self._rows: list[HeroSelectorRow] = []
        for hero in heroes:
            count = current_counts.get(hero["name"], 0)
            row_w = HeroSelectorRow(hero, count)
            vbox.addWidget(row_w)
            self._rows.append(row_w)

        vbox.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        confirm_btn = QPushButton("Confirm Selection")
        confirm_btn.clicked.connect(self._confirm)
        root.addWidget(confirm_btn)

    def _confirm(self):
        result = [
            (row.hero, row.requested_count())
            for row in self._rows
            if row.requested_count() > 0
        ]
        self.confirmed.emit(result)
        self.close()


# ─────────────────────────────────────────────────────────────────────────────
# Single-side panel
# ─────────────────────────────────────────────────────────────────────────────
class SidePanel(QWidget):

    def __init__(self, side_index: int, parent=None):
        super().__init__(parent)
        self.side_index  = side_index
        self.side_colour = SIDE_COLOURS[side_index]
        self.side_name   = SIDE_NAMES[side_index]

        self._army_names:  list[str]       = []
        self._army_heroes: dict[str, list] = {}
        self._current_army: str | None     = None

        self._hero_counts: dict[str, int] = {}
        self._hero_cards:  dict[str, HeroCard] = {}

        self._build_ui()

    def _update_badge_style(self, badge: QLabel, bg_color: str):
        # Simply update the background color. Qt already knows the object name is "badge".
        badge.setStyleSheet(f"background-color: {bg_color};")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        hdr = QLabel(f"⚔  {self.side_name}")
        hdr.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {self.side_colour};"
            f" border-bottom: 2px solid {self.side_colour}; padding-bottom: 4px;"
        )
        root.addWidget(hdr)

        # ── Roster Status Tracker (Casualties, Broken & Quartered) ────────────
        status_box = QGroupBox("Roster Status Tracker")
        status_layout = QGridLayout(status_box)
        status_layout.setSpacing(10)

        # Labels
        lbl_total = QLabel("Starting Units:")
        lbl_kills = QLabel("Kills / Casualties:")
        status_layout.addWidget(lbl_total, 0, 0)
        status_layout.addWidget(lbl_kills, 1, 0)

        # Inputs
        self.spin_total = QSpinBox()
        self.spin_total.setRange(1, 500)
        self.spin_total.setValue(1)
        self.spin_total.valueChanged.connect(self._recalculate_thresholds)
        status_layout.addWidget(self.spin_total, 0, 1)

        self.spin_kills = QSpinBox()
        self.spin_kills.setRange(0, 500)
        self.spin_kills.setValue(0)
        self.spin_kills.valueChanged.connect(self._recalculate_thresholds)
        status_layout.addWidget(self.spin_kills, 1, 1)

        # Info Displays
        self.lbl_broken_calc = QLabel("Broken at: --")
        self.lbl_broken_calc.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        status_layout.addWidget(self.lbl_broken_calc, 0, 2)

        self.lbl_quarter_calc = QLabel("Quartered at: --")
        self.lbl_quarter_calc.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        status_layout.addWidget(self.lbl_quarter_calc, 1, 2)

        # Status Badges
        self.badge_broken = QLabel("BROKEN")
        self.badge_broken.setObjectName("badge")
        self.badge_broken.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.badge_broken, 0, 3)

        self.badge_quartered = QLabel("QUARTERED")
        self.badge_quartered.setObjectName("badge")
        self.badge_quartered.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.badge_quartered, 1, 3)

        root.addWidget(status_box)
        
        # Reset visual lights initially
        self._update_badge_style(self.badge_broken, COLOR_INACTIVE)
        self._update_badge_style(self.badge_quartered, COLOR_INACTIVE)

        # ── Army Setup ────────────────────────────────────────────────────────
        army_lbl = QLabel("Army")
        army_lbl.setObjectName("section")
        root.addWidget(army_lbl)

        self.army_combo = QComboBox()
        self.army_combo.addItem("── Select an army ──")
        self.army_combo.currentIndexChanged.connect(self._on_army_changed)
        root.addWidget(self.army_combo)

        btn_row = QHBoxLayout()
        self.hero_btn = QPushButton("Choose Heroes…")
        self.hero_btn.setEnabled(False)
        self.hero_btn.clicked.connect(self._open_hero_selector)
        btn_row.addWidget(self.hero_btn)

        self.clear_btn = QPushButton("✕ Clear All")
        self.clear_btn.setObjectName("danger")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(self.clear_btn)
        root.addLayout(btn_row)

        sep = QFrame(); sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # ── Dashboard Layout ──────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.empty_lbl = QLabel("Select an army, then choose heroes.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; padding: 30px;")
        self.cards_layout.addWidget(self.empty_lbl, 0, 0, 1, 2)

        self.scroll.setWidget(self.cards_container)
        root.addWidget(self.scroll, stretch=1)

    #def _update_badge_style(self, badge: QLabel, bg_color: str):
    #    badge.setStyleSheet(f"background-color: {bg_color}; id: 'badge';")

    def _recalculate_thresholds(self):
        total = self.spin_total.value()
        kills = self.spin_kills.value()

        # MESBG rules: Broken at EQUAL TO OR GREATER THAN 50% casualties
        # For 10 units, 10 / 2 = 5 kills. For 11 units, 11 / 2 = 5.5 -> rounds up to 6 kills.
        broken_threshold = math.ceil(total / 2)

        # Quartered: Remaining models are strictly LESS THAN 25%
        # This is mathematically identical to casualties being strictly GREATER THAN 75%
        # For 10 units: 75% is 7.5 kills. Strictly greater than 7.5 means 8 kills.
        # For 12 units: 75% is 9 kills. Strictly greater than 9 means 10 kills.
        quartered_threshold = math.floor(total * 0.75) + 1

        self.lbl_broken_calc.setText(f"Broken at: {broken_threshold} kills")
        self.lbl_quarter_calc.setText(f"Quartered at: {quartered_threshold} kills")

        # Evaluate current conditions and light up badges
        if kills >= broken_threshold:
            self._update_badge_style(self.badge_broken, COLOR_BROKEN)
        else:
            self._update_badge_style(self.badge_broken, COLOR_INACTIVE)

        if kills >= quartered_threshold:
            self._update_badge_style(self.badge_quartered, COLOR_QUARTERED)
        else:
            self._update_badge_style(self.badge_quartered, COLOR_INACTIVE)

    def populate(self, army_names: list[str], army_heroes: dict[str, list]):
        self._army_names  = army_names
        self._army_heroes = army_heroes
        self.army_combo.blockSignals(True)
        self.army_combo.clear()
        self.army_combo.addItem("── Select an army ──")
        for name in army_names:
            self.army_combo.addItem(name)
        self.army_combo.blockSignals(False)
        self.army_combo.setEnabled(True)

    def _on_army_changed(self, index: int):
        if index <= 0:
            self._current_army = None
            self.hero_btn.setEnabled(False)
            return
        self._current_army = self._army_names[index - 1]
        self.hero_btn.setEnabled(True)

    def _open_hero_selector(self):
        if not self._current_army:
            return
        heroes = self._army_heroes.get(self._current_army, [])
        if not heroes:
            QMessageBox.information(self, "No Heroes", "This army has no heroes defined.")
            return

        sel = HeroSelector(heroes, dict(self._hero_counts), parent=self)
        sel.confirmed.connect(self._on_heroes_confirmed)
        pos = self.hero_btn.mapToGlobal(self.hero_btn.rect().bottomLeft())
        sel.move(pos)
        sel.show()

    def _on_heroes_confirmed(self, selections: list[tuple[dict, int]]):
        desired: dict[str, tuple[dict, int]] = {
            hero["name"]: (hero, count) for hero, count in selections
        }

        for hero_name in list(self._hero_counts.keys()):
            current = self._hero_counts[hero_name]
            wanted  = desired[hero_name][1] if hero_name in desired else 0
            if wanted < current:
                for i in range(wanted, current):
                    self._remove_card(f"{hero_name}#{i}")
                if wanted == 0:
                    del self._hero_counts[hero_name]
                else:
                    self._hero_counts[hero_name] = wanted

        for hero_name, (hero, wanted) in desired.items():
            current = self._hero_counts.get(hero_name, 0)
            for i in range(current, wanted):
                card_id = f"{hero_name}#{i}"
                self._add_card(hero, card_id, i, wanted)
            if wanted > 0:
                self._hero_counts[hero_name] = wanted

        self._refresh_layout()
        self.clear_btn.setEnabled(bool(self._hero_cards))

    def _instance_label(self, hero_name: str, index: int, total: int) -> str:
        if total <= 1:
            return ""
        return f"#{index + 1}"

    def _add_card(self, hero: dict, card_id: str, index: int, total: int):
        label = self._instance_label(hero["name"], index, total)
        card = HeroCard(hero, card_id, label, parent=self.cards_container)
        card.remove_requested.connect(self._on_remove_card)
        self._hero_cards[card_id] = card

    def _remove_card(self, card_id: str):
        card = self._hero_cards.pop(card_id, None)
        if card:
            self.cards_layout.removeWidget(card)
            card.deleteLater()

    def _on_remove_card(self, card_id: str):
        hero_name = card_id.rsplit("#", 1)[0]
        self._remove_card(card_id)

        remaining = [
            cid for cid in self._hero_cards
            if cid.rsplit("#", 1)[0] == hero_name
        ]
        count = len(remaining)
        if count == 0:
            self._hero_counts.pop(hero_name, None)
        else:
            heroes_list = self._army_heroes.get(self._current_army, [])
            hero_data   = next((h for h in heroes_list if h["name"] == hero_name), None)
            self._hero_counts[hero_name] = count
            for old_id in sorted(remaining, key=lambda c: int(c.rsplit("#",1)[1])):
                old_card = self._hero_cards.pop(old_id)
                old_card.deleteLater()
            for i in range(count):
                new_id = f"{hero_name}#{i}"
                if hero_data:
                    self._add_card(hero_data, new_id, i, count)

        self._refresh_layout()
        self.clear_btn.setEnabled(bool(self._hero_cards))

    def _refresh_layout(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if not self._hero_cards:
            self.cards_layout.addWidget(self.empty_lbl, 0, 0, 1, 2)
            self.empty_lbl.show()
            return

        self.empty_lbl.hide()
        COLS = 2
        def sort_key(cid):
            name, idx = cid.rsplit("#", 1)
            return (name.casefold(), int(idx))

        for pos, card_id in enumerate(sorted(self._hero_cards, key=sort_key)):
            card = self._hero_cards[card_id]
            r, c = divmod(pos, COLS)
            self.cards_layout.addWidget(card, r, c)

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Clear All Heroes",
            f"Remove all heroes from {self.side_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for cid in list(self._hero_cards.keys()):
                self._remove_card(cid)
            self._hero_counts.clear()
            self._refresh_layout()
            self.clear_btn.setEnabled(False)


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MESBG Hero & Casualties Tracker")
        self.resize(1240, 840)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Fetching data…")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        top = QHBoxLayout()
        icon = QLabel("⚔")
        icon.setStyleSheet(f"font-size: 26px; color: {GOLD};")
        top.addWidget(icon)

        txt = QVBoxLayout()
        t = QLabel("Middle-Earth Strategy Battle Game")
        t.setObjectName("title")
        txt.addWidget(t)
        s = QLabel("Two-sided Match Tracker – Might · Will · Fate · Wounds & Casualties")
        s.setObjectName("subtitle")
        txt.addWidget(s)
        top.addLayout(txt)
        top.addStretch()

        self.reload_btn = QPushButton("⟳  Reload Data")
        self.reload_btn.setFixedHeight(32)
        self.reload_btn.clicked.connect(self._load_data)
        top.addWidget(self.reload_btn)
        root.addLayout(top)

        sep = QFrame(); sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setChildrenCollapsible(False)

        self.side_panels = [SidePanel(0), SidePanel(1)]
        for panel in self.side_panels:
            panel.army_combo.setEnabled(False)
            splitter.addWidget(panel)

        splitter.setSizes([620, 620])
        root.addWidget(splitter, stretch=1)

    def _load_data(self):
        self.reload_btn.setEnabled(False)
        for p in self.side_panels:
            p.army_combo.setEnabled(False)
        self.statusBar().showMessage("Fetching data…")
        self._loader = DataLoader()
        self._loader.finished.connect(self._on_data_ready)
        self._loader.error.connect(self._on_data_error)
        self._loader.start()

    def _on_data_ready(self, raw: dict):
        army_names, army_heroes = parse_armies(raw)
        for panel in self.side_panels:
            panel.populate(army_names, army_heroes)
            panel._recalculate_thresholds() # trigger initial state display
        self.reload_btn.setEnabled(True)
        self.statusBar().showMessage(f"Loaded {len(army_names)} armies.  Ready.")

    def _on_data_error(self, msg: str):
        self.reload_btn.setEnabled(True)
        self.statusBar().showMessage("Error loading data.")
        QMessageBox.critical(
            self, "Network Error",
            f"Could not fetch game data:\n\n{msg}\n\n"
            "Check your internet connection and try reloading."
        )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setApplicationName("MESBG Match Tracker")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()