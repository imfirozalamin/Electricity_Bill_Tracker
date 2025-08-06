import sys
import json
import os
import calendar
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QDateEdit, QComboBox, QMessageBox, QHeaderView, QGroupBox,
                             QTabWidget, QFrame, QSizePolicy, QInputDialog)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette

# --- Matplotlib Integration ---
# Make sure to install matplotlib: pip install matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Helper class for the Matplotlib canvas
class MplCanvas(FigureCanvas):
    """A custom Matplotlib canvas widget to embed in PyQt5."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)

class ElectricityBillTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        # --- UPDATED: Window Title and Icon ---
        self.setWindowTitle("E-Bill Tracker")
        
        # Centralized path management for all data files
        self.base_path = self._get_base_path()
        self.history_file = os.path.join(self.base_path, "electricity_bill_history.json")
        self.initial_reading_file = os.path.join(self.base_path, "initial_reading.json")
        self.devices_file = os.path.join(self.base_path, "devices.json")
        
        # Set the window icon. The icon file must be in the same folder.
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setGeometry(100, 100, 1200, 800)
        self.unit_cost = 12  # ₹12 per unit

        self.history_data = self.load_history()
        self.devices_data = self.load_devices()
        self.current_reading = self.get_initial_reading()

        # Dark theme colors
        self.dark_bg = "#2D2D2D"
        self.dark_widget = "#3E3E3E"
        self.dark_text = "#E0E0E0"
        self.accent_color = "#476ed4"
        self.accent_dark = "#388eff"
        self.warning_color = "#F44336"
        self.grid_color = "#555555"

        self.init_ui()
        self.apply_dark_theme()

        # Initial updates after UI is built
        self.refresh_current_reading()
        self.update_history_table()
        self.update_summary()
        self.update_analytics()
        self.update_devices_table()
        self.update_usage_estimation()
        
    def _get_base_path(self):
        """
        Creates and returns a path to a dedicated app data folder.
        This is a robust way to ensure write permissions.
        """
        if sys.platform == "win32":
            app_data_path = os.getenv('APPDATA')
        else:
            app_data_path = os.path.join(os.path.expanduser("~"), ".config")
        
        app_folder = os.path.join(app_data_path, "EBillTracker")
        
        try:
            if not os.path.exists(app_folder):
                os.makedirs(app_folder)
        except OSError as e:
            print(f"Warning: Could not create app data directory at {app_folder}. Error: {e}. Falling back to script directory.")
            return os.path.dirname(os.path.abspath(__file__))
            
        return app_folder

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(self.dark_bg))
        palette.setColor(QPalette.WindowText, QColor(self.dark_text))
        palette.setColor(QPalette.Base, QColor(self.dark_widget))
        palette.setColor(QPalette.AlternateBase, QColor(self.dark_widget))
        palette.setColor(QPalette.ToolTipBase, QColor(self.dark_text))
        palette.setColor(QPalette.ToolTipText, QColor(self.dark_text))
        palette.setColor(QPalette.Text, QColor(self.dark_text))
        palette.setColor(QPalette.Button, QColor(self.dark_widget))
        palette.setColor(QPalette.ButtonText, QColor(self.dark_text))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(self.accent_color))
        palette.setColor(QPalette.HighlightedText, Qt.black)

        self.setPalette(palette)
        
        self.setStyleSheet(f"""
            QMainWindow, QDialog {{
                background-color: {self.dark_bg};
            }}
            QGroupBox {{
                border: 1px solid {self.grid_color};
                border-radius: 4px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {self.dark_text};
                font-weight: bold;
            }}
            QLabel {{
                color: {self.dark_text};
            }}
            QLineEdit, QDateEdit {{
                background-color: {self.dark_widget};
                color: {self.dark_text};
                border: 1px solid {self.grid_color};
                border-radius: 4px;
                padding: 5px;
            }}
            QLineEdit:focus, QDateEdit:focus {{
                border: 1px solid {self.accent_color};
            }}
            QComboBox {{
                background-color: {self.dark_widget};
                color: {self.dark_text};
                border: 1px solid {self.grid_color};
                border-radius: 4px;
                padding: 5px;
            }}
            QComboBox:focus {{
                border: 1px solid {self.accent_color};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                color: black;
                border: 1px solid {self.grid_color};
                selection-background-color: {self.accent_dark};
                selection-color: white;
            }}
            QHeaderView::section {{
                background-color: {self.accent_dark};
                color: white;
                padding: 5px;
                border: none;
            }}
            QTabWidget::pane {{
                border: 1px solid {self.dark_widget};
                border-radius: 4px;
                padding: 5px;
            }}
            QTabBar::tab {{
                background: {self.dark_widget};
                color: {self.dark_text};
                padding: 8px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background: {self.accent_dark};
                color: white;
            }}

            #historyTable {{
                background-color: white;
                color: black;
                gridline-color: #cccccc;
                alternate-background-color: #f0f0f0;
            }}
            #historyTable::item {{
                color: black;
                border-bottom: 1px solid #eee;
            }}
            #historyTable::item:selected {{
                background-color: {self.accent_dark};
                color: white;
            }}
            #historyTable QHeaderView::section {{
                background-color: #333333;
                color: white;
            }}

            #devicesTable {{
                background-color: white;
                color: black;
                gridline-color: #cccccc;
                alternate-background-color: #f0f0f0;
            }}
            #devicesTable::item {{
                color: black;
                border-bottom: 1px solid #eee;
            }}
            #devicesTable::item:selected {{
                background-color: {self.accent_dark};
                color: white;
            }}
            #devicesTable QHeaderView::section {{
                background-color: #333333;
                color: white;
            }}

            QMessageBox {{
                background-color: #f0f0f0;
            }}
            QMessageBox QLabel {{
                color: black;
            }}
            QMessageBox QPushButton {{
                background-color: #c0c0c0;
                color: black;
                border: 1px solid #a0a0a0;
                padding: 5px 15px;
                border-radius: 4px;
                min-width: 70px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #d0d0d0;
            }}
            QMessageBox QPushButton:pressed {{
                background-color: #b0b0b0;
            }}
        """)

    def get_initial_reading(self):
        # If we have history data, always use the most recent reading as the current reading
        if self.history_data:
            last_entry = max(self.history_data, key=lambda x: QDate.fromString(x["date"], "dd-MM-yyyy").toJulianDay())
            return last_entry["new_reading"]
        
        # If no history but we have an initial reading file, use that
        if os.path.exists(self.initial_reading_file):
            try:
                with open(self.initial_reading_file, "r") as f:
                    data = json.load(f)
                    return float(data["initial_reading"])
            except:
                pass
        
        # No data at all, return 0
        return 0.0
    
    def refresh_current_reading(self):
        """Refresh the current reading display based on the latest data"""
        self.current_reading = self.get_initial_reading()
        if hasattr(self, 'current_reading_label'):
            self.current_reading_label.setText(f"Current Meter Reading: {self.current_reading}")

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        header = QLabel("E-Bill Tracker")
        header_font = QFont("Segoe UI", 24, QFont.Bold)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"color: {self.accent_color}; margin-bottom: 10px;")

        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.init_main_tab()
        self.tabs.addTab(self.main_tab, "Tracker")

        self.analytics_tab = QWidget()
        self.init_analytics_tab()
        self.tabs.addTab(self.analytics_tab, "Analytics")

        self.devices_tab = QWidget()
        self.init_devices_tab()
        self.tabs.addTab(self.devices_tab, "Devices")

        main_layout.addWidget(header)
        main_layout.addWidget(self.tabs)

        reset_action = self.menuBar().addAction("Reset Data")
        reset_action.triggered.connect(self.confirm_reset)
        
        self.menuBar().setNativeMenuBar(False)
        self.menuBar().hide()

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def init_main_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.initial_group = QGroupBox("Set Initial Meter Reading")
        self.initial_group.setVisible(not bool(self.history_data) and self.current_reading == 0)
        initial_layout = QVBoxLayout()
        initial_help = QLabel("Welcome! Please enter the meter reading from when you started using this electricity connection.")
        initial_help.setWordWrap(True)
        initial_input_layout = QHBoxLayout()
        label_initial = QLabel("Initial Meter Reading:")
        initial_input_layout.addWidget(label_initial)
        self.initial_reading_input = QLineEdit()
        self.initial_reading_input.setPlaceholderText("Enter initial meter reading")
        self.set_initial_btn = QPushButton("Set Initial Reading")
        self.set_initial_btn.setStyleSheet(self.get_button_style(self.accent_color))
        self.set_initial_btn.clicked.connect(self.set_initial_reading)
        initial_input_layout.addWidget(self.initial_reading_input)
        initial_input_layout.addWidget(self.set_initial_btn)
        initial_layout.addWidget(initial_help)
        initial_layout.addLayout(initial_input_layout)
        self.initial_group.setLayout(initial_layout)

        self.meter_group = QGroupBox("Meter Reading")
        self.meter_group.setVisible(bool(self.history_data) or self.current_reading != 0)
        meter_layout = QVBoxLayout()
        self.current_reading_label = QLabel(f"Current Meter Reading: {self.current_reading}")
        self.current_reading_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.current_reading_label.setStyleSheet(f"color: {self.accent_color};")
        reading_input_layout = QHBoxLayout()
        label_new = QLabel("New Meter Reading:")
        reading_input_layout.addWidget(label_new)
        self.new_reading_input = QLineEdit()
        self.new_reading_input.setPlaceholderText("Enter new meter reading")
        self.new_reading_input.textChanged.connect(self.update_consumption)
        reading_input_layout.addWidget(self.new_reading_input)
        reading_input_layout.addStretch()
        self.consumption_label = QLabel("Consumption: 0.00 units")
        self.consumption_label.setFont(QFont("Segoe UI", 10))
        meter_layout.addWidget(self.current_reading_label)
        meter_layout.addLayout(reading_input_layout)
        meter_layout.addWidget(self.consumption_label)
        self.meter_group.setLayout(meter_layout)

        calc_group = QGroupBox("Calculate Bill")
        calc_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        left_inputs = QVBoxLayout()
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        label_date = QLabel("Date:")
        left_inputs.addWidget(label_date)
        left_inputs.addWidget(self.date_input)
        left_inputs.addStretch()
        right_inputs = QVBoxLayout()
        self.cost_label = QLabel("Total Cost: ₹0.00")
        self.cost_label.setFont(QFont("Segoe UI", 12))
        btn_layout = QHBoxLayout()
        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.setStyleSheet(self.get_button_style("#2196F3"))
        self.calculate_btn.clicked.connect(self.calculate_bill)
        self.save_btn = QPushButton("Save Entry")
        self.save_btn.setStyleSheet(self.get_button_style(self.accent_color))
        self.save_btn.clicked.connect(self.save_entry)
        btn_layout.addWidget(self.calculate_btn)
        btn_layout.addWidget(self.save_btn)
        right_inputs.addWidget(self.cost_label)
        right_inputs.addLayout(btn_layout)
        right_inputs.addStretch()
        input_layout.addLayout(left_inputs)
        input_layout.addLayout(right_inputs)
        calc_layout.addLayout(input_layout)
        calc_group.setLayout(calc_layout)

        history_group = QGroupBox("Usage History")
        history_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        label_filter = QLabel("Filter by:")
        filter_layout.addWidget(label_filter)
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All", "This Month", "This Year", "Custom Range"])
        self.filter_type.currentIndexChanged.connect(self.update_history_table)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setEnabled(False)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setEnabled(False)
        self.filter_type.currentTextChanged.connect(self.toggle_date_range)
        
        self.start_date.dateChanged.connect(self.update_history_table)
        self.end_date.dateChanged.connect(self.update_history_table)

        filter_layout.addWidget(self.filter_type)
        filter_layout.addWidget(self.start_date)
        label_to = QLabel("to")
        filter_layout.addWidget(label_to)
        filter_layout.addWidget(self.end_date)
        filter_layout.addStretch()
        
        self.history_table = QTableWidget()
        self.history_table.setObjectName("historyTable")
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Previous", "New", "Units", "Total Cost"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        
        history_layout.addLayout(filter_layout)
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)

        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()
        self.summary_label = QLabel("Loading summary...")
        self.summary_label.setFont(QFont("Segoe UI", 10))
        summary_layout.addWidget(self.summary_label)
        summary_group.setLayout(summary_layout)

        layout.addWidget(self.initial_group)
        layout.addWidget(self.meter_group)
        layout.addWidget(calc_group)
        layout.addWidget(history_group)
        layout.addWidget(summary_group)
        self.main_tab.setLayout(layout)

    def init_analytics_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        period_group = QGroupBox("Time Period")
        period_layout = QHBoxLayout()
        self.analytics_period = QComboBox()
        self.analytics_period.addItems(["Monthly", "Weekly", "Daily", "Yearly"])
        self.analytics_period.currentIndexChanged.connect(self.update_analytics)
        self.analytics_period.currentTextChanged.connect(self._on_analytics_period_change)
        current_year = datetime.now().year
        self.analytics_year = QComboBox()
        self.analytics_year.addItems([str(y) for y in range(current_year - 5, current_year + 1)])
        self.analytics_year.setCurrentText(str(current_year))
        self.analytics_year.currentIndexChanged.connect(self.update_analytics)
        label_view = QLabel("View:")
        period_layout.addWidget(label_view)
        period_layout.addWidget(self.analytics_period)
        self.label_year = QLabel("Year:")
        period_layout.addWidget(self.label_year)
        period_layout.addWidget(self.analytics_year)
        period_layout.addStretch()
        period_group.setLayout(period_layout)

        graph_group = QGroupBox("Consumption Trend")
        graph_layout = QVBoxLayout()
        self.graph_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        graph_layout.addWidget(self.graph_canvas)
        graph_group.setLayout(graph_layout)

        layout.addWidget(period_group, 0)
        layout.addWidget(graph_group, 1)
        self.analytics_tab.setLayout(layout)

    def init_devices_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Add Device Section
        add_device_group = QGroupBox("Add New Device")
        add_device_layout = QVBoxLayout()
        
        device_input_layout = QHBoxLayout()
        device_input_layout.addWidget(QLabel("Device Name:"))
        self.device_name_input = QLineEdit()
        self.device_name_input.setPlaceholderText("e.g., LED TV, Refrigerator, AC")
        device_input_layout.addWidget(self.device_name_input)
        
        device_input_layout.addWidget(QLabel("Power (Watts):"))
        self.device_power_input = QLineEdit()
        self.device_power_input.setPlaceholderText("e.g., 150")
        device_input_layout.addWidget(self.device_power_input)
        
        device_input_layout.addWidget(QLabel("Hours/Day:"))
        self.device_hours_input = QLineEdit()
        self.device_hours_input.setPlaceholderText("e.g., 8")
        device_input_layout.addWidget(self.device_hours_input)
        
        self.add_device_btn = QPushButton("Add Device")
        self.add_device_btn.setStyleSheet(self.get_button_style(self.accent_color))
        self.add_device_btn.clicked.connect(self.add_device)
        device_input_layout.addWidget(self.add_device_btn)
        
        add_device_layout.addLayout(device_input_layout)
        add_device_group.setLayout(add_device_layout)

        # Devices Table
        devices_group = QGroupBox("Your Devices")
        devices_layout = QVBoxLayout()
        
        self.devices_table = QTableWidget()
        self.devices_table.setObjectName("devicesTable")
        self.devices_table.setColumnCount(6)
        self.devices_table.setHorizontalHeaderLabels([
            "Device Name", "Power (W)", "Hours/Day", "Daily kWh", "Monthly kWh", "Actions"
        ])
        self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.devices_table.setAlternatingRowColors(True)
        
        devices_layout.addWidget(self.devices_table)
        devices_group.setLayout(devices_layout)

        # Usage Estimation
        estimation_group = QGroupBox("Usage Estimation")
        estimation_layout = QVBoxLayout()
        
        self.estimation_label = QLabel("Total Estimated Monthly Usage: 0.00 kWh (₹0.00)")
        self.estimation_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.estimation_label.setStyleSheet(f"color: {self.accent_color};")
        
        comparison_layout = QHBoxLayout()
        self.comparison_label = QLabel("Comparison with actual usage will appear here")
        comparison_layout.addWidget(self.comparison_label)
        
        estimation_layout.addWidget(self.estimation_label)
        estimation_layout.addLayout(comparison_layout)
        estimation_group.setLayout(estimation_layout)

        layout.addWidget(add_device_group)
        layout.addWidget(devices_group)
        layout.addWidget(estimation_group)
        self.devices_tab.setLayout(layout)
        
    def get_button_style(self, color):
        try:
            base_color = QColor(color)
            hover_color = base_color.darker(115)
            pressed_color = base_color.darker(130)
            
            return f"""
                QPushButton {{
                    background-color: {base_color.name()};
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                    min-width: 80px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {hover_color.name()};
                }}
                QPushButton:pressed {{
                    background-color: {pressed_color.name()};
                }}
                QPushButton:disabled {{
                    background-color: #555;
                    color: #999;
                }}
            """
        except Exception:
            return "QPushButton { background-color: #555; }"

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Alt:
            if self.menuBar().isHidden():
                self.menuBar().show()
            else:
                self.menuBar().hide()
        super().keyPressEvent(event)

    def set_initial_reading(self):
        try:
            initial_reading = float(self.initial_reading_input.text())
            if initial_reading < 0:
                raise ValueError("Reading cannot be negative")

            with open(self.initial_reading_file, "w") as f:
                json.dump({"initial_reading": initial_reading}, f)

            self.current_reading = initial_reading
            self.refresh_current_reading()
            self.initial_group.setVisible(False)
            self.meter_group.setVisible(True)
            QMessageBox.information(self, "Success", f"Initial reading set to {initial_reading}")

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid, non-negative number.")
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Could not save the initial reading file.\nError: {e}")

    def update_consumption(self):
        try:
            if not self.new_reading_input.text():
                 self.consumption_label.setText("Consumption: 0.00 units")
                 self.consumption_label.setStyleSheet(f"color: {self.dark_text};")
                 return
                 
            new_reading = float(self.new_reading_input.text())
            consumption = new_reading - self.current_reading

            if consumption < 0:
                self.consumption_label.setText("⚠️ New reading must be higher than current reading")
                self.consumption_label.setStyleSheet(f"color: {self.warning_color};")
            else:
                self.consumption_label.setText(f"Consumption: {consumption:.2f} units")
                self.consumption_label.setStyleSheet(f"color: {self.dark_text};")
        except ValueError:
            self.consumption_label.setText("Enter valid meter reading")
            self.consumption_label.setStyleSheet(f"color: {self.warning_color};")

    def calculate_bill(self):
        try:
            new_reading = float(self.new_reading_input.text())
            consumption = new_reading - self.current_reading

            if consumption < 0:
                raise ValueError("New reading must be higher than current reading")

            total_cost = consumption * self.unit_cost
            self.cost_label.setText(f"Total Cost: ₹{total_cost:.2f}")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid, non-negative number.")

    def save_entry(self):
        try:
            new_reading = float(self.new_reading_input.text())
            consumption = new_reading - self.current_reading

            if consumption < 0:
                raise ValueError("New reading must be higher than current reading")

            date = self.date_input.date().toString("dd-MM-yyyy")
            total_cost = consumption * self.unit_cost

            entry = {
                "date": date,
                "previous_reading": self.current_reading,
                "new_reading": new_reading,
                "units": consumption,
                "unit_cost": self.unit_cost,
                "total_cost": total_cost
            }
            
            self.history_data.append(entry)
            self.save_history()
            
            # Update current reading to the new reading
            self.current_reading = new_reading
            self.refresh_current_reading()
            
            # Clear inputs
            self.new_reading_input.clear()
            self.consumption_label.setText("Consumption: 0.00 units")
            self.cost_label.setText("Total Cost: ₹0.00")
            
            # Update all displays
            self.update_history_table()
            self.update_summary()
            self.update_analytics()
            self.update_usage_estimation()  # Update device comparison
            
            if not self.meter_group.isVisible():
                self.meter_group.setVisible(True)

            QMessageBox.information(self, "Success", "Entry saved successfully")

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid, non-negative number to save.")

    def update_history_table(self):
        if not hasattr(self, 'filter_type'):
            return
        filtered_data = self.filter_history()
        self.history_table.setRowCount(len(filtered_data))

        for row, entry in enumerate(filtered_data):
            self.history_table.setItem(row, 0, QTableWidgetItem(entry["date"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(f"{entry['previous_reading']:.2f}"))
            self.history_table.setItem(row, 2, QTableWidgetItem(f"{entry['new_reading']:.2f}"))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{entry['units']:.2f}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(f"₹{entry['total_cost']:.2f}"))

    def filter_history(self):
        if not self.history_data:
            return []

        filter_type = self.filter_type.currentText()
        today = QDate.currentDate()
        filtered = []
        sorted_data = sorted(self.history_data, key=lambda x: QDate.fromString(x["date"], "dd-MM-yyyy"), reverse=True)

        for entry in sorted_data:
            entry_date = QDate.fromString(entry["date"], "dd-MM-yyyy")
            if filter_type == "All":
                filtered.append(entry)
            elif filter_type == "This Month":
                if entry_date.month() == today.month() and entry_date.year() == today.year():
                    filtered.append(entry)
            elif filter_type == "This Year":
                if entry_date.year() == today.year():
                    filtered.append(entry)
            elif filter_type == "Custom Range":
                start_date = self.start_date.date()
                end_date = self.end_date.date()
                if start_date <= entry_date <= end_date:
                    filtered.append(entry)
        return filtered

    def toggle_date_range(self, text):
        is_custom = (text == "Custom Range")
        self.start_date.setEnabled(is_custom)
        self.end_date.setEnabled(is_custom)
        self.update_history_table()

    def update_summary(self):
        if not self.history_data:
            self.summary_label.setText("No usage history available")
            return

        total_units = sum(entry["units"] for entry in self.history_data)
        total_cost = sum(entry["total_cost"] for entry in self.history_data)
        today = QDate.currentDate()
        this_month_units = sum(
            entry["units"] for entry in self.history_data
            if QDate.fromString(entry["date"], "dd-MM-yyyy").month() == today.month()
            and QDate.fromString(entry["date"], "dd-MM-yyyy").year() == today.year()
        )
        summary_text = (
            f"📊 Total Usage: {total_units:.2f} units (₹{total_cost:.2f})   |   "
            f"📅 This Month: {this_month_units:.2f} units (₹{this_month_units * self.unit_cost:.2f})   |   "
            f"💰 Unit Cost: ₹{self.unit_cost:.2f}"
        )
        self.summary_label.setText(summary_text)

    def _on_analytics_period_change(self, text):
        is_yearly = (text == "Yearly")
        self.analytics_year.setVisible(not is_yearly)
        self.label_year.setVisible(not is_yearly)

    def update_analytics(self):
        if not self.history_data:
            self.update_graph({})
            return

        period = self.analytics_period.currentText()
        year_str = self.analytics_year.currentText()
        if not year_str: return
        year = int(year_str)

        if period == "Daily":
            self.show_daily_stats(year)
        elif period == "Weekly":
            self.show_weekly_stats(year)
        elif period == "Monthly":
            self.show_monthly_stats(year)
        elif period == "Yearly":
            self.show_yearly_stats()

    def update_graph(self, stats_data, sorted_keys=None):
        ax = self.graph_canvas.axes
        ax.cla()

        if not stats_data:
            ax.text(0.5, 0.5, 'No data to display', 
                    horizontalalignment='center', verticalalignment='center', 
                    transform=ax.transAxes, color=self.dark_text)
        else:
            periods = sorted_keys if sorted_keys is not None else sorted(stats_data.keys())
            units = [stats_data[key]['units'] for key in periods]
            ax.plot(periods, units, marker='o', linestyle='-', color=self.accent_color, label='Units Consumed')
            ax.set_xlabel('Period', color=self.dark_text, fontweight='bold')
            ax.set_ylabel('Units Consumed', color=self.dark_text, fontweight='bold')
            ax.set_title('Consumption Trend', color=self.dark_text, fontweight='bold')
            ax.grid(True, color=self.grid_color, linestyle='--', linewidth=0.5)

        ax.set_facecolor(self.dark_widget)
        self.graph_canvas.fig.set_facecolor(self.dark_bg)
        ax.tick_params(axis='x', colors=self.dark_text, labelrotation=40, labelsize='small')
        ax.tick_params(axis='y', colors=self.dark_text)
        for spine in ax.spines.values():
            spine.set_edgecolor(self.grid_color)

        self.graph_canvas.fig.tight_layout()
        self.graph_canvas.draw()

    def _get_ordinal(self, n):
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return f"{n}{suffix}"

    def show_daily_stats(self, year):
        daily_data = {}
        for entry in self.history_data:
            entry_date = QDate.fromString(entry["date"], "dd-MM-yyyy")
            if entry_date.year() != year: continue
            day_key = entry_date.toString("yyyy-MM-dd")
            if day_key not in daily_data:
                daily_data[day_key] = {"units": 0, "cost": 0}
            daily_data[day_key]["units"] += entry["units"]
            daily_data[day_key]["cost"] += entry["total_cost"]
        self.update_graph(daily_data)

    def show_weekly_stats(self, year):
        weekly_data = {}
        for entry in self.history_data:
            entry_date = QDate.fromString(entry["date"], "dd-MM-yyyy")
            if entry_date.year() != year: continue
            
            week_of_month = (entry_date.day() - 1) // 7 + 1
            sort_key = f"{entry_date.year()}-{entry_date.month():02d}-{week_of_month}"

            if sort_key not in weekly_data:
                weekly_data[sort_key] = {"units": 0, "cost": 0}
            weekly_data[sort_key]["units"] += entry["units"]
            weekly_data[sort_key]["cost"] += entry["total_cost"]

        display_data = {}
        sorted_keys = sorted(weekly_data.keys())
        for key in sorted_keys:
            y, m, w = map(int, key.split('-'))
            ordinal_week = self._get_ordinal(w)
            month_name = calendar.month_name[m]
            display_key = f"{ordinal_week} week {month_name} {y}"
            display_data[display_key] = weekly_data[key]
        
        sorted_display_keys = list(display_data.keys())
        self.update_graph(display_data, sorted_keys=sorted_display_keys)

    def show_monthly_stats(self, year):
        monthly_data_by_num = {}
        for entry in self.history_data:
            entry_date = QDate.fromString(entry["date"], "dd-MM-yyyy")
            if entry_date.year() != year: continue
            month_num = entry_date.month()
            if month_num not in monthly_data_by_num:
                monthly_data_by_num[month_num] = {"units": 0, "cost": 0}
            monthly_data_by_num[month_num]["units"] += entry["units"]
            monthly_data_by_num[month_num]["cost"] += entry["total_cost"]

        display_data = {}
        sorted_month_nums = sorted(monthly_data_by_num.keys())
        for month_num in sorted_month_nums:
            display_key = calendar.month_name[month_num]
            display_data[display_key] = monthly_data_by_num[month_num]
            
        sorted_display_keys = [calendar.month_name[k] for k in sorted_month_nums]
        self.update_graph(display_data, sorted_keys=sorted_display_keys)

    def show_yearly_stats(self):
        yearly_data = {}
        for entry in self.history_data:
            entry_date = QDate.fromString(entry["date"], "dd-MM-yyyy")
            year_key = entry_date.year()
            if year_key not in yearly_data:
                yearly_data[year_key] = {"units": 0, "cost": 0}
            yearly_data[year_key]["units"] += entry["units"]
            yearly_data[year_key]["cost"] += entry["total_cost"]
        self.update_graph(yearly_data)

    def confirm_reset(self):
        password, ok = QInputDialog.getText(self, "Reset Data",
                                          "This will delete ALL your data!\nEnter 'reset123' to confirm:",
                                          QLineEdit.Password)
        if ok and password == "reset123":
            reply = QMessageBox.question(
                self, "Confirm Reset",
                "Are you absolutely sure you want to delete ALL data?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.reset_data()
        elif ok:
             QMessageBox.warning(self, "Incorrect Password", "The password was incorrect. Data was not reset.")

    def reset_data(self):
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            if os.path.exists(self.initial_reading_file):
                os.remove(self.initial_reading_file)
            self.history_data = []
            self.current_reading = 0.0
            self.initial_group.setVisible(True)
            self.meter_group.setVisible(False)
            self.update_history_table()
            self.update_summary()
            self.update_analytics()
            self.initial_reading_input.clear()
            self.current_reading_label.setText("Current Meter Reading: 0.0")
            QMessageBox.information(self, "Reset Complete", "All data has been reset successfully")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to reset data: {str(e)}")

    def save_history(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history_data, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save history file: {e}")

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load history file. It may be corrupted.\nError: {e}")
            return []

    def load_devices(self):
        try:
            if os.path.exists(self.devices_file):
                with open(self.devices_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Could not load devices file. It may be corrupted.\nError: {e}")
            return []

    def save_devices(self):
        try:
            with open(self.devices_file, "w") as f:
                json.dump(self.devices_data, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save devices file: {e}")

    def add_device(self):
        try:
            name = self.device_name_input.text().strip()
            power = float(self.device_power_input.text())
            hours = float(self.device_hours_input.text())
            
            if not name:
                QMessageBox.warning(self, "Invalid Input", "Please enter a device name.")
                return
            
            if power <= 0 or hours <= 0:
                QMessageBox.warning(self, "Invalid Input", "Power and hours must be positive numbers.")
                return
            
            if hours > 24:
                QMessageBox.warning(self, "Invalid Input", "Hours per day cannot exceed 24.")
                return
            
            # Check if device already exists
            for device in self.devices_data:
                if device["name"].lower() == name.lower():
                    QMessageBox.warning(self, "Duplicate Device", "A device with this name already exists.")
                    return
            
            device = {
                "name": name,
                "power_watts": power,
                "hours_per_day": hours,
                "daily_kwh": (power * hours) / 1000,
                "monthly_kwh": (power * hours * 30) / 1000
            }
            
            self.devices_data.append(device)
            self.save_devices()
            self.update_devices_table()
            self.update_usage_estimation()
            
            # Clear inputs
            self.device_name_input.clear()
            self.device_power_input.clear()
            self.device_hours_input.clear()
            
            QMessageBox.information(self, "Success", f"Device '{name}' added successfully!")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for power and hours.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not add device: {e}")

    def remove_device(self, device_name):
        try:
            self.devices_data = [d for d in self.devices_data if d["name"] != device_name]
            self.save_devices()
            self.update_devices_table()
            self.update_usage_estimation()
            QMessageBox.information(self, "Success", f"Device '{device_name}' removed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not remove device: {e}")

    def update_devices_table(self):
        if not hasattr(self, 'devices_table'):
            return
            
        self.devices_table.setRowCount(len(self.devices_data))
        
        for row, device in enumerate(self.devices_data):
            self.devices_table.setItem(row, 0, QTableWidgetItem(device["name"]))
            self.devices_table.setItem(row, 1, QTableWidgetItem(f"{device['power_watts']:.0f}"))
            self.devices_table.setItem(row, 2, QTableWidgetItem(f"{device['hours_per_day']:.1f}"))
            self.devices_table.setItem(row, 3, QTableWidgetItem(f"{device['daily_kwh']:.3f}"))
            self.devices_table.setItem(row, 4, QTableWidgetItem(f"{device['monthly_kwh']:.2f}"))
            
            # Add remove button
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet(self.get_button_style(self.warning_color))
            remove_btn.clicked.connect(lambda checked, name=device["name"]: self.remove_device(name))
            self.devices_table.setCellWidget(row, 5, remove_btn)

    def update_usage_estimation(self):
        if not hasattr(self, 'estimation_label'):
            return
            
        total_monthly_kwh = sum(device["monthly_kwh"] for device in self.devices_data)
        total_cost = total_monthly_kwh * self.unit_cost
        
        self.estimation_label.setText(f"Total Estimated Monthly Usage: {total_monthly_kwh:.2f} kWh (₹{total_cost:.2f})")
        
        # Compare with actual usage if available
        if hasattr(self, 'comparison_label') and self.history_data:
            today = QDate.currentDate()
            this_month_actual = sum(
                entry["units"] for entry in self.history_data
                if QDate.fromString(entry["date"], "dd-MM-yyyy").month() == today.month()
                and QDate.fromString(entry["date"], "dd-MM-yyyy").year() == today.year()
            )
            
            if this_month_actual > 0:
                difference = this_month_actual - total_monthly_kwh
                if abs(difference) < 1:
                    comparison_text = f"📊 Actual this month: {this_month_actual:.2f} kWh - Very close to estimate!"
                    color = "#4CAF50"  # Green
                elif difference > 0:
                    comparison_text = f"📊 Actual this month: {this_month_actual:.2f} kWh - {difference:.2f} kWh more than estimate"
                    color = "#FF9800"  # Orange
                else:
                    comparison_text = f"📊 Actual this month: {this_month_actual:.2f} kWh - {abs(difference):.2f} kWh less than estimate"
                    color = "#2196F3"  # Blue
                
                self.comparison_label.setText(comparison_text)
                self.comparison_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            else:
                self.comparison_label.setText("No actual usage data for this month yet")
                self.comparison_label.setStyleSheet(f"color: {self.dark_text};")
        elif hasattr(self, 'comparison_label'):
            self.comparison_label.setText("Add some usage history to see comparison")
            self.comparison_label.setStyleSheet(f"color: {self.dark_text};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ElectricityBillTracker()
    window.show()
    sys.exit(app.exec_())
