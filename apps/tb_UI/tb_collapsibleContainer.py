from . import *


class CollpasingContainerHeader(QWidget):
    """Header class for collapsible group"""

    def __init__(self, name, content_widget):
        """Header Class Constructor to initialize the object.

        Args:
            name (str): Name for the header
            content_widget (QtWidgets.QWidget): Widget containing child elements
        """
        super(CollpasingContainerHeader, self).__init__()
        self.content = content_widget
        self.expand_ico = QPixmap(":teDownArrow.png")
        self.collapse_ico = QPixmap(":teRightArrow.png")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        stacked = QStackedLayout(self)
        stacked.setStackingMode(QStackedLayout.StackAll)
        background = QLabel()
        background.setStyleSheet("QLabel{ background-color: rgb(93, 93, 93); border-radius:2px}")

        widget = QWidget()
        layout = QHBoxLayout(widget)

        self.icon = QLabel()
        self.icon.setPixmap(self.expand_ico)
        layout.addWidget(self.icon)
        layout.setContentsMargins(11, 0, 11, 0)

        font = QFont()
        font.setBold(True)
        label = QLabel(name)
        label.setFont(font)

        layout.addWidget(label)
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        stacked.addWidget(widget)
        stacked.addWidget(background)
        background.setMinimumHeight(layout.sizeHint().height() * 1.5)

    def mousePressEvent(self, *args):
        """Handle mouse events, call the function to toggle groups"""
        self.expand() if not self.content.isVisible() else self.collapse()

    def expand(self):
        self.content.setVisible(True)
        self.icon.setPixmap(self.expand_ico)

    def collapse(self):
        self.content.setVisible(False)
        self.icon.setPixmap(self.collapse_ico)


class CollapsingContainer(QGroupBox):
    """Class for creating a collapsible group similar to how it is implement in Maya

        Examples:
            Simple example of how to add a Container to a QVBoxLayout and attach a QGridLayout

            >>> layout = QVBoxLayout()
            >>> container = CollapsingContainer("Group")
            >>> layout.addWidget(container)
            >>> content_layout = QGridLayout(container.contentWidget)
            >>> content_layout.addWidget(QPushButton("Button"))
    """
    def __init__(self, name, useBackgroundColour=False):
        """Container Class Constructor to initialize the object

        Args:
            name (str): Name for the header
            useBackgroundColour (bool): whether or not to color the background lighter like in maya
        """
        super(CollapsingContainer, self).__init__()
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self._content_widget = CollapsingContainerBackground()
        if useBackgroundColour:
            self._content_widget.setStyleSheet(".CollapsingContainerBackground{background-color: rgb(73, 73, 73); "
                                               "margin-left: 2px; margin-right: 2px}")
        header = CollpasingContainerHeader(name, self._content_widget)
        self.mainLayout.addWidget(header)
        self.mainLayout.addWidget(self._content_widget)

        # assign header methods to instance attributes so they can be called outside of this class
        self.collapse = header.collapse
        self.expand = header.expand
        self.toggle = header.mousePressEvent

    @property
    def contentWidget(self):
        """Getter for the content widget

        Returns: Content widget
        """
        return self._content_widget

class CollapsingContainerBackground(QWidget):
    pass
