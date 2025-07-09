import sys
import pandas as pd
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QInputDialog, QPushButton, QLineEdit, QLabel,
    QComboBox, QSpinBox, QTextEdit, QGridLayout, QTableView,
    QAbstractItemView, QHeaderView, QStatusBar, QFrame,
    QDialog, QDialogButtonBox, QTabWidget, QCheckBox,
    QFileDialog # Added QFileDialog for save location
)
from PyQt6.QtGui import QAction, QIcon, QRegularExpressionValidator, QColor, QBrush, QKeySequence
from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QVariant, QModelIndex, pyqtSignal,
    QRegularExpression, QTimer # QTimer for temporary highlight & search debounce
)

# For plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import json # For JSON export

# --- GLOBAL CONSTANTS ---
CARD_COLORS = ["Red", "Green", "Blue", "Black", "White", "Purple", "Yellow", "Mixed (Check Notes)"]
FOIL_NORMAL_OPTIONS = ["Normal", "Foil"]
CARD_KINDS = ["Leader", "Character", "Event", "Stage", "Don Art"]
CARD_RARITIES = ["C", "UC", "R", "SR", "L", "SEC", "Promo"] # Common, Uncommon, Rare, Super Rare, Leader, Secret

DATA_FILENAME = "one_piece_cards.xlsx" # Default filename

COLUMNS = [
    "QTY",
    "Card Number",
    "Card Name",
    "Crew",
    "Color",
    "Foil / Normal",
    "Rarity",
    "Kind",
    "Alt Art",
    "Special Power",
    "Notes"
]

# --- HELPER FUNCTIONS ---
def create_card_number_validator():
    """
    Creates a validator for One Piece Card Game card numbers (e.g., ST04-001, OP01-001).
    Allows letters, then digits, hyphen, then digits.
    """
    regex = QRegularExpression(r"^[A-Za-z]+\d+-\d+$")
    return QRegularExpressionValidator(regex)

# --- DATA MANAGEMENT CLASS ---
class CardDataManager:
    def __init__(self, filename=DATA_FILENAME):
        self.filename = filename
        self.df = self._load_data()

    def _load_data(self):
        """Loads card data from an Excel file, or creates a new DataFrame if the file doesn't exist."""
        if os.path.exists(self.filename):
            try:
                df = pd.read_excel(self.filename)
                # Ensure all expected columns are present, add missing ones if necessary
                for col in COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                # Reorder columns to match COLUMNS constant
                df = df[COLUMNS]
                # Ensure 'Alt Art' is boolean type if it exists
                if 'Alt Art' in df.columns:
                    df['Alt Art'] = df['Alt Art'].astype(bool)
                return df
            except Exception as e:
                print(f"Error loading data from {self.filename}: {e}")
                QMessageBox.warning(None, "File Load Error",
                                    f"Could not load data from '{self.filename}'. It might be corrupted or in an unexpected format.\n"
                                    "A new empty collection will be started. Please check the file manually.")
                return pd.DataFrame(columns=COLUMNS)
        else:
            return pd.DataFrame(columns=COLUMNS)

    def save_data(self):
        """Saves the current DataFrame to the Excel file."""
        if not self.filename: # Should not happen if prompt_for_initial_save_location is used
            return False
        try:
            self.df.to_excel(self.filename, index=False)
            print(f"Data successfully saved to {self.filename}")
            return True
        except Exception as e:
            print(f"Error saving data to {self.filename}: {e}")
            QMessageBox.critical(None, "Save Error",
                                 f"Failed to save data to '{self.filename}'. Please check permissions or if the file is open.\n"
                                 f"Error: {e}")
            return False

    def add_card(self, card_data):
        """Adds a new card entry to the DataFrame."""
        full_card_data = {col: card_data.get(col) for col in COLUMNS}
        new_row = pd.DataFrame([full_card_data], columns=COLUMNS)
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        # Save data is now handled by the main window after successful operations
        return True

    def update_card(self, index, new_data):
        """Updates an existing card entry in the DataFrame by index."""
        if 0 <= index < len(self.df):
            for key, value in new_data.items():
                if key in self.df.columns:
                    self.df.at[index, key] = value
            # Save data is now handled by the main window after successful operations
            return True
        return False

    def delete_card(self, indices):
        """Deletes card entries from the DataFrame by a list of indices."""
        indices_to_delete = sorted(list(indices), reverse=True)
        initial_len = len(self.df)
        self.df = self.df.drop(indices_to_delete).reset_index(drop=True)
        if len(self.df) < initial_len:
            # Save data is now handled by the main window after successful operations
            return True
        return False

    def get_all_cards(self):
        """Returns the entire DataFrame."""
        return self.df

    def search_cards(self, query):
        """
        Searches the DataFrame for cards matching the query in any text-based column.
        Case-insensitive search. Optimized by targeting string columns explicitly.
        """
        if not query:
            return self.df

        query_lower = query.lower()
        
        # Identify columns that contain string data and are relevant for searching
        searchable_columns = [
            "Card Number", "Card Name", "Crew", "Color", "Foil / Normal",
            "Rarity", "Kind", "Special Power", "Notes"
        ]
        
        # Create a boolean mask for each searchable column
        masks = [
            self.df[col].astype(str).str.lower().str.contains(query_lower, na=False)
            for col in searchable_columns if col in self.df.columns
        ]
        
        if not masks:
            return pd.DataFrame(columns=COLUMNS) # No searchable columns, return empty

        # Combine masks with OR to find rows matching in any column
        combined_mask = masks[0]
        for mask in masks[1:]:
            combined_mask = combined_mask | mask

        return self.df[combined_mask]

    def find_card_by_number_name(self, card_number, card_name):
        """
        Finds existing cards by Card Number and Card Name.
        Returns a list of matching row indices.
        """
        if not card_number or not card_name:
            return []
        matches = self.df[
            (self.df["Card Number"].astype(str).str.lower() == card_number.lower()) &
            (self.df["Card Name"].astype(str).str.lower() == card_name.lower())
        ]
        return matches.index.tolist()

    def get_card_data_by_index(self, index):
        """Retrieves all data for a card at a given index as a dictionary."""
        if 0 <= index < len(self.df):
            return self.df.iloc[index].to_dict()
        return None

