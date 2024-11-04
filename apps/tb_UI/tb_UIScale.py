from . import *
import colorsys

LIGHTTHRESHOLD = 128


def dpiScale(optionName='tbCustomDpiScale'):
    if not get_option_var('tbUseWindowsScale', True):
        return QApplication.primaryScreen().logicalDotsPerInch() / 96.0
    return QApplication.primaryScreen().logicalDotsPerInch() / 96.0 * get_option_var(optionName, 1)


def dpiFontScale():
    if not get_option_var('tbUseFontScale', True):
        return QApplication.primaryScreen().logicalDotsPerInch() / 96.0
    return get_option_var('tbCustomFontScale', 1)


def defaultFont():
    font = QFont("Console", 10 / dpiFontScale(), 10 / dpiFontScale(), QFont.DemiBold)
    # font.setStrikeOut(True)
    font.setStyleHint(QFont.Courier, QFont.PreferAntialias)
    return font


def boldFont():
    return QFont("Segoe UI", 10 / dpiFontScale(), QFont.Bold)

def semiBoldFont():
    return QFont("Segoe UI", 10 / dpiFontScale(), QFont.DemiBold)

def adjust_color_lightness(r, g, b, factor):
    h, l, s = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def darken_color(colour, factor=0.1):
    return adjust_color_lightness(colour[0], colour[1], colour[2], 1 - factor)


def hex_to_rgb(value):
    """
    Return (red, green, blue) for the color given as #rrggbb.
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(colour=[0.5, 0.5, 0.5]):
    return "#%02x%02x%02x" % (int(colour[0]), int(colour[1]), int(colour[2]))

def getColourBasedOnRGB(inputColour, lightColour, darkColour):
    hls = colorsys.rgb_to_hls(inputColour[0], inputColour[1], inputColour[2])
    isLight = hls[1] > LIGHTTHRESHOLD
    if isLight:
        return darkColour, False
    return lightColour, True

def darken_hex_color(hex_color, percentage):
    # Convert the hex color to an RGB tuple
    rgb_color = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))

    # Darken each channel by the specified percentage
    darkened_rgb = [int(channel * (1 - percentage / 100)) for channel in rgb_color]

    # Convert the darkened RGB back to a hex color
    darkened_hex_color = "#{:02X}{:02X}{:02X}".format(*darkened_rgb)

    return darkened_hex_color

def generate_linear_gradient(start_color, end_color, num_steps):
    # Convert the start and end colors to RGB tuples
    start_color = tuple(int(start_color[i:i + 2], 16) for i in (1, 3, 5))
    end_color = tuple(int(end_color[i:i + 2], 16) for i in (1, 3, 5))

    # Calculate the step size for each color channel
    step_size = [(end_color[i] - start_color[i]) / (num_steps - 1) for i in range(3)]

    # Generate the gradient colors
    gradient_colors = []
    for step in range(num_steps):
        color = [
            int(start_color[i] + step * step_size[i]) for i in range(3)
        ]
        hex_color = "#{:02X}{:02X}{:02X}".format(*color)
        gradient_colors.append(hex_color)

    return gradient_colors
