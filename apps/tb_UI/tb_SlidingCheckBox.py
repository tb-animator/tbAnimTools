from . import *

class AnimatedCheckBox(QCheckBox):
    def __init__(self,
                 text='on',
                 offText='Off',
                 checked=False,
                 width=80,
                 height=16,
                 bg_color="#777",
                 circle_color="#DDD",
                 active_color="#ffaa00",
                 animation_curve=QEasingCurve.InOutCirc):
        super(AnimatedCheckBox, self).__init__(text)
        self.setChecked(checked)
        self.setFixedWidth(width * dpiScale())
        self.setFixedHeight(height * dpiScale())
        self.setCursor(Qt.PointingHandCursor)

        # colors
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        # spacing
        self.margin = 2
        # create animation
        self._handlePosition = self.margin

        self.animation = QPropertyAnimation(self, b"handlePosition", self)
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(500)
        # connect state change
        self.stateChanged.connect(self.start_transition)

        self.onText = text
        self.offText = offText

        self.start_transition(checked)

    # create and set property
    @Property(float)
    def handlePosition(self):
        return self._handlePosition

    @handlePosition.setter
    def handlePosition(self, pos):
        self._handlePosition = pos
        self.update()

    def start_transition(self, value):
        self.animation.stop()
        circleSize = self.height() - self.margin - self.margin
        if value:
            self.animation.setEndValue(self.width() - circleSize - self.margin)
        else:
            self.animation.setEndValue(self.margin)

        self.animation.start()

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        # set painter
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        font = boldFont()
        # set no pen
        p.setPen(Qt.NoPen)
        p.setFont(font)
        fontMetrics = QFontMetrics(font)

        # rectangle
        rect = QRect(0, 0, self.width(), self.height())

        circleSize = self.height() - self.margin - self.margin

        if not self.isChecked():
            # draw bg
            p.setBrush(QColor(self._bg_color))
            p.drawRoundedRect(0, 0, rect.width(), self.height(), self.height() / 2, self.height() / 2)

            # draw circle
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._handlePosition, self.margin, circleSize, circleSize)

            # draw text
            pixelsWide = fontMetrics.boundingRect(self.offText).width()
            pixelsHigh = fontMetrics.boundingRect(self.offText).height()
            text_rect = QRect(self._handlePosition + circleSize + self.margin, self.margin, pixelsWide, circleSize)
            p.setPen(Qt.black)
            p.drawText(text_rect, Qt.AlignCenter, self.offText)

        else:
            # draw bg
            p.setBrush(QColor(self._active_color))
            p.drawRoundedRect(0, 0, rect.width(), self.height(), self.height() / 2, self.height() / 2)

            # draw circle
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._handlePosition, self.margin, circleSize, circleSize)

            # draw text
            pixelsWide = fontMetrics.boundingRect(self.onText).width()
            pixelsHigh = fontMetrics.boundingRect(self.onText).height()
            text_rect = QRect(self._handlePosition - self.margin - pixelsWide, self.margin, pixelsWide, circleSize)
            p.setPen(Qt.black)
            p.drawText(text_rect, Qt.AlignCenter, self.onText)
        # end
        p.end()