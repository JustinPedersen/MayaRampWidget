import re
import sys

from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance


from functools import partial

import maya.cmds as cmds
import maya.OpenMayaUI as omui


from ramp_widget import Ramp


def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


# noinspection PyAttributeOutsideInit
class RampDemoWindow(QtWidgets.QDialog):
    WINDOW_TITLE = "Ramp Demo"

    def __init__(self, parent=maya_main_window()):
        super(RampDemoWindow, self).__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        if cmds.about(ntOS=True):
            self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        elif cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.setMinimumWidth(30)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.resize(400, 400)

        # Force the ui to update with the currently selected marker
        self.set_base_ui_state(self.ramp.current_selected_marker)

    def create_widgets(self):

        # Ramp widget
        self.ramp = Ramp()

        # Value control widgets
        self.value_control_groupbox = QtWidgets.QGroupBox('Value')
        self.value_label = QtWidgets.QLabel('U Value')
        self.value_spin = QtWidgets.QDoubleSpinBox()
        self.value_spin.setRange(0.0, 1.0)
        self.value_spin.setSingleStep(0.01)

        # Colour control widgets
        self.colour_control_groupbox = QtWidgets.QGroupBox('Color')
        self.colour_preview_label = QtWidgets.QLabel()
        self.colour_preview_label.setMinimumHeight(30)
        self.hex_line_edit = QtWidgets.QLineEdit()

        # -- Labels
        self.r_label = QtWidgets.QLabel('R')
        self.g_label = QtWidgets.QLabel('G')
        self.b_label = QtWidgets.QLabel('B')

        # -- Sliders
        self.r_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.g_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.b_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        # -- Slider Settings
        self.r_slider.setRange(0, 255)
        self.g_slider.setRange(0, 255)
        self.b_slider.setRange(0, 255)

        # -- Spin Boxes
        self.r_spin_box = QtWidgets.QSpinBox()
        self.g_spin_box = QtWidgets.QSpinBox()
        self.b_spin_box = QtWidgets.QSpinBox()

        # --- Spin Box Settings
        self.r_spin_box.setRange(0, 255)
        self.g_spin_box.setRange(0, 255)
        self.b_spin_box.setRange(0, 255)

    def create_layout(self):
        # Create the root layout
        root_layout = QtWidgets.QVBoxLayout()
        self.setLayout(root_layout)

        # Value control box layout
        value_control_layout = QtWidgets.QVBoxLayout()
        self.value_control_groupbox.setLayout(value_control_layout)
        value_h_layout = QtWidgets.QHBoxLayout()
        value_control_layout.addLayout(value_h_layout)
        value_h_layout.addWidget(self.value_label)
        value_h_layout.addWidget(self.value_spin)


        # Colour control box layout
        colour_control_layout = QtWidgets.QVBoxLayout()
        self.colour_control_groupbox.setLayout(colour_control_layout)

        # Add Preview bits
        colour_control_layout.addWidget(self.colour_preview_label)
        colour_control_layout.addWidget(self.hex_line_edit)

        # Add sliders to their layouts
        r_layout = QtWidgets.QHBoxLayout()
        r_layout.addWidget(self.r_label)
        r_layout.addWidget(self.r_slider)
        r_layout.addWidget(self.r_spin_box)

        g_layout = QtWidgets.QHBoxLayout()
        g_layout.addWidget(self.g_label)
        g_layout.addWidget(self.g_slider)
        g_layout.addWidget(self.g_spin_box)

        b_layout = QtWidgets.QHBoxLayout()
        b_layout.addWidget(self.b_label)
        b_layout.addWidget(self.b_slider)
        b_layout.addWidget(self.b_spin_box)

        # Add sliders to the layout
        colour_control_layout.addLayout(r_layout)
        colour_control_layout.addLayout(g_layout)
        colour_control_layout.addLayout(b_layout)

        # Add everything to the root
        root_layout.addWidget(self.ramp)
        root_layout.addWidget(self.value_control_groupbox)
        root_layout.addWidget(self.colour_control_groupbox)

    def create_connections(self):
        """
        Create all the connections needed within the UI
        """
        # When sliders are updated, update the corresponding spin box
        self.r_slider.valueChanged.connect(partial(self.on_colour_value_changed, self.r_spin_box))
        self.g_slider.valueChanged.connect(partial(self.on_colour_value_changed, self.g_spin_box))
        self.b_slider.valueChanged.connect(partial(self.on_colour_value_changed, self.b_spin_box))

        # When spin boxes are updated, update the corresponding slider
        self.r_spin_box.valueChanged.connect(partial(self.on_colour_value_changed, self.r_slider))
        self.g_spin_box.valueChanged.connect(partial(self.on_colour_value_changed, self.g_slider))
        self.b_spin_box.valueChanged.connect(partial(self.on_colour_value_changed, self.b_slider))

        # Hex line edit
        self.hex_line_edit.textEdited.connect(self.on_hex_value_set)

        # Value connections
        self.value_spin.valueChanged.connect(self.on_value_spin_changed)

        # Ramp connections
        self.ramp.marker_selected.connect(self.on_marker_selected)
        self.ramp.marker_moved.connect(self.on_marker_moved)

    def set_all_spin_boxes(self, r, g, b):
        """ Helper function to set all the spin boxes at once """
        self.r_spin_box.setValue(r)
        self.g_spin_box.setValue(g)
        self.b_spin_box.setValue(b)

    def set_all_sliders(self, r, g, b):
        """ Helper function to set all the sliders at once """
        self.r_slider.setValue(r)
        self.g_slider.setValue(g)
        self.b_slider.setValue(b)

    def current_hex(self):
        """
        :return: current RBG spin box values and return that as a hex value
        :rtype: str
        """
        r, g, b = self.r_spin_box.value(), self.g_spin_box.value(), self.b_spin_box.value()
        return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

    @classmethod
    def hex_to_rgb(cls, hex_value):
        """
        :param hex_value: Given a hex value convert it to an RGB value
        :return: rgb value
        :rtype: tuple|None
        """
        match = re.search(r'^(#)?(.{6})$', hex_value)
        if match:
            return tuple(int(match.group(2)[i:i + 2], 16) for i in (0, 2, 4))

    def update_colour_preview(self, hex_value=None):
        """
        Change the current colour label preview to what the current slider and spin box values are set to.

        :param hex_value: Optional, if present set the colour preview to this hex value
        """
        # Get the hex value of the current UI state if its not given
        if not hex_value:
            hex_value = self.current_hex()
        self.colour_preview_label.setStyleSheet(f"background-color: {hex_value}")

    def on_colour_value_changed(self, target, value, update_marker=True):
        """
        Called when a slider or spin box has its value updated

        :param target: The UI element to update
        :param value: The value to update the other ui element to
        :param update_marker: If True will update the currently selected marker
        """
        target.setValue(value)
        current_hex = self.current_hex()
        self.update_colour_preview(current_hex)
        self.hex_line_edit.setText(current_hex)

        if update_marker:
            self.ramp.edit_current_marker(new_color=current_hex)

    def on_hex_value_set(self, hex_value):
        """
        Called when the hex value is edited within the UI. We parse the hex value to see if it is valid
        and if it is, then update the UI with the RGB values pulled from it.

        :param hex_value: Text placed into the UI
        """
        # check that the user has input a valid hex value
        rgb = self.hex_to_rgb(hex_value)
        if rgb:
            self.set_all_spin_boxes(*rgb)
        else:
            print(f'Warning: Invalid hex value given: {hex_value}')

    def on_marker_selected(self, marker):
        """
        Called when a marker on the ramp is selected. We need to update the UI to match the newly selected colour
        :param marker:
        :return:
        """

        # Setting the spin boxes also updates the sliders so we only have to do one
        self.set_all_spin_boxes(*self.hex_to_rgb(marker.color))

        # Set the U Value
        self.value_spin.setValue(marker.u_value)

    def on_marker_moved(self, marker):
        """
        Called when a marker is moved
        :param marker: The marker that is currently being moved
        """
        self.value_spin.setValue(marker.u_value)

    def on_value_spin_changed(self):
        """
        Called when the value spin is updated
        """
        u_value = self.value_spin.value()
        self.ramp.edit_current_marker(new_u_value=u_value)

    def set_base_ui_state(self, maker):
        """
        Helper function to set the base pass of the UI
        """
        hex_value = maker.color
        self.set_all_spin_boxes(*self.hex_to_rgb(hex_value))
        self.update_colour_preview(hex_value)
        self.hex_line_edit.setText(hex_value)


def main():
    """
    To demo the ramp widget within Maya run this function
    """
    try:
        # noinspection PyUnboundLocalVariable
        ramp_demo_window.close()
        ramp_demo_window.deleteLater()
    except:
        pass

    ramp_demo_window = RampDemoWindow()
    ramp_demo_window.show()