# --- GUI COMPONENTS ---
class PandasModel(QAbstractTableModel):
    """
    A custom model to display a Pandas DataFrame in a QTableView.
    Supports basic display, headers, and custom row highlighting.
    """
    def __init__(self, data=pd.DataFrame(columns=COLUMNS), parent=None):
        super().__init__(parent)
        self._data = data
        self._highlight_row = -1 # Row index to highlight
        self._highlight_timer = QTimer(self)
        self._highlight_timer.timeout.connect(self._clear_highlight)
        self._add_highlight_color = QColor("#d4edda") # Light green for success highlight (add)
        self._edit_highlight_color = QColor("#cce5ff") # Light blue for success highlight (edit)
        self._current_highlight_color = self._add_highlight_color

    def rowCount(self, parent=QModelIndex()):
        return len(self._data.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            value = self._data.iloc[index.row(), index.column()]
            if index.column() == COLUMNS.index("Alt Art"): # Handle boolean display
                return "Yes" if value else "No"
            return "" if pd.isna(value) else str(value)
        elif role == Qt.ItemDataRole.BackgroundRole:
            if index.row() == self._highlight_row:
                return QBrush(self._current_highlight_color)
        elif role == Qt.ItemDataRole.TextAlignmentRole: # Center align QTY
            if index.column() == COLUMNS.index("QTY"):
                return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return QVariant()

    def update_data(self, new_data):
        """Updates the model with a new DataFrame."""
        # This performs a full reset, which is good for major data changes (load/save)
        # but for filtering, directly modifying _data and emitting layoutChanged might be faster
        # However, the current filtering re-creates the entire filtered DF, so reset is simpler.
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

    def highlight_row(self, row_index, highlight_type="add", duration_ms=2000):
        """Highlights a specific row for a duration."""
        if 0 <= row_index < self.rowCount():
            self._highlight_row = row_index
            self._current_highlight_color = (
                self._add_highlight_color if highlight_type == "add" else self._edit_highlight_color
            )
            # Emit dataChanged to force redraw of the row
            self.dataChanged.emit(self.index(row_index, 0), self.index(row_index, self.columnCount() - 1))
            self._highlight_timer.start(duration_ms)

    def _clear_highlight(self):
        """Clears the highlight and redraws the row."""
        if self._highlight_row != -1:
            row_to_clear = self._highlight_row
            self._highlight_row = -1
            self.dataChanged.emit(self.index(row_to_clear, 0), self.index(row_to_clear, self.columnCount() - 1))
        self._highlight_timer.stop()


class CardTableView(QTableView):
    card_selected_for_edit = pyqtSignal(int) # Emits the index of the row to be edited

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = PandasModel()
        self.setModel(self.model)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setAlternatingRowColors(True) # For better readability of rows
        self.doubleClicked.connect(self._on_double_click)

    def set_data(self, df):
        """Sets the DataFrame to be displayed in the table."""
        self.model.update_data(df)
        self.resize_columns_to_contents()

    def resize_columns_to_contents(self):
        """Resizes columns to fit their content, with the last one stretching."""
        # Ensure that COLUMNS is used for width adjustment
        for i in range(len(COLUMNS) - 1):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Set the last column ("Notes") to stretch
        self.horizontalHeader().setSectionResizeMode(
            len(COLUMNS) - 1, QHeaderView.ResizeMode.Stretch
        )

    def get_selected_rows_indices(self):
        """Returns a list of selected row indices."""
        selected_rows = set()
        for index in self.selectionModel().selectedRows():
            # Map the proxy index to source model index if sorting is active
            source_index = self.model.mapToSource(index) if hasattr(self.model, 'mapToSource') else index
            selected_rows.add(source_index.row())
        return list(selected_rows)

    def _on_double_click(self, index):
        """Handle double-click to initiate edit."""
        if index.isValid():
            # Ensure we get the source model row index for editing
            source_index = self.model.mapToSource(index) if hasattr(self.model, 'mapToSource') else index
            self.card_selected_for_edit.emit(source_index.row())

    def highlight_added_row(self, card_data):
        """Finds and highlights the newly added row."""
        df = self.model._data # Access the actual data in the model
        try:
            # Find the index of the newly added card.
            # This is robust for finding the *last* added exact match.
            matches = df[(df["Card Number"].astype(str).str.lower() == card_data["Card Number"].lower()) &
                         (df["Card Name"].astype(str).str.lower() == card_data["Card Name"].lower())]
            if not matches.empty:
                new_row_index = matches.index.max() # Get the highest index (most recent addition)
                if pd.notna(new_row_index):
                    self.model.highlight_row(new_row_index, "add")
                    self.scrollTo(self.model.index(new_row_index, 0), QAbstractItemView.ScrollHint.PositionAtCenter)
        except Exception as e:
            print(f"Could not highlight added row: {e}")

    def highlight_updated_row(self, row_index):
        """Highlights an updated row."""
        if 0 <= row_index < self.model.rowCount():
            self.model.highlight_row(row_index, "edit")
            self.scrollTo(self.model.index(row_index, 0), QAbstractItemView.ScrollHint.PositionAtCenter)

# --- Duplicate Handling Dialog ---
class DuplicateCardDialog(QDialog):
    def __init__(self, existing_qty, new_qty, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Card Detected")
        self.setModal(True)
        self.setFixedSize(550, 300)

        layout = QVBoxLayout()
        message = QLabel(f"A card with this Card Number and Name already exists.\n"
                         f"Existing Quantity: {existing_qty}\n"
                         f"Quantity to Add: {new_qty}\n\n"
                         f"What would you like to do?")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)

        self.button_box = QDialogButtonBox()
        self.add_to_qty_button = self.button_box.addButton("Add to Quantity", QDialogButtonBox.ButtonRole.AcceptRole)
        self.add_as_new_button = self.button_box.addButton("Add as New Card", QDialogButtonBox.ButtonRole.ActionRole)
        self.cancel_button = self.button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(self.button_box)
        self.setLayout(layout)

        self.choice = None # Will store "add_qty", "add_new", or None

        self.add_to_qty_button.clicked.connect(self._set_add_to_qty)
        self.add_as_new_button.clicked.connect(self._set_add_as_new)
        self.cancel_button.clicked.connect(self.reject)

    def _set_add_to_qty(self):
        self.choice = "add_qty"
        self.accept()

    def _set_add_as_new(self):
        self.choice = "add_new"
        self.accept()

    def get_choice(self):
        return self.choice


class CardInputForm(QWidget):
    card_added = pyqtSignal(dict)
    card_updated = pyqtSignal(int, dict) # Emits index and new data
    form_cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CardInputForm")
        self.init_ui()
        self.edit_mode = False
        self.editing_row_index = -1

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QGridLayout()
        form_layout.setContentsMargins(15, 15, 15, 15) # Add more internal padding
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(12)

        self.inputs = {} # Stores input widgets for easy access

        # QTY
        qty_label = QLabel("QTY:")
        self.qty_input = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setMaximum(999)
        self.qty_input.setToolTip("Number of copies of this card you own.")
        form_layout.addWidget(qty_label, 0, 0)
        form_layout.addWidget(self.qty_input, 0, 1)
        self.inputs["QTY"] = self.qty_input

        # Card Number
        card_number_label = QLabel("Card Number:")
        self.card_number_input = QLineEdit()
        self.card_number_input.setValidator(create_card_number_validator())
        self.card_number_input.setPlaceholderText("e.g. ST04-001 or OP01-023")
        self.card_number_input.setToolTip("Unique identifier for the card (e.g., ST04-001).")
        form_layout.addWidget(card_number_label, 1, 0)
        form_layout.addWidget(self.card_number_input, 1, 1)
        self.inputs["Card Number"] = self.card_number_input

        # Card Name
        card_name_label = QLabel("Card Name:")
        self.card_name_input = QLineEdit()
        self.card_name_input.setPlaceholderText("e.g. Kaido")
        self.card_name_input.setToolTip("Full name of the card.")
        form_layout.addWidget(card_name_label, 2, 0)
        form_layout.addWidget(self.card_name_input, 2, 1)
        self.inputs["Card Name"] = self.card_name_input

        # Crew
        crew_label = QLabel("Crew:")
        self.crew_input = QLineEdit()
        self.crew_input.setPlaceholderText("e.g. Animal Kingdom Pirates")
        self.crew_input.setToolTip("The crew or affiliation of the character/leader.")
        form_layout.addWidget(crew_label, 3, 0)
        form_layout.addWidget(self.crew_input, 3, 1)
        self.inputs["Crew"] = self.crew_input

        # Color [dropdown]
        color_label = QLabel("Color:")
        self.color_dropdown = QComboBox()
        self.color_dropdown.addItems([""] + CARD_COLORS)
        self.color_dropdown.setToolTip("Main color of the card.")
        form_layout.addWidget(color_label, 4, 0)
        form_layout.addWidget(self.color_dropdown, 4, 1)
        self.inputs["Color"] = self.color_dropdown

        # Foil / Normal [dropdown]
        foil_normal_label = QLabel("Foil / Normal:")
        self.foil_normal_dropdown = QComboBox()
        self.foil_normal_dropdown.addItems([""] + FOIL_NORMAL_OPTIONS)
        self.foil_normal_dropdown.setToolTip("Is this card a foil (shiny) version or normal?")
        form_layout.addWidget(foil_normal_label, 5, 0)
        form_layout.addWidget(self.foil_normal_dropdown, 5, 1)
        self.inputs["Foil / Normal"] = self.foil_normal_dropdown

        # Rarity [dropdown]
        rarity_label = QLabel("Rarity:")
        self.rarity_dropdown = QComboBox()
        self.rarity_dropdown.addItems([""] + CARD_RARITIES)
        self.rarity_dropdown.setToolTip("Rarity of the card (C, UC, R, SR, L, SEC).")
        form_layout.addWidget(rarity_label, 6, 0)
        form_layout.addWidget(self.rarity_dropdown, 6, 1)
        self.inputs["Rarity"] = self.rarity_dropdown

        # Kind [dropdown]
        kind_label = QLabel("Kind:")
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.addItems([""] + CARD_KINDS)
        self.kind_dropdown.setToolTip("Type of card (Leader, Character, Event, Stage, Don Art).")
        form_layout.addWidget(kind_label, 7, 0)
        form_layout.addWidget(self.kind_dropdown, 7, 1)
        self.inputs["Kind"] = self.kind_dropdown

        # Alt Art [checkbox]
        alt_art_label = QLabel("Alt Art:")
        self.alt_art_checkbox = QCheckBox()
        self.alt_art_checkbox.setToolTip("Check if this card is an alternate art version.")
        form_layout.addWidget(alt_art_label, 8, 0)
        form_layout.addWidget(self.alt_art_checkbox, 8, 1)
        self.inputs["Alt Art"] = self.alt_art_checkbox

        # Special Power (using QTextEdit for multi-line)
        special_power_label = QLabel("Special Power:")
        self.special_power_input = QTextEdit()
        self.special_power_input.setPlaceholderText("e.g. [Activate: Main] [Once Per Turn] Give this Leader or 1 of your Characters up to 1 rested DON!! card.")
        self.special_power_input.setMinimumHeight(60)
        self.special_power_input.setToolTip("Detailed text for the card's special abilities.")
        form_layout.addWidget(special_power_label, 9, 0)
        form_layout.addWidget(self.special_power_input, 9, 1)
        self.inputs["Special Power"] = self.special_power_input

        # Notes
        notes_label = QLabel("Notes:")
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Any personal notes about the card (e.g., condition, purchase date).")
        self.notes_input.setMinimumHeight(40)
        form_layout.addWidget(notes_label, 10, 0)
        form_layout.addWidget(self.notes_input, 10, 1)
        self.inputs["Notes"] = self.notes_input

        # Action Buttons
        button_layout = QVBoxLayout()
        self.submit_button = QPushButton("Add Card to Collection")
        self.submit_button.clicked.connect(self._handle_submit)
        self.submit_button.setProperty("class", "submitButton") # Common class for styling

        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        self.clear_button.setProperty("class", "clearButton")

        self.cancel_edit_button = QPushButton("Cancel Edit")
        self.cancel_edit_button.clicked.connect(self.cancel_edit_mode)
        self.cancel_edit_button.setProperty("class", "cancelButton")
        self.cancel_edit_button.setVisible(False) # Initially hidden

        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.cancel_edit_button) # Add it to the layout, but keep hidden
        button_layout.addWidget(self.clear_button)


        main_layout.addLayout(form_layout)
        main_layout.addStretch(1) # Pushes buttons to the bottom
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def get_card_data(self):
        """Collects data from all input fields."""
        data = {}
        for col in COLUMNS:
            if col == "QTY":
                data[col] = self.qty_input.value()
            elif col in ["Color", "Foil / Normal", "Rarity", "Kind"]:
                # Use currentText() and ensure it's not empty, otherwise None/empty string
                text = self.inputs[col].currentText().strip()
                data[col] = text if text else None
            elif col == "Alt Art":
                data[col] = self.alt_art_checkbox.isChecked()
            elif col in ["Special Power", "Notes"]:
                text = self.inputs[col].toPlainText().strip()
                data[col] = text if text else None
            else: # For QLineEdit
                text = self.inputs[col].text().strip()
                data[col] = text if text else None
        return data

    def set_card_data(self, card_data):
        """Populates the input fields with given card data."""
        self.qty_input.setValue(card_data.get("QTY", 1) or 1) # Handle None or 0 QTY
        self.card_number_input.setText(card_data.get("Card Number", "") or "")
        self.card_name_input.setText(card_data.get("Card Name", "") or "")
        self.crew_input.setText(card_data.get("Crew", "") or "")
        self.color_dropdown.setCurrentText(card_data.get("Color", "") or "")
        self.foil_normal_dropdown.setCurrentText(card_data.get("Foil / Normal", "") or "")
        self.rarity_dropdown.setCurrentText(card_data.get("Rarity", "") or "")
        self.kind_dropdown.setCurrentText(card_data.get("Kind", "") or "")
        self.alt_art_checkbox.setChecked(card_data.get("Alt Art", False)) # Set checkbox state
        self.special_power_input.setText(card_data.get("Special Power", "") or "")
        self.notes_input.setText(card_data.get("Notes", "") or "")

    def validate_input(self, card_data):
        """Performs basic validation on the collected card data and applies visual feedback."""
        is_valid = True
        # Reset styles for all inputs
        for widget in self.inputs.values():
            if isinstance(widget, (QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox)):
                widget.setStyleSheet("") # Clear any previous error styles

        if not card_data["Card Number"]:
            QMessageBox.warning(self.parentWidget(), "Validation Error", "Card Number cannot be empty.")
            self.card_number_input.setStyleSheet("border: 2px solid #dc3545;") # Red border
            self.card_number_input.setFocus()
            is_valid = False
        else:
            validator_state = self.card_number_input.validator().validate(card_data["Card Number"], 0)[0]
            if validator_state != QRegularExpressionValidator.State.Acceptable:
                QMessageBox.warning(self.parentWidget(), "Validation Error", "Invalid Card Number format (e.g., ST04-001, OP01-023).")
                self.card_number_input.setStyleSheet("border: 2px solid #dc3545;")
                self.card_number_input.setFocus()
                is_valid = False

        if is_valid and not card_data["Card Name"]:
            QMessageBox.warning(self.parentWidget(), "Validation Error", "Card Name cannot be empty.")
            self.card_name_input.setStyleSheet("border: 2px solid #dc3545;")
            self.card_name_input.setFocus()
            is_valid = False

        if is_valid and card_data["QTY"] <= 0:
            QMessageBox.warning(self.parentWidget(), "Validation Error", "Quantity must be at least 1.")
            self.qty_input.setStyleSheet("border: 2px solid #dc3545;")
            self.qty_input.setFocus()
            is_valid = False

        return is_valid

    def _handle_submit(self):
        """Routes the submit action based on current mode (add or edit)."""
        card_data = self.get_card_data()
        if not self.validate_input(card_data):
            return # Validation message already shown

        if self.edit_mode:
            self.card_updated.emit(self.editing_row_index, card_data)
        else:
            self.card_added.emit(card_data) # Let parent handle duplicate check

    def clear_form(self):
        """Clears all input fields in the form and exits edit mode."""
        self.qty_input.setValue(1)
        self.card_number_input.clear()
        self.card_name_input.clear()
        self.crew_input.clear()
        self.color_dropdown.setCurrentIndex(0)
        self.foil_normal_dropdown.setCurrentIndex(0)
        self.rarity_dropdown.setCurrentIndex(0)
        self.kind_dropdown.setCurrentIndex(0)
        self.alt_art_checkbox.setChecked(False) # Clear alt art checkbox
        self.special_power_input.clear()
        self.notes_input.clear()
        # Clear any error styles
        for widget in self.inputs.values():
            if isinstance(widget, (QLineEdit, QTextEdit, QComboBox, QSpinBox, QCheckBox)):
                widget.setStyleSheet("")
        self.form_cleared.emit()
        self.exit_edit_mode() # Always exit edit mode on clear

    def enter_edit_mode(self, card_data, row_index):
        """Sets the form to edit mode and populates with card data."""
        self.edit_mode = True
        self.editing_row_index = row_index
        self.submit_button.setText("Update Card")
        self.submit_button.setProperty("class", "updateButton") # New class for styling
        self.cancel_edit_button.setVisible(True)
        self.clear_button.setVisible(False) # Hide clear button in edit mode, use cancel instead
        self.set_card_data(card_data)
        self.card_number_input.setFocus() # Bring focus to the first field

    def exit_edit_mode(self):
        """Resets the form to add mode."""
        self.edit_mode = False
        self.editing_row_index = -1
        self.submit_button.setText("Add Card to Collection")
        self.submit_button.setProperty("class", "submitButton") # Reset class
        self.cancel_edit_button.setVisible(False)
        self.clear_button.setVisible(True) # Show clear button again

        # Re-apply stylesheet to ensure button class change is rendered
        self.submit_button.style().polish(self.submit_button)


    def cancel_edit_mode(self):
        """Clears form and exits edit mode."""
        self.clear_form() # This also calls exit_edit_mode
        if self.parentWidget():
            self.parentWidget().statusBar().showMessage("Edit cancelled. Form cleared.", 2000)

