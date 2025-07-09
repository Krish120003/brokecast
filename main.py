# sample pyside winow hellow world

from enum import Enum, auto
import os
import sys
from typing import List, Callable
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWidgets import (
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QLabel,
    QListWidgetItem,
)
from PySide6.QtCore import Signal, Slot, Qt, QEvent
import threading
from pynput import keyboard
from components.lists import ListFilterView, ListItem, ListItemType
from lib import get_installed_applications, Application
import pyperclip
import time


class HotkeyAction(Enum):
    TOGGLE_WINDOW = auto()


class SampleSubWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Sample Sub Widget"))


class ClipboardWidget(QWidget):
    clipboard_entry_signal = Signal(str)
    clipboard_history = []  # class variable, shared across all instances

    def __init__(self):
        print("ClipboardWidget created")
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Clipboard"))

        self.list_widget = QListWidget()
        self.layout().addWidget(self.list_widget)

        # Add padding and spacing between items via stylesheet
        self.list_widget.setStyleSheet(
            """
            QListWidget::item {
                background: red;
                margin: 8px;
                padding: 12px;
                border-radius: 6px;
                color: white;
            }
            QListWidget {
                background: transparent;
                border: none;
            }
            """
        )

        self.clipboard_entry_signal.connect(self.add_clipboard_entry)

        # in the background, listen for all clipboard changes and store them
        threading.Thread(target=self.start_clipboard_listener, daemon=True).start()

    @Slot(str)
    def add_clipboard_entry(self, entry):
        ClipboardWidget.clipboard_history.append(entry)
        self.list_widget.addItem(entry)
        print("Clipboard has", len(ClipboardWidget.clipboard_history), "items")

    def start_clipboard_listener(self):
        last_clipboard = None
        while True:
            clipboard = pyperclip.paste()
            if clipboard and clipboard != last_clipboard:
                self.clipboard_entry_signal.emit(clipboard)
                last_clipboard = clipboard
            time.sleep(0.1)

    # on show, rerender the entire list
    def showEvent(self, event):
        self.list_widget.clear()
        for item in ClipboardWidget.clipboard_history:
            self.list_widget.addItem(item)
        super().showEvent(event)


class MainWindow(QMainWindow):
    hotkey_pressed = Signal(HotkeyAction)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hello World")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # Widgets
        self.input_bar = QLineEdit(self)
        self.input_bar.setPlaceholderText("Type here")
        self.input_bar.installEventFilter(self)

        self.view_stack = []
        self.current_view = None

        # Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.input_bar)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        # Add initial view
        self.setup_home_view()

        # Connect input changes to view update (React-like state/props)
        self.input_bar.textChanged.connect(self.on_input_changed)

        self.hotkey_config = {
            (
                keyboard.Key.cmd,
                keyboard.Key.alt_l,
                keyboard.Key.space,
            ): HotkeyAction.TOGGLE_WINDOW,
        }

        self.hotkey_pressed.connect(self.on_hotkey)
        # Start the global hotkey listener in a separate thread
        threading.Thread(target=self.start_hotkey_listener, daemon=True).start()

    def _get_application_action(self, application: Application):
        def action():
            os.system(f"open {application.path}")

        return action

    def _get_command_action(self, fn: Callable):
        def action():
            print("COMMAND ACTION")
            fn()
            print("Clearing input bar")
            self.input_bar.clear()

        return action

    def setup_home_view(self):
        home_items = []
        for application in get_installed_applications():
            home_items.append(
                ListItem(
                    application.name,
                    ListItemType.APPLICATION,
                    self._get_application_action(application),
                )
            )

        home_items.append(
            ListItem(
                "11 Sample Sub Widget",
                ListItemType.COMMAND,
                self._get_command_action(lambda: self.push_view(SampleSubWidget())),
            )
        )

        home_items.append(
            ListItem(
                "Clipboard History",
                ListItemType.COMMAND,
                self._get_command_action(lambda: self.push_view(ClipboardWidget())),
            )
        )

        home_items.sort(key=str)

        home_view = ListFilterView(home_items)
        self.push_view(home_view)

    def push_view(self, view: QWidget):
        if self.current_view is not None:
            self.layout.removeWidget(self.current_view)
            self.current_view.setParent(None)
        self.view_stack.append(view)
        self.layout.addWidget(view)
        self.current_view = view

    def pop_view(self):
        if len(self.view_stack) > 1:
            old_view = self.view_stack.pop()
            self.layout.removeWidget(old_view)
            old_view.setParent(None)
            self.current_view = self.view_stack[-1]
            self.layout.addWidget(self.current_view)

    def toggle_window(self):
        # just propgate
        self.on_input_changed(self.input_bar.text())
        # handle visibility
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.input_bar.setFocus()

    def start_hotkey_listener(self):
        # Define the hotkey: Command (cmd) + Option (alt) + Space
        current_keys = set()

        def on_press(key):
            current_keys.add(key)
            # if any of the keys in the hotkey config are in the current keys, emit the hotkey pressed signal
            for combo, action in self.hotkey_config.items():
                if all(k in current_keys for k in combo):
                    self.hotkey_pressed.emit(action)

        def on_release(key):
            if key in current_keys:
                current_keys.remove(key)

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def on_hotkey(self, action: HotkeyAction):
        print(f"Hotkey {action} was pressed globally!")

        if action == HotkeyAction.TOGGLE_WINDOW:
            self.toggle_window()

    def on_input_changed(self, text):
        # Pass "props" to the current view if it supports set_filter_text
        if hasattr(self.current_view, "set_filter_text"):
            self.current_view.set_filter_text(text)

    def eventFilter(self, obj, event):
        if obj == self.input_bar and event.type() == QEvent.KeyPress:
            key = event.key()
            text = event.text()
            # Handle Escape: clear, pop view, or toggle window
            if key == Qt.Key_Escape:
                if self.input_bar.text():
                    self.input_bar.clear()
                elif len(self.view_stack) > 1:
                    self.pop_view()
                else:
                    self.toggle_window()
                return True
            # Handle Up/Down: forward to current view
            if key in (Qt.Key_Up, Qt.Key_Down):
                if self.current_view is not None:
                    from PySide6.QtCore import QCoreApplication

                    QCoreApplication.sendEvent(self.current_view, event)
                    return True
            # Allow text input and backspace
            if (text and text.isprintable()) or key == Qt.Key_Backspace:
                return False  # Let QLineEdit handle it
            # Otherwise, forward the event to the current view
            if self.current_view is not None:
                from PySide6.QtCore import QCoreApplication

                QCoreApplication.sendEvent(self.current_view, event)
                return True
        return super().eventFilter(obj, event)

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate:
            self.input_bar.selectAll()
            self.hide()
        return super().event(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    sys.exit(app.exec())
