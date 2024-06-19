from . import *

class OverlayContents(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.button = QPushButton("Close Overlay")
        self.button2 = QPushButton("Close Overlay")
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.button)
        self.layout().addWidget(self.button2)

        self.button.clicked.connect(self.hideOverlay)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 4 * dpiScale(), 4 * dpiScale())
        # mask = QRegion(path.toFillPolygon().toPolygon())
        pen = QPen(Qt.white, .2)
        linePen = QPen(Qt.white, 2, Qt.SolidLine)

        painter.setPen(linePen)
        painter.drawLine(0, 0, 200, 200)

        painter.setPen(pen)
        painter.fillPath(path, Qt.white)
        painter.drawPath(path)
        painter.end()

    def hideOverlay(self):
        self.parent().hide()


class Overlay(QWidget):
    def __init__(self, parent, widget):
        QWidget.__init__(self, parent)
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

        self.widget = widget
        self.widget.setParent(self)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(0, 0, 0, 127)))
        painter.end()

    def resizeEvent(self, event):
        position_x = (self.frameGeometry().width() - self.widget.frameGeometry().width()) / 2
        position_y = (self.frameGeometry().height() - self.widget.frameGeometry().height()) / 2

        self.widget.move(position_x, position_y)
        event.accept()

class TranslucentWidgetSignals(QObject):
    # SIGNALS
    CLOSE = Signal()

class TranslucentWidget(QWidget):
    def __init__(self, parent=None, text='Default text', hasButton=False):
        super(TranslucentWidget, self).__init__(parent)

        # text
        self.text = text
        # make the window frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.fillColor = QColor(30, 30, 30, 160)
        self.penColor = QColor("#333333")

        self.popup_fillColor = QColor(160, 160, 160, 255)
        self.popup_penColor = QColor(100, 100, 100, 255)
        font = QFont()
        font.setPixelSize(18)
        font.setBold(True)
        self.close_btn = None
        if hasButton:
            self.close_btn = QPushButton(self)
            self.close_btn.setText("x")
            self.close_btn.setFont(font)
            self.close_btn.setStyleSheet("background-color: rgb(0, 0, 0, 0)")
            self.close_btn.setFixedSize(30, 30)
            self.close_btn.clicked.connect(self._onclose)

        self.SIGNALS = TranslucentWidgetSignals()

    def resizeEvent(self, event):
        s = self.size()
        popup_width = 300
        popup_height = 120
        ow = int(s.width() / 2 - popup_width / 2)
        oh = int(s.height() / 2 - popup_height / 2)
        if self.close_btn:
            self.close_btn.move(ow + 265, oh + 5)
        self.label.move(ow + 32, oh)

    def paintEvent(self, event):
        # This method is, in practice, drawing the contents of
        # your window.

        # get current window size
        s = self.size()
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        qp.setPen(self.penColor)
        qp.setBrush(self.fillColor)
        qp.drawRect(0, 0, s.width(), s.height())

        # drawpopup
        qp.setPen(self.popup_penColor)
        qp.setBrush(self.popup_fillColor)
        popup_width = 300
        popup_height = 120
        ow = int(s.width()/2-popup_width/2)
        oh = int(s.height()/2-popup_height/2)
        qp.drawRoundedRect(ow, oh, popup_width, popup_height, 5, 5)

        font = QFont()
        font.setPixelSize(18)
        font.setBold(True)
        qp.setFont(font)
        qp.setPen(QColor(70, 70, 70))
        tolw, tolh = 80, -5
        qp.drawText(ow + int(popup_width/2) - tolw, oh + int(popup_height/2) - tolh, self.text)

        qp.end()

    def _onclose(self):
        print("Close")
        self.SIGNALS.CLOSE.emit()