class ShortcutsDialog(QDialog):
    """A small, non-modal dialog to display shortcuts."""
    def __init__(self, parent=None, is_temporary=True):
        super().__init__(parent)
        self.is_temporary = is_temporary
        self.setWindowTitle("Keyboard Shortcuts")
        if is_temporary:
            self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) # Does not take focus
        else:
            # For persistent dialog opened via menu
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint) # Remove ? button
            self.setModal(False) # Non-modal so user can still interact with main window

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        shortcuts = [
            ("Ctrl+S", "Save Collection"),
            ("Ctrl+R", "Reload Collection"),
            ("Ctrl+F", "Focus Search Bar"),
            ("Ctrl+A", "Add Card"),
            ("Delete", "Delete Selected Card(s)"),
            ("Double Click Row", "Edit Card"),
            ("Ctrl+H", "Show Quick Shortcuts Window")
        ]

        for shortcut, desc in shortcuts:
            label = QLabel(f"<b>{shortcut}:</b> {desc}")
            layout.addWidget(label)

        if not is_temporary:
            # Add a close button for the persistent dialog
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.accepted.connect(self.accept)
            layout.addWidget(button_box)

        self.setLayout(layout)
        self.adjustSize() # Adjust size based on content

class StatisticsWidget(QWidget):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._current_df = pd.DataFrame(columns=COLUMNS) # Store the currently displayed data
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Filters for statistics
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter Stats By:"))

        self.color_filter_dropdown = QComboBox()
        self.color_filter_dropdown.addItems(["All Colors"] + CARD_COLORS)
        self.color_filter_dropdown.currentIndexChanged.connect(self.update_statistics)
        filter_layout.addWidget(self.color_filter_dropdown)

        self.rarity_filter_dropdown = QComboBox()
        self.rarity_filter_dropdown.addItems(["All Rarities"] + CARD_RARITIES)
        self.rarity_filter_dropdown.currentIndexChanged.connect(self.update_statistics)
        filter_layout.addWidget(self.rarity_filter_dropdown)

        self.kind_filter_dropdown = QComboBox()
        self.kind_filter_dropdown.addItems(["All Kinds"] + CARD_KINDS)
        self.kind_filter_dropdown.currentIndexChanged.connect(self.update_statistics)
        filter_layout.addWidget(self.kind_filter_dropdown)

        self.alt_art_filter_checkbox = QCheckBox("Only Alt Art")
        self.alt_art_filter_checkbox.stateChanged.connect(self.update_statistics)
        filter_layout.addWidget(self.alt_art_filter_checkbox)

        self.reset_filters_button = QPushButton("Reset Filters")
        self.reset_filters_button.clicked.connect(self._reset_filters)
        filter_layout.addWidget(self.reset_filters_button)

        filter_layout.addStretch(1)
        main_layout.addLayout(filter_layout)

        # Statistics Display Area
        stats_display_layout = QGridLayout()
        main_layout.addLayout(stats_display_layout)

        self.total_cards_label = QLabel("<b>Total Cards:</b> 0")
        self.unique_cards_label = QLabel("<b>Unique Card Entries:</b> 0")
        self.alt_art_count_label = QLabel("<b>Alt Art Cards:</b> 0")

        stats_display_layout.addWidget(self.total_cards_label, 0, 0)
        stats_display_layout.addWidget(self.unique_cards_label, 0, 1)
        stats_display_layout.addWidget(self.alt_art_count_label, 0, 2)
        stats_display_layout.setColumnStretch(3, 1) # Stretch to push labels to left

        # Matplotlib Canvas for charts
        self.figure_rarity = plt.figure(figsize=(5, 3))
        self.canvas_rarity = FigureCanvasQTAgg(self.figure_rarity)
        self.toolbar_rarity = NavigationToolbar2QT(self.canvas_rarity, self)
        self.ax_rarity = self.figure_rarity.add_subplot(111)

        self.figure_color = plt.figure(figsize=(5, 3))
        self.canvas_color = FigureCanvasQTAgg(self.figure_color)
        self.toolbar_color = NavigationToolbar2QT(self.canvas_color, self)
        self.ax_color = self.figure_color.add_subplot(111)

        self.figure_kind = plt.figure(figsize=(5, 3))
        self.canvas_kind = FigureCanvasQTAgg(self.figure_kind)
        self.toolbar_kind = NavigationToolbar2QT(self.canvas_kind, self)
        self.ax_kind = self.figure_kind.add_subplot(111)

        chart_layout = QHBoxLayout()
        chart_layout.addWidget(self.canvas_rarity)
        chart_layout.addWidget(self.canvas_color)
        chart_layout.addWidget(self.canvas_kind)
        main_layout.addLayout(chart_layout)

        # Create and add toolbars for each canvas
        self.toolbar_rarity = NavigationToolbar2QT(self.canvas_rarity, self)
        self.toolbar_color = NavigationToolbar2QT(self.canvas_color, self)
        self.toolbar_kind = NavigationToolbar2QT(self.canvas_kind, self)

        # Toolbar layout to place them under their respective graphs
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addWidget(self.toolbar_rarity)
        toolbar_layout.addWidget(self.toolbar_color)
        toolbar_layout.addWidget(self.toolbar_kind)
        main_layout.addLayout(toolbar_layout) # Add the toolbar layout to the main layout

        # Apply stylesheet to make toolbar buttons black
        toolbar_stylesheet = """
            NavigationToolbar2QT QToolButton {
                background-color: #333333; /* Dark background for the button */
                color: #FFFFFF; /* White text/icon color for contrast */
                border: 1px solid #555555; /* Slightly lighter border */
                border-radius: 4px;
                padding: 4px;
            }
            NavigationToolbar2QT QToolButton:hover {
                background-color: #555555; /* Darker on hover */
            }
            NavigationToolbar2QT QToolButton:pressed {
                background-color: #111111; /* Even darker when pressed */
            }
        """
        self.toolbar_rarity.setStyleSheet(toolbar_stylesheet)
        self.toolbar_color.setStyleSheet(toolbar_stylesheet)
        self.toolbar_kind.setStyleSheet(toolbar_stylesheet)


        main_layout.addStretch(1) # Push content to top

    def set_data(self, df):
        self._current_df = df
        self.update_statistics()

    def _reset_filters(self):
        self.color_filter_dropdown.setCurrentIndex(0)
        self.rarity_filter_dropdown.setCurrentIndex(0)
        self.kind_filter_dropdown.setCurrentIndex(0)
        self.alt_art_filter_checkbox.setChecked(False)

    def update_statistics(self):
        df_filtered = self._current_df.copy()

        selected_color = self.color_filter_dropdown.currentText()
        if selected_color != "All Colors":
            df_filtered = df_filtered[df_filtered["Color"] == selected_color]

        selected_rarity = self.rarity_filter_dropdown.currentText()
        if selected_rarity != "All Rarities":
            df_filtered = df_filtered[df_filtered["Rarity"] == selected_rarity]

        selected_kind = self.kind_filter_dropdown.currentText()
        if selected_kind != "All Kinds":
            df_filtered = df_filtered[df_filtered["Kind"] == selected_kind]

        if self.alt_art_filter_checkbox.isChecked():
            df_filtered = df_filtered[df_filtered["Alt Art"] == True]

        # Calculate statistics
        total_cards_qty = df_filtered["QTY"].sum()
        unique_card_entries = len(df_filtered)
        alt_art_count = df_filtered["Alt Art"].sum() # True counts as 1

        self.total_cards_label.setText(f"<b>Total Cards (QTY):</b> {total_cards_qty}")
        self.unique_cards_label.setText(f"<b>Unique Card Entries:</b> {unique_card_entries}")
        self.alt_art_count_label.setText(f"<b>Alt Art Cards:</b> {alt_art_count}")

        # Update Rarity Chart
        self.ax_rarity.clear()
        rarity_counts = df_filtered.groupby("Rarity")["QTY"].sum().reindex(CARD_RARITIES, fill_value=0)
        if not rarity_counts.empty:
            self.ax_rarity.bar(rarity_counts.index, rarity_counts.values, color='skyblue')
        self.ax_rarity.set_title("Cards by Rarity")
        self.ax_rarity.set_ylabel("Total Quantity")
        self.figure_rarity.tight_layout() # Ensure tight layout
        self.canvas_rarity.draw()

        # Update Color Chart (Pie Chart)
        self.ax_color.clear()
        color_counts = df_filtered.groupby("Color")["QTY"].sum()
        if not color_counts.empty:
            wedges, texts, autotexts = self.ax_color.pie(color_counts.values, labels=color_counts.index, autopct='%1.1f%%', startangle=90,
                                                       pctdistance=0.85, textprops={'fontsize': 8})
            self.ax_color.set_title("Cards by Color")
            self.ax_color.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
            for autotext in autotexts:
                autotext.set_color('white')
            for text in texts:
                text.set_color('black')
        else:
            self.ax_color.text(0.5, 0.5, "No data", horizontalalignment='center', verticalalignment='center', transform=self.ax_color.transAxes)
            self.ax_color.set_title("Cards by Color")

        self.figure_color.tight_layout() # Ensure tight layout
        self.canvas_color.draw()

        # Update Kind Chart
        self.ax_kind.clear()
        kind_counts = df_filtered.groupby("Kind")["QTY"].sum().reindex(CARD_KINDS, fill_value=0)
        if not kind_counts.empty:
            self.ax_kind.bar(kind_counts.index, kind_counts.values, color='lightcoral')
        self.ax_kind.set_title("Cards by Kind")
        self.ax_kind.set_ylabel("Total Quantity")
        self.ax_kind.tick_params(axis='x', rotation=45) # Rotate x labels for better readability
        self.figure_kind.tight_layout() # Ensure tight layout
        self.canvas_kind.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_manager = CardDataManager()
        self.setWindowTitle("One Piece Card Game Collection Tracker")
        self.setGeometry(100, 100, 1400, 900) # Initial window size (larger for tabs)

        # --- Set Application and Window Icon ---
        # For the .exe application icon (usually set during packaging, e.g., with PyInstaller)
        # You'd typically use a .ico file for Windows, or .icns for macOS.
        # Example for PyInstaller: pyinstaller --icon=app_logo.ico your_script.py

        # For the application window icon (displayed in title bar, taskbar)
        # Replace 'path/to/your/window_icon.png' with your actual icon file path
        # self.setWindowIcon(QIcon('path/to/your/window_icon.png'))


        self.quick_shortcuts_dialog = ShortcutsDialog(self, is_temporary=True) # For 'H' key
        self.quick_shortcuts_dialog.hide()

        self.persistent_shortcuts_dialog = ShortcutsDialog(self, is_temporary=False) # For Ctrl+H / menu
        self.persistent_shortcuts_dialog.hide()


        self.init_ui()

        # Initial check for new collection/file
        initial_file_exists = os.path.exists(self.data_manager.filename)
        if self.data_manager.df.empty and not initial_file_exists:
            self.prompt_for_initial_save_location()

        self.load_data_into_table()
        self.update_statistics_tab() # Initial update for stats tab

        # Set up search debounce timer
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # 300 ms debounce delay
        self.search_timer.timeout.connect(self._perform_debounced_search)
        self.search_input.textChanged.connect(self.search_timer.start) # Start timer on text change

    def init_ui(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready to track your One Piece cards!")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Tab 1: Card Collection ---
        collection_tab = QWidget()
        collection_layout = QHBoxLayout(collection_tab)
        collection_layout.setContentsMargins(15, 15, 15, 15) # More padding for the main layout
        collection_layout.setSpacing(20) # More spacing between left and right panels

        # Left side: Input Form
        self.input_form = CardInputForm(self) # Pass self as parent for message boxes
        self.input_form.card_added.connect(self._handle_card_added)
        self.input_form.card_updated.connect(self._handle_card_updated)
        collection_layout.addWidget(self.input_form, 2) # Give it 2/5 of the width

        # Vertical separator line (visual enhancement)
        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.Shape.VLine)
        separator_line.setFrameShadow(QFrame.Shadow.Sunken)
        collection_layout.addWidget(separator_line)

        # Right side: Table View, Search, and Table Actions
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(0, 0, 0, 0) # No extra padding here, main_layout handles it
        right_panel_layout.setSpacing(10)

        # Search Bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setToolTip("Type to filter cards by any text field.")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Card Number, Name, Crew, etc.")
        # self.search_input.textChanged.connect(self.filter_table) # Connected to timer now
        self.search_input.setToolTip("Enter keywords to filter the card list.")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        right_panel_layout.addLayout(search_layout)

        # Card Table View
        self.card_table_view = CardTableView()
        self.card_table_view.card_selected_for_edit.connect(self.edit_selected_card)
        right_panel_layout.addWidget(self.card_table_view, 1) # Take remaining vertical space

        # Table Action Buttons
        table_button_layout = QHBoxLayout()
        table_button_layout.setSpacing(10)

        self.edit_button = QPushButton("Edit Selected Card")
        # Connect to a lambda that calls with get_selected_rows_indices() to ensure it's always a list
        self.edit_button.clicked.connect(lambda: self.edit_selected_card(self.card_table_view.get_selected_rows_indices()))
        self.edit_button.setProperty("class", "editButton")
        self.edit_button.setToolTip("Populate the form with details of the selected card for editing (select only one).")

        self.delete_button = QPushButton("Delete Selected Card(s)")
        self.delete_button.clicked.connect(self.delete_selected_cards)
        self.delete_button.setProperty("class", "deleteButton")
        self.delete_button.setToolTip("Permanently delete selected card(s) from your collection.")

        self.save_button = QPushButton("Manual Save")
        self.save_button.clicked.connect(self._manual_save_data)
        self.save_button.setProperty("class", "saveButton")
        self.save_button.setToolTip(f"Manually save your collection to '{DATA_FILENAME}'.")

        table_button_layout.addWidget(self.edit_button)
        table_button_layout.addWidget(self.delete_button)
        table_button_layout.addStretch(1) # Pushes save button to the right
        table_button_layout.addWidget(self.save_button)
        right_panel_layout.addLayout(table_button_layout)

        collection_layout.addLayout(right_panel_layout, 3) # Give it 3/5 of the width
        self.tab_widget.addTab(collection_tab, "Card Collection")

        # --- Tab 2: Statistics and Graphs ---
        self.statistics_widget = StatisticsWidget(self.data_manager, self)
        self.tab_widget.addTab(self.statistics_widget, "Collection Statistics")

        self._create_menu_bar()
        self.tab_widget.currentChanged.connect(self._on_tab_changed)


    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        save_action = QAction("&Save Collection", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setStatusTip("Save current collection to Excel")
        save_action.triggered.connect(self._manual_save_data)
        file_menu.addAction(save_action)

        load_action = QAction("&Reload Collection", self)
        load_action.setShortcut(QKeySequence("Ctrl+R"))
        load_action.setStatusTip("Reload collection from Excel (discards unsaved changes)")
        load_action.triggered.connect(self.confirm_reload_data)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        export_csv_action = QAction("Export as &CSV...", self)
        export_csv_action.setStatusTip("Export current collection (or filtered view) to a CSV file")
        export_csv_action.triggered.connect(self.export_as_csv)
        file_menu.addAction(export_csv_action)

        export_json_action = QAction("Export as &JSON...", self)
        export_json_action.setStatusTip("Export current collection (or filtered view) to a JSON file")
        export_json_action.triggered.connect(self.export_as_json)
        file_menu.addAction(export_json_action)

        file_menu.addSeparator() # Separator for clarity

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")
        add_card_action = QAction("&Add New Card", self)
        add_card_action.setShortcut(QKeySequence("Ctrl+A"))
        add_card_action.setStatusTip("Clear the form and prepare to add a new card")
        add_card_action.triggered.connect(self.input_form.clear_form)
        edit_menu.addAction(add_card_action)

        focus_search_action = QAction("&Focus Search", self)
        focus_search_action.setShortcut(QKeySequence("Ctrl+F"))
        focus_search_action.setStatusTip("Move focus to the search bar")
        focus_search_action.triggered.connect(self.search_input.setFocus)
        edit_menu.addAction(focus_search_action)

        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        shortcuts_action = QAction("&Shortcuts", self)
        shortcuts_action.setShortcut(QKeySequence("Ctrl+H"))
        shortcuts_action.triggered.connect(self._show_persistent_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)

    def prompt_for_initial_save_location(self):
        """Prompts the user to choose a save location for the initial data file."""
        self.statusBar.showMessage("No collection file found. Please choose a location to save your new collection.", 5000)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save New Collection File",
            os.path.join(os.getcwd(), "one_piece_cards.xlsx"),
            "Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            self.data_manager.filename = file_path
            if not file_path.lower().endswith(".xlsx"):
                self.data_manager.filename += ".xlsx"
            self._manual_save_data() # Save the empty DataFrame to the new location
            self.statusBar.showMessage(f"New collection file created at: {self.data_manager.filename}", 5000)
        else:
            self.statusBar.showMessage("No file location selected. Data will not be saved automatically.", 5000)


    def load_data_into_table(self):
        """Loads data from the data manager and displays it in the table view."""
        current_df = self.data_manager.get_all_cards()
        self.card_table_view.set_data(current_df)
        self.statusBar.showMessage(f"Collection loaded. Total unique card entries: {len(current_df)}", 3000)
        self.update_statistics_tab()


    def _handle_card_added(self, card_data):
        """Slot to handle new card data emitted from the input form, including duplicate check."""
        matching_indices = self.data_manager.find_card_by_number_name(
            card_data["Card Number"], card_data["Card Name"]
        )

        if matching_indices:
            # Duplicate found, prompt user
            dialog = DuplicateCardDialog(
                existing_qty=self.data_manager.get_all_cards().iloc[matching_indices[0]]["QTY"],
                new_qty=card_data["QTY"],
                parent=self
            )
            result = dialog.exec() # Show the dialog
            choice = dialog.get_choice()

            if result == QDialog.DialogCode.Accepted:
                if choice == "add_qty":
                    # Add to quantity of the first matching card
                    first_match_index = matching_indices[0]
                    existing_card = self.data_manager.get_card_data_by_index(first_match_index)
                    if existing_card:
                        existing_card["QTY"] = (existing_card["QTY"] or 0) + card_data["QTY"] # Handle None existing QTY
                        if self.data_manager.update_card(first_match_index, existing_card):
                            self._manual_save_data() # Save after successful data manager operation
                            self.load_data_into_table() # Reloads data and updates table
                            self.filter_table() # Re-apply filter in case search is active
                            self.card_table_view.highlight_updated_row(first_match_index)
                            self.statusBar.showMessage(f"Quantity for '{card_data['Card Name']}' updated successfully!", 3000)
                            self.input_form.clear_form()
                            self.update_statistics_tab()
                        else:
                            self.statusBar.showMessage("Failed to update card quantity.", 3000)
                elif choice == "add_new":
                    # Add as a completely new card
                    if self.data_manager.add_card(card_data):
                        self._manual_save_data() # Save after successful data manager operation
                        self.load_data_into_table()
                        self.filter_table()
                        self.card_table_view.highlight_added_row(card_data)
                        self.statusBar.showMessage("New card added successfully!", 3000)
                        self.input_form.clear_form()
                        self.update_statistics_tab()
                    else:
                        self.statusBar.showMessage("Failed to add new card.", 3000)
            else: # User cancelled
                self.statusBar.showMessage("Card addition cancelled.", 2000)
        else:
            # No duplicate, just add the card
            if self.data_manager.add_card(card_data):
                self._manual_save_data() # Save after successful data manager operation
                self.load_data_into_table() # Reloads data and updates table
                self.filter_table() # Re-apply filter in case search is active
                self.card_table_view.highlight_added_row(card_data) # Highlight the new row
                self.statusBar.showMessage("Card added successfully!", 3000)
                self.input_form.clear_form()
                self.update_statistics_tab()
            else:
                self.statusBar.showMessage("Failed to add card. Please check input.", 3000)


    def _handle_card_updated(self, row_index, new_data):
        """Slot to handle updated card data emitted from the input form."""
        if self.data_manager.update_card(row_index, new_data):
            self._manual_save_data() # Save after successful data manager operation
            self.load_data_into_table()
            self.filter_table()
            self.card_table_view.highlight_updated_row(row_index)
            self.statusBar.showMessage("Card updated successfully!", 3000)
            self.input_form.clear_form() # Also exits edit mode
            self.update_statistics_tab()
        else:
            QMessageBox.critical(self, "Update Failed", "Could not update card information.")
            self.statusBar.showMessage("Card update failed.", 3000)

    def edit_selected_card(self, row_indices_or_single_index):
        """
        Populates the input form with data from the selected card for editing.
        Can be called by button (list of indices) or double-click (single index).
        """
        # Ensure selected_indices is always a list for consistent processing
        if isinstance(row_indices_or_single_index, int):
            selected_indices = [row_indices_or_single_index]
        else:
            selected_indices = row_indices_or_single_index

        if len(selected_indices) != 1:
            QMessageBox.warning(self, "Edit Error", "Please select exactly one card to edit.")
            self.statusBar.showMessage("Select a single card to edit.", 2000)
            return

        row_index = selected_indices[0]
        card_data = self.data_manager.get_card_data_by_index(row_index)
        if card_data:
            self.input_form.enter_edit_mode(card_data, row_index)
            self.statusBar.showMessage(f"Editing card: {card_data.get('Card Name', '')}", 3000)
        else:
            QMessageBox.critical(self, "Edit Error", "Could not retrieve card data for editing.")
            self.statusBar.showMessage("Error retrieving card data.", 2000)


    def delete_selected_cards(self):
        """Deletes selected rows from the table and updates the data manager."""
        selected_indices = self.card_table_view.get_selected_rows_indices()
        if not selected_indices:
            QMessageBox.warning(self, "No Selection", "Please select at least one card to delete.")
            self.statusBar.showMessage("No cards selected for deletion.", 2000)
            return

        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_indices)} selected card(s)? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if self.data_manager.delete_card(selected_indices):
                self._manual_save_data() # Save after successful data manager operation
                self.statusBar.showMessage(f"{len(selected_indices)} card(s) deleted.", 3000)
                self.load_data_into_table()
                self.filter_table()
                self.input_form.exit_edit_mode() # Exit edit mode if edited card was deleted
                self.update_statistics_tab()
            else:
                QMessageBox.critical(self, "Deletion Failed", "Could not delete card(s).")
                self.statusBar.showMessage("Deletion failed.", 3000)

    def _perform_debounced_search(self):
        """Called by QTimer after a short delay to perform the actual search."""
        self.filter_table()

    def filter_table(self):
        """Filters the table based on the search input."""
        query = self.search_input.text().strip()
        filtered_df = self.data_manager.search_cards(query)
        self.card_table_view.set_data(filtered_df)
        self.statusBar.showMessage(f"Filtered results: {len(filtered_df)} cards found.", 2000)
        self.update_statistics_tab(filtered_df) # Update stats based on filtered data

    def _on_tab_changed(self, index):
        """Called when the tab changes."""
        if self.tab_widget.tabText(index) == "Collection Statistics":
            self.update_statistics_tab() # Ensure stats are fresh when tab is opened

    def update_statistics_tab(self, df=None):
        """Updates the statistics tab with current (or filtered) data."""
        if df is None:
            # If no dataframe is passed, use the full current data from data_manager
            df = self.data_manager.get_all_cards()
            # If a search query is active, apply it to the data used for stats
            current_search_query = self.search_input.text().strip()
            if current_search_query:
                df = self.data_manager.search_cards(current_search_query)

        self.statistics_widget.set_data(df)


    def _manual_save_data(self):
        """Wrapper for data_manager.save_data to provide status bar feedback."""
        if self.data_manager.save_data():
            self.statusBar.showMessage(f"Collection saved to '{self.data_manager.filename}'", 3000)
            return True
        else:
            self.statusBar.showMessage(f"Failed to save collection to '{self.data_manager.filename}'", 3000)
            return False


    def confirm_reload_data(self):
        """Prompts user to confirm reloading data from file."""
        confirm = QMessageBox.question(
            self, "Confirm Reload",
            "Are you sure you want to reload the collection from file? Any unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            # Re-initialize data manager to ensure fresh load from potentially changed file
            self.data_manager = CardDataManager(self.data_manager.filename) # Use current filename
            self.load_data_into_table()
            self.search_input.clear()
            self.input_form.clear_form() # Also exits edit mode
            self.statusBar.showMessage("Collection reloaded from file.", 3000)
            self.update_statistics_tab()


    def export_as_csv(self):
        """Exports the current data (or filtered view) to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            os.path.join(os.getcwd(), "exported_one_piece_cards.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"
            try:
                # Export the currently displayed (filtered) data if search is active
                current_df_in_table = self.card_table_view.model._data
                current_df_in_table.to_csv(file_path, index=False)
                self.statusBar.showMessage(f"Collection exported to '{file_path}'", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to CSV: {e}")
                self.statusBar.showMessage("CSV export failed.", 3000)

    def export_as_json(self):
        """Exports the current data (or filtered view) to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to JSON",
            os.path.join(os.getcwd(), "exported_one_piece_cards.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            if not file_path.lower().endswith(".json"):
                file_path += ".json"
            try:
                # Export the currently displayed (filtered) data if search is active
                current_df_in_table = self.card_table_view.model._data
                # Convert DataFrame to list of dictionaries (records format) for JSON
                current_df_in_table.to_json(file_path, orient="records", indent=4)
                self.statusBar.showMessage(f"Collection exported to '{file_path}'", 5000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to JSON: {e}")
                self.statusBar.showMessage("JSON export failed.", 3000)


    def show_about_dialog(self):
        """Displays the about dialog."""
        QMessageBox.about(
            self,
            "About One Piece Card Tracker",
            "This is a simple application to help you track your One Piece Card Game Collection.\n\n"
            "Developed with Python and PyQt6.\n\n"
            "Version: 1.0.1" # Updated version number
        )

    def _show_persistent_shortcuts_dialog(self):
        """Shows the persistent shortcuts dialog (from menu/Ctrl+H)."""
        if self.persistent_shortcuts_dialog.isHidden():
            # Position it centrally or relative to main window
            self.persistent_shortcuts_dialog.move(self.geometry().center() - self.persistent_shortcuts_dialog.rect().center())
            self.persistent_shortcuts_dialog.show()
        else:
            self.persistent_shortcuts_dialog.hide() # Toggle visibility

    def keyPressEvent(self, event):
        """Handle key press events for global shortcuts and 'H' key for quick shortcuts dialog."""
        if event.key() == Qt.Key.Key_H and not event.isAutoRepeat():
            if self.quick_shortcuts_dialog.isHidden():
                # Position it centrally or relative to main window
                self.quick_shortcuts_dialog.move(self.geometry().center() - self.quick_shortcuts_dialog.rect().center())
                self.quick_shortcuts_dialog.show()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected_cards()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events for 'H' key to hide quick shortcuts dialog."""
        if event.key() == Qt.Key.Key_H and not event.isAutoRepeat():
            self.quick_shortcuts_dialog.hide()
        else:
            super().keyReleaseEvent(event)

    def closeEvent(self, event):
        """Overrides the close event to prompt for saving."""
        reply = QMessageBox.question(
            self, "Save on Exit?",
            "Do you want to save your changes before exiting?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Save:
            if self._manual_save_data(): # Use the wrapper function to save and get status
                event.accept()
            else:
                # If save failed, do not close the application
                QMessageBox.critical(self, "Save Error", "Failed to save data. Aborting exit.")
                event.ignore()
        elif reply == QMessageBox.StandardButton.Discard:
            event.accept()
        else:
            event.ignore()

# --- QSS STYLING (Embedded) ---
QSS_STYLE = """
/* General Window Styling */
QMainWindow {
    background-color: #f0f2f5; /* Lighter background for a modern feel */
}

/* Labels */
QLabel {
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 14px;
    color: #34495e; /* Darker blue-grey for labels */
    padding: 2px;
}

/* Line Edits, Text Edits, Spin Boxes, Combo Boxes - General Input Styling */
QLineEdit, QTextEdit, QSpinBox, QComboBox {
    border: 1px solid #dcdfe6; /* Light grey-blue border */
    border-radius: 6px; /* Slightly more rounded corners */
    padding: 8px 10px; /* More padding for better touch/click targets */
    background-color: #ffffff; /* White background */
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 14px;
    color: #333333; /* Explicitly set text color to dark grey */
    min-height: 28px; /* Ensure consistent height for single-line inputs */
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 2px solid #409eff; /* Brighter blue border on focus */
    background-color: #f0faff; /* Very light blue background on focus */
    outline: none; /* Remove default focus outline */
}

QLineEdit::placeholder-text, QTextEdit::placeholder-text {
    color: #909399; /* Medium grey for placeholder text */
}

/* QComboBox specific adjustments */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px; /* Wider dropdown arrow area */
    border-left-width: 1px;
    border-left-color: #dcdfe6;
    border-left-style: solid;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
QComboBox::down-arrow {
    /* Base64 encoded SVG for a clearer, modern arrow */
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDE2IDE2Ij48cGF0aCBmaWxsPSIjNTA1NzYzIiBkPSJNOC4wMiA5LjgyNWwtNC45LTQuOWwtLjcwNy43MDhMNy41OCA5LjgyNWwxLjQxNC0xLjQxNGwtLjcwNy0uNzA3eiIvPjxwYXRoIGZpbGw9IiM1MDU3NjMiIGQ9Ik03LjU4IDkuODI1bDQuOSA0LjlsLjcwNy0uNzA4TDE1LjI1IDkuODI1bDAtMi44MThMNy41OCA5LjgyNXoiLz48L3N2Zz4=);
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    border: 1px solid #c0c4cc; /* Slightly darker border for dropdown list */
    selection-background-color: #409eff; /* Blue selection */
    selection-color: white; /* White text on blue selection */
    background-color: #ffffff; /* Explicitly set dropdown list background to white */
    color: #333333; /* Explicitly set dropdown list item text to black */
    padding: 5px;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); /* Subtle shadow for dropdown */
}
QComboBox QAbstractItemView::item {
    padding: 8px 10px; /* Padding for dropdown items */
}
QComboBox QAbstractItemView::item:selected {
    background-color: #409eff;
    color: white;
}

/* QCheckBox Styling */
QCheckBox {
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 14px;
    color: #34495e;
    padding: 5px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #dcdfe6;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border: 1px solid #409eff;
}

QCheckBox::indicator:checked {
    background-color: #409eff;
    border: 1px solid #409eff;
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3d3cudzMuorgvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSIjZmZmZmZmIiBkMTAgMTUuNzg2LTMuNjQzLTMuNjQzLTIuMTI1IDIuMTI1TDkuNCAyMC4zNzZsOS44Mi05LjgyLTIuMTItMi4xMjVsLTcuMDk1IDcuMDk1eiIvPjwvc3ZnPg==); /* Checkmark SVG */
}


