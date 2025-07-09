from enum import Enum, auto
from PySide6.QtWidgets import QWidget, QListWidget, QVBoxLayout
from PySide6.QtCore import Signal
from typing import List, Callable
from PySide6.QtCore import Qt


class ListItemType(Enum):
    APPLICATION = auto()
    COMMAND = auto()


class ListItem:
    def __init__(self, label: str, type: ListItemType, action: Callable | None = None):
        self.label = label
        self.type = type
        # TODO: add icon support
        self.icon = None
        self.action = action

    def __str__(self):
        return f"{self.label} - {self.type} - {self.action}"

    def __repr__(self):
        return self.__str__()


class ListFilterView(QWidget):
    filter_text = Signal(str)

    def __init__(self, items: List[ListItem]):
        super().__init__()
        self.items = items
        self.filtered_items = items.copy()
        self.list_widget = QListWidget(self)
        for item in self.filtered_items:
            self.list_widget.addItem(item.label)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.list_widget)
        self.list_widget.setCurrentRow(0)

    def filter(self, text):
        self.list_widget.clear()
        self.filtered_items = [
            item for item in self.items if text.lower() in item.label.lower()
        ]
        for item in self.filtered_items:
            self.list_widget.addItem(item.label)
        if self.filtered_items:
            self.list_widget.setCurrentRow(0)

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
            print("CURRENT ROW", current_row)
            print("CURRENT ITEM", item)
            if item is not None and self.filtered_items:
                item = self.filtered_items[current_row]
                if item.action is not None:
                    item.action()
        else:
            super().keyPressEvent(event)
