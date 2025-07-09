from enum import Enum, auto
from PySide6.QtWidgets import QWidget, QListWidget, QVBoxLayout
from PySide6.QtCore import Signal
from typing import List
from PySide6.QtCore import Qt


class ListItemType(Enum):
    APPLICATION = auto()
    COMMAND = auto()


class ListItem:
    def __init__(self, label: str, type: ListItemType):
        self.label = label
        self.type = type
        # TODO: add icon support
        self.icon = None


class ListFilterView(QWidget):
    filter_text = Signal(str)

    def __init__(self, items: List[ListItem]):
        super().__init__()
        self.items = items
        self.list_widget = QListWidget(self)
        for item in self.items:
            self.list_widget.addItem(item.label)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.list_widget)
        self.list_widget.setCurrentRow(0)

    def filter(self, text):
        self.list_widget.clear()
        filtered = [item for item in self.items if text.lower() in item.label.lower()]
        for item in filtered:
            self.list_widget.addItem(item.label)

    def set_filter_text(self, text):
        self.filter(text)

    def keyPressEvent(self, event):
        key = event.key()
        current_row = self.list_widget.currentRow()
        count = self.list_widget.count()
        if key == Qt.Key_Up:
            if current_row > 0:
                self.list_widget.setCurrentRow(current_row - 1)
        elif key == Qt.Key_Down:
            if current_row < count - 1:
                self.list_widget.setCurrentRow(current_row + 1)
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            item = self.list_widget.currentItem()
            if item is not None:
                print(f"Selected: {item.text()}")
        else:
            super().keyPressEvent(event)