/* Push Buttons */
QPushButton {
    background-color: #409eff; /* Primary blue */
    color: white;
    border: none;
    border-radius: 8px; /* More rounded */
    padding: 12px 20px; /* Larger padding for better clickability */
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 15px; /* Slightly larger font */
    font-weight: 600; /* Semi-bold */
    margin: 8px 0; /* Vertical margin */
    transition: all 0.2s ease-in-out; /* Smooth transitions */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Subtle shadow */
}

QPushButton:hover {
    background-color: #66b1ff; /* Lighter blue on hover */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15); /* Slightly larger shadow on hover */
    transform: translateY(-1px); /* Slight lift effect */
}

QPushButton:pressed {
    background-color: #3a8ee6; /* Darker blue on press */
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1); /* Smaller shadow on press */
    transform: translateY(0); /* Reset lift effect */
}

QPushButton:disabled {
    background-color: #a0cfff; /* Lighter, desaturated blue */
    color: #fefefe;
    box-shadow: none;
    opacity: 0.7;
}

/* Specific Button Styling (using qProperty) */
QPushButton[class="submitButton"] {
    background-color: #67c23a; /* Green for add */
}
QPushButton[class="submitButton"]:hover {
    background-color: #85ce61;
}
QPushButton[class="submitButton"]:pressed {
    background-color: #5cb85c;
}

