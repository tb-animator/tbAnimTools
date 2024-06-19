from . import *

class Header(QLabel):
    """
    label with wordwrap
    """

    def __init__(self, label=str()):
        super(Header, self).__init__()
        self.setText(label)
        self.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

class SubHeader(QLabel):
    """
    label with wordwrap
    """

    def __init__(self, label=str()):
        super(SubHeader, self).__init__()
        self.setText(label)
        self.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)


class infoLabel(QLabel):
    def __init__(self, textLines=list()):
        super(infoLabel, self).__init__()
        text = str()
        for line in textLines:
            text += line + '\n'
        self.setText(text)
        self.setWordWrap(True)

class QBoldLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super(QLabel).__init__(*args, **kwargs)

class DropShadowLabel(QLabel):

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setCompositionMode(qp.CompositionMode_Source)
        qp.setRenderHint(QPainter.Antialiasing)
        lineColor = QColor(32, 32, 32, 32)
        fillColor = QColor(198, 198, 198)
        path = QPainterPath()
        pen = QPen()
        brush = QBrush()
        font = defaultFont()

        pen.setWidth(3.5)
        pen.setColor(lineColor)
        brush.setColor(fillColor)
        qp.setFont(font)
        qp.setPen(pen)

        fontMetrics = QFontMetrics(font)
        pixelsWide = fontMetrics.width(self.text())
        pixelsHigh = fontMetrics.height()

        path.addText(0, pixelsHigh, font, self.text())

        pen = QPen(lineColor, 6.5, Qt.SolidLine, Qt.RoundCap)
        pen2 = QPen(lineColor, 3.5, Qt.SolidLine, Qt.RoundCap)
        brush = QBrush(fillColor)
        qp.setCompositionMode(qp.CompositionMode_SourceOver)
        qp.strokePath(path, pen)
        qp.strokePath(path, pen2)
        qp.fillPath(path, brush)
        qp.end()