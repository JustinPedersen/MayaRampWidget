import json
import re
import sys
from functools import partial

import maya.OpenMayaUI as omui
import maya.cmds as cmds

import ramp_widget
from qt import QtCore
from qt import QtGui
from qt import QtWidgets
from qt import wrapInstance

WINDOW_TITLE = "CurveColourRamper"


def maya_main_window() -> QtWidgets.QWidget:
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


# noinspection PyAttributeOutsideInit
class CurveColourRamper(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(CurveColourRamper, self).__init__(parent)
        self.setObjectName(WINDOW_TITLE)
        self.setWindowTitle(WINDOW_TITLE)

        if cmds.about(ntOS=True):
            self.setWindowFlags(
                self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint
            )
        elif cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.setMinimumWidth(30)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.resize(400, 600)

        # Force the ui to update with the currently selected marker
        self.set_base_ui_state(self.ramp.current_selected_marker)

    def create_widgets(self) -> None:
        """
        Create all widgets required for the window
        """
        # Ramp widget
        self.ramp = ramp_widget.Ramp()

        # Value control widgets
        self.value_control_groupbox = QtWidgets.QGroupBox("Value")
        self.value_label = QtWidgets.QLabel("U Value")
        self.value_spin = QtWidgets.QDoubleSpinBox()
        self.value_spin.setRange(0.0, 1.0)
        self.value_spin.setSingleStep(0.01)
        self.value_spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        # Colour control widgets
        self.colour_control_groupbox = QtWidgets.QGroupBox("Color")
        self.colour_preview_label = QtWidgets.QLabel()
        self.colour_preview_label.setMinimumHeight(30)
        self.hex_line_edit = QtWidgets.QLineEdit()

        # -- Labels
        self.r_label = QtWidgets.QLabel("R")
        self.g_label = QtWidgets.QLabel("G")
        self.b_label = QtWidgets.QLabel("B")

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
        self.r_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.g_spin_box.setRange(0, 255)
        self.g_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.b_spin_box.setRange(0, 255)
        self.b_spin_box.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        # -- IO Buttons
        self.io_groupbox = QtWidgets.QGroupBox("Gradient IO")
        self.export_ramp_button = QtWidgets.QPushButton("Export")
        self.import_ramp_button = QtWidgets.QPushButton("Import")

        # -- Set Curve Colour Buttons
        self.set_curve_colour_button = QtWidgets.QPushButton("Set Curves Colour")

    def create_layout(self) -> None:
        """
        Create all layouts required for the window and parent widgets to them
        """
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

        # IO Groupbox
        io_buttons_layout = QtWidgets.QHBoxLayout()
        self.io_groupbox.setLayout(io_buttons_layout)
        io_buttons_layout.addWidget(self.import_ramp_button)
        io_buttons_layout.addWidget(self.export_ramp_button)

        # Add everything to the root
        root_layout.addWidget(self.ramp)
        root_layout.addWidget(self.value_control_groupbox)
        root_layout.addWidget(self.colour_control_groupbox)
        root_layout.addWidget(self.io_groupbox)
        root_layout.addWidget(self.set_curve_colour_button)

    def create_connections(self) -> None:
        """
        Create all the connections needed within the UI
        """
        # When sliders are updated, update the corresponding spin box
        self.r_slider.valueChanged.connect(
            partial(self.on_colour_value_changed, self.r_spin_box)
        )
        self.g_slider.valueChanged.connect(
            partial(self.on_colour_value_changed, self.g_spin_box)
        )
        self.b_slider.valueChanged.connect(
            partial(self.on_colour_value_changed, self.b_spin_box)
        )

        # When spin boxes are updated, update the corresponding slider
        self.r_spin_box.valueChanged.connect(
            partial(self.on_colour_value_changed, self.r_slider)
        )
        self.g_spin_box.valueChanged.connect(
            partial(self.on_colour_value_changed, self.g_slider)
        )
        self.b_spin_box.valueChanged.connect(
            partial(self.on_colour_value_changed, self.b_slider)
        )

        # Hex line edit
        self.hex_line_edit.textEdited.connect(self.on_hex_value_set)

        # Value connections
        self.value_spin.valueChanged.connect(self.on_value_spin_changed)

        # Ramp connections
        self.ramp.marker_selected.connect(self.on_marker_selected)
        self.ramp.marker_moved.connect(self.on_marker_moved)

        # IO
        self.import_ramp_button.clicked.connect(self.on_import_clicked)
        self.export_ramp_button.clicked.connect(self.on_export_clicked)
        self.set_curve_colour_button.clicked.connect(self.on_set_curve_colour)

    def set_all_spin_boxes(self, r: float, g: float, b: float) -> None:
        """Helper function to set all the spin boxes at once"""
        self.r_spin_box.setValue(r)
        self.g_spin_box.setValue(g)
        self.b_spin_box.setValue(b)

    def set_all_sliders(self, r: float, g: float, b: float) -> None:
        """Helper function to set all the sliders at once"""
        self.r_slider.setValue(r)
        self.g_slider.setValue(g)
        self.b_slider.setValue(b)

    def current_hex(self) -> str:
        """
        :return: current RBG spin box values and return that as a hex value
        :rtype: str
        """
        r, g, b = (
            self.r_spin_box.value(),
            self.g_spin_box.value(),
            self.b_spin_box.value(),
        )
        return "#{0:02x}{1:02x}{2:02x}".format(r, g, b)

    @classmethod
    def hex_to_rgb(cls, hex_value: str, normalised: bool = False) -> tuple:
        """
        :param hex_value: Given a hex value convert it to an RGB value
        :param normalised: If True, returns values in 0.0-1.0 range instead of 0-255
        :return: rgb value
        :rtype: tuple
        """
        match = re.search(r"^(#)?(.{6})$", hex_value)
        if match:
            rgb = tuple(int(match.group(2)[i : i + 2], 16) for i in (0, 2, 4))
            return tuple(c / 255.0 for c in rgb) if normalised else rgb

        raise ValueError(f"Could not convert hex value {hex_value} to RGB")

    def update_colour_preview(self, hex_value: str = None) -> None:
        """
        Change the current colour label preview to what the current slider and spin box values are set to.

        :param hex_value: Optional, if present set the colour preview to this hex value
        """
        # Get the hex value of the current UI state if its not given
        if not hex_value:
            hex_value = self.current_hex()
        self.colour_preview_label.setStyleSheet(f"background-color: {hex_value}")

    def on_colour_value_changed(
        self, target: QtWidgets.QWidget, value: float, update_marker: bool = True
    ) -> None:
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
            self.ramp.edit_marker(new_color=current_hex)

    def on_hex_value_set(self, hex_value: str) -> None:
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
            print(f"Warning: Invalid hex value given: {hex_value}")

    def on_marker_selected(self, marker: ramp_widget.Marker) -> None:
        """
        Called when a marker on the ramp is selected. We need to update the UI to match the newly selected colour
        :param marker:
        :return:
        """

        # Setting the spin boxes also updates the sliders so we only have to do one
        self.set_all_spin_boxes(*self.hex_to_rgb(marker.color))

        # Set the U Value
        self.value_spin.setValue(marker.u_value)

    def on_marker_moved(self, marker: ramp_widget.Marker) -> None:
        """
        Called when a marker is moved
        :param marker: The marker that is currently being moved
        """
        self.value_spin.setValue(marker.u_value)

    def on_value_spin_changed(self) -> None:
        """
        Called when the value spin is updated
        """
        u_value = self.value_spin.value()
        self.ramp.edit_marker(new_u_value=u_value)

    def set_base_ui_state(self, maker: ramp_widget.Marker) -> None:
        """
        Helper function to set the base pass of the UI
        """
        hex_value = maker.color
        self.set_all_spin_boxes(*self.hex_to_rgb(hex_value))
        self.update_colour_preview(hex_value)
        self.hex_line_edit.setText(hex_value)

    def on_import_clicked(self) -> None:
        """
        Prompt the user to select a JSON file and return its contents.
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        # JSON keys are always strings, cast back to float for set_markers
        self.ramp.set_markers({float(k): v for k, v in data.items()})

    def on_export_clicked(self) -> None:
        """
        Prompt the user for a save location and export the data as JSON.
        """
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(self.ramp.markers, handle, indent=4)

    def on_set_curve_colour(self) -> None:
        """
        Set the colour on the currently selected curves
        """
        transforms = sorted([t for t in cmds.ls(sl=True, type="transform")])
        total_shapes = len(transforms)

        for i, t in enumerate(transforms):
            shapes = cmds.listRelatives(t, shapes=True)

            u_value = i / (total_shapes - 1) if total_shapes > 1 else 0.0
            colour = self.hex_to_rgb(
                self.ramp.color_at_u_value(u_value), normalised=True
            )
            for shape in shapes:
                cmds.setAttr(f"{shape}.overrideEnabled", 1)
                cmds.setAttr(f"{shape}.overrideRGBColors", 1)
                cmds.setAttr(
                    f"{shape}.overrideColorRGB", colour[0], colour[1], colour[2]
                )


1


def main():
    """
    To demo the ramp widget within Maya run this function
    """

    maya_window = maya_main_window()
    existing_window = maya_window.findChild(QtWidgets.QWidget, WINDOW_TITLE)

    if existing_window:
        existing_window.close()
        existing_window.deleteLater()

    window = CurveColourRamper()
    window.show()