QPushButton[class="updateButton"] {
    background-color: #e6a23c; /* Orange for update */
}
QPushButton[class="updateButton"]:hover {
    background-color: #ebb563;
}
QPushButton[class="updateButton"]:pressed {
    background-color: #d6932e;
}


QPushButton[class="deleteButton"] {
    background-color: #f56c6c; /* Red for delete */
}
QPushButton[class="deleteButton"]:hover {
    background-color: #f78989;
}
QPushButton[class="deleteButton"]:pressed {
    background-color: #e15f5f;
}

QPushButton[class="saveButton"] {
    background-color: #909399; /* Grey for save */
}
QPushButton[class="saveButton"]:hover {
    background-color: #a6a9ad;
}
QPushButton[class="saveButton"]:pressed {
    background-color: #7f8185;
}

QPushButton[class="clearButton"], QPushButton[class="cancelButton"] {
    background-color: #dcdfe6; /* Light grey for clear/cancel */
    color: #606266; /* Darker text */
}
QPushButton[class="clearButton"]:hover, QPushButton[class="cancelButton"]:hover {
    background-color: #e4e7ed;
    color: #4d4e51;
}
QPushButton[class="clearButton"]:pressed, QPushButton[class="cancelButton"]:pressed {
    background-color: #c0c4cc;
}

QPushButton[class="editButton"] {
    background-color: #b3d8ff; /* Lighter blue for edit */
    color: #409eff; /* Blue text */
    border: 1px solid #409eff;
}
QPushButton[class="editButton"]:hover {
    background-color: #cce5ff;
}
QPushButton[class="editButton"]:pressed {
    background-color: #93c8ff;
}


/* Table View */
QTableView {
    background-color: #ffffff;
    border: 1px solid #ebeef5; /* Very light border */
    border-radius: 10px; /* More rounded corners */
    gridline-color: #f2f6fc; /* Very light grid lines */
    selection-background-color: #d9ecff; /* Lighter blue selection */
    selection-color: #333333; /* Dark text on selection */
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    color: #333333; /* Default text color for table items */
    padding: 5px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); /* Subtle shadow */
}

QTableView::item {
    padding: 6px;
    border-bottom: 1px solid #f2f6fc; /* Subtle separator between items */
}

QTableView::item:alternate {
    background-color: #f8f9fb; /* Subtle alternating row color */
}

QHeaderView::section {
    background-color: #eef2f8; /* Light blue-grey header background */
    padding: 10px 12px;
    border: 1px solid #e0e6ec; /* Lighter border for header */
    font-weight: 600; /* Semi-bold */
    font-size: 14px;
    color: #4d596a; /* Darker blue-grey for header text */
    text-align: left; /* Align header text to left */
    border-radius: 5px; /* Rounded header corners */
}

QHeaderView::section:horizontal {
    border-bottom: 1px solid #d4dae0;
    border-right: 1px solid #eef2f8; /* Match background for seamless look */
}
QHeaderView::section:horizontal:last-child {
    border-right: none; /* No right border on last header */
}

QHeaderView::section:vertical {
    border-right: 1px solid #d4dae0;
    border-bottom: 1px solid #eef2f8; /* Match background for seamless look */
}
QHeaderView::section:vertical:last-child {
    border-bottom: none; /* No bottom border on last vertical header */
}


/* Input Form Specifics (targeting by objectName) */
#CardInputForm {
    background-color: #ffffff;
    border-radius: 12px; /* More rounded */
    padding: 25px; /* More internal padding */
    margin: 10px; /* External margin */
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08); /* Soft shadow for depth */
    border: 1px solid #e6e6e6; /* Very light border */
}

/* Status Bar */
QStatusBar {
    background-color: #e9eff5; /* Light blue-grey */
    color: #34495e; /* Dark text */
    font-size: 13px;
    padding: 5px 10px;
    border-top: 1px solid #d4dbe2;
    border-radius: 0 0 10px 10px; /* Rounded bottom corners if main window has them */
}

/* Duplicate Card Dialog specific styling */
QDialog {
    background-color: #ffffff;
    border-radius: 10px;
    border: 1px solid #c0c4cc;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

QDialog QLabel {
    font-size: 15px;
    font-weight: 500;
    color: #303133;
    padding: 15px;
}

QDialog QDialogButtonBox QPushButton {
    min-width: 100px;
    padding: 10px 15px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: normal;
    box-shadow: none; /* Remove extra shadows for dialog buttons */
}

QDialog QDialogButtonBox QPushButton[text="Add to Quantity"] {
    background-color: #409eff; /* Blue for primary action */
    color: white;
}
QDialog QDialogButtonBox QPushButton[text="Add to Quantity"]:hover {
    background-color: #66b1ff;
}

QDialog QDialogButtonBox QPushButton[text="Add as New Card"] {
    background-color: #e6a23c; /* Orange for alternative action */
    color: white;
}
QDialog QDialogButtonBox QPushButton[text="Add as New Card"]:hover {
    background-color: #ebb563;
}

QDialog QDialogButtonBox QPushButton[text="Cancel"] {
    background-color: #f56c6c; /* Red for cancel */
    color: white;
}
QDialog QDialogButtonBox QPushButton[text="Cancel"]:hover {
    background-color: #f78989;
}

/* QTabWidget Styling */
QTabWidget::pane { /* The tab widget frame */
    border: 1px solid #c0c4cc;
    border-radius: 8px;
    padding: 10px;
    background-color: #ffffff;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

QTabBar::tab {
    background: #eef2f8; /* Light background for inactive tabs */
    border: 1px solid #d4dae0;
    border-bottom: none; /* No bottom border for tabs */
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 14px;
    color: #4d596a; /* Dark text for inactive tabs */
    margin-right: 2px; /* Small space between tabs */
}

QTabBar::tab:selected {
    background: #ffffff; /* White background for selected tab */
    border-color: #c0c4cc;
    border-bottom-color: #ffffff; /* Make the bottom border disappear */
    color: #34495e; /* Darker text for selected tab */
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background: #e4e7ed; /* Slightly darker on hover for unselected tabs */
}

/* Menu Bar and Menu Styling */
QMenuBar {
    background-color: #f0f2f5; /* Match window background */
    color: #333333; /* Dark text color */
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 14px;
}

QMenuBar::item {
    padding: 5px 10px;
    background: transparent;
}

QMenuBar::item:selected {
    background-color: #e0e6ec; /* Highlight on hover */
    border-radius: 4px;
}

QMenu {
    background-color: #ffffff; /* White background for dropdown menu */
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    padding: 5px;
}

QMenu::item {
    padding: 8px 15px;
    color: #333333; /* Dark text color for menu items */
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
}

QMenu::item:selected {
    background-color: #409eff; /* Blue highlight on selection */
    color: white; /* White text on selected item */
    border-radius: 4px;
}

QMenu::separator {
    height: 1px;
    background-color: #e0e6ec;
    margin: 5px 0;
}

/* Shortcuts Dialog Styling */
ShortcutsDialog {
    background-color: #f9f9f9;
    border: 1px solid #c0c4cc;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    padding: 10px;
}
ShortcutsDialog QLabel {
    color: #333333;
    font-size: 13px;
}
ShortcutsDialog QLabel b {
    color: #409eff; /* Make shortcut text a bit more prominent */
}

"""

# --- MAIN APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply the embedded QSS style
    app.setStyleSheet(QSS_STYLE)
    print("Embedded stylesheet applied.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
