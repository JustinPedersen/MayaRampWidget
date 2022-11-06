import re
import math

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets


class Marker:
    """
    Holder Class for all markers that form part of the Ramp.
    Simply tracks metadata about them. Some convenience functions included too.
    """

    def __init__(self, data=None):
        self.color = '#000000'
        self.u_value = 0.0
        self.selected = False
        self.position = None
        self.drag_position = QtCore.QPoint(0, 0)
        self.marker_size = 0
        self.marker_margin = 0
        self.del_rect_size = 0
        self.del_rect_position = None

        if data:
            self.set_values(data)

    @property
    def outline_color(self):
        return '#FFFFFF' if self.selected else '#000000'

    def set_values(self, data):
        self.color = data.get('color', self.color)
        self.u_value = data.get('u_value', self.u_value)
        self.selected = data.get('selected', self.selected)
        self.position = data.get('position', self.position)
        self.marker_size = data.get('marker_size', self.marker_size)
        self.marker_margin = data.get('marker_margin', self.marker_margin)
        self.del_rect_size = data.get('del_rect_size', self.del_rect_size)
        self.del_rect_position = data.get('del_rect_position', self.del_rect_position)

    def is_selected(self, point):
        """
        Given a QPoint decide if the Marker was selected or not using its Position
        """

        if self.position:
            # Calculate the distance between the known position and the point position
            distance = abs(
                math.hypot(
                    point.x() - self.position.x(),
                    point.y() - self.position.y()
                )
            )
            # If the distance is smaller than the circle marker then it was selected
            if distance <= (self.marker_size + self.marker_margin):
                return True

        return False

    def is_deleted(self, point):
        """
        Given a QPoint decide if the Marker was deleted
        """
        if self.del_rect_position:
            x = self.del_rect_position.x() - int(self.del_rect_size / 2)
            y = self.del_rect_position.y() - int(self.del_rect_size / 2)
            if QtCore.QRect(x, y, self.del_rect_size, self.del_rect_size).contains(point):
                return True
        return False

    def set_u_value(self, point, rect_size):
        """
        Given the start and end points of where the ramp is drawn and the
        point the user has their mouse pointer, work out the relative U value
        :param QPoint point: Where the mouse is
        :param rect_size: Tuple describing the x,y, width and height of the gradient rectangle.
        """

        relative_start = QtCore.QPoint(
            rect_size[0],
            point.y())
        relative_end = QtCore.QPoint(
            rect_size[0] + rect_size[2],
            point.y())

        # Calculate where the point is relative to the start and end positions
        u_value = (relative_end.x() - point.x()) / (relative_end.x() - relative_start.x())
        u_value = max(min(u_value, 1.0), 0.0)

        # Lastly we flip the value as its calculated with the 1.0 on the left, not sure why just yet
        self.u_value = 1.0 - u_value

    def get_pos_from_u_value(self, rect_size):
        """
        Get the relative marker position using the rect size and it's U value
        """
        start = rect_size[0]
        # Rect size [2] is width of the rectangle so we account for the start offset
        end = rect_size[0] + rect_size[2]
        return int((self.u_value * (end - start)) + start)


class Ramp(QtWidgets.QWidget):
    # ---------------------------------------------------------------------- #
    # SIGNALS
    # ---------------------------------------------------------------------- #
    marker_selected = QtCore.Signal(object)
    marker_deleted = QtCore.Signal(object)
    marker_moved = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super(Ramp, self).__init__(*args, **kwargs)

        self.circle_marker_size = 6
        self.circle_marker_margin = 1
        self.del_rect_size = 11

        self.horizontal_spacing = 20
        self.vertical_spacing = 40

        self.min_gradient_height = 30
        self.min_gradient_width = 100

        # Base properties all markers will hold by default
        self._basic_marker_data = {
            'color': '#000000',
            'u_value': 0.0,
            'marker_size': self.circle_marker_size,
            'marker_margin': self.circle_marker_margin,
            'del_rect_size': self.del_rect_size,
            'selected': False
        }

        # Data for starter markers
        starting_marker_data = [
            {'color': '#000000',
             'u_value': 0.0,
             'selected': True},
            {'color': '#ff0000',
             'u_value': 0.5},
            {'color': '#ffffff',
             'u_value': 1.0},
        ]

        # Create the base starter markers
        self._gradient = [
            Marker(self._basic_marker_data),
            Marker(self._basic_marker_data),
            Marker(self._basic_marker_data)
        ]

        # Set starter marker special properties
        for marker, marker_data in zip(self._gradient, starting_marker_data):
            marker.set_values(marker_data)

        # Set the current selection
        self._current_marker_selection = self._gradient[0]
        self._drag_marker = False

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

    # ---------------------------------------------------------------------- #
    # PROPERTIES
    # ---------------------------------------------------------------------- #

    @property
    def markers(self):
        """
        :returns: All markers present on the gradient. Namely their u value and color
        :rtype: list[{float:str}]
        """
        self._sort_gradient()
        return [{m.u_value: m.color} for m in self._gradient]

    @property
    def selected_marker_index(self):
        """
        :returns: the currently selected marker index
        :rtype: int
        """
        self._sort_gradient()
        return self._gradient.index(self._current_marker_selection)

    @property
    def current_selected_marker(self):
        """
        :returns: The currently selected marker
        """
        return self._current_marker_selection

    # ---------------------------------------------------------------------- #
    # PRIVATE METHODS
    # ---------------------------------------------------------------------- #

    def _update_marker_selection(self):
        """
        Helper method to make sure only the self._current_marker_selection is the only
        marker that has its selected property set to True.
        """
        if self._current_marker_selection:
            for marker in self._gradient:
                marker.selected = bool(marker == self._current_marker_selection)

    def _marker_selection(self, position):
        """
        Check through all the markers and see if the selection event selected one of them
        """
        # Check if the event selected a marker
        for marker in self._gradient:
            if marker.is_selected(position):
                # We have a selection, update the internals and also set the drag to enabled
                self._current_marker_selection = marker
                self._drag_marker = True
                self._update_marker_selection()
                self.repaint()
                self.marker_selected.emit(marker)
                return

            else:
                if marker.is_deleted(position):
                    # Delete the marker if we have more than 1 point on the gradient
                    if len(self._gradient) > 1:
                        self._delete_marker(marker)
                        self.repaint()
                        self.marker_deleted.emit(marker)
                    break

    def _add_marker(self, point):
        """
        Add a new marker to the gradient given a point so it's U value can be calculated
        :param QPoint point: Point where the mouse was clicked
        """
        # Deselect all the current markers
        for marker in self._gradient:
            marker.selected = False

        # Create the new marker and add it to the gradient
        new_marker = Marker(self._basic_marker_data)
        new_marker.selected = True

        # Calculate it's U value and colour at that position
        rect_data = self._get_gradient_rect_size()
        new_marker.set_u_value(point, rect_data)
        new_marker.color = self.color_at_u_value(new_marker.u_value)

        # Add the marker to the gradient
        self._gradient.append(new_marker)

        # Make the new marker the current selection, let the user drag it and emit that it's been selected.
        self._current_marker_selection = new_marker
        self._drag_marker = True
        self.marker_selected.emit(new_marker)

    def _delete_marker(self, marker):
        """
        Delete the given marker from the gradient and select the left most marker, if none
        exist to the left, select the right most marker.
        """
        self._drag_marker = False

        self._sort_gradient()

        # Select the closest marker
        marker_index = self._gradient.index(marker)
        new_marker_index = marker_index - 1 if marker_index >= 1 else marker_index + 1
        self._current_marker_selection = self._gradient[new_marker_index]
        self._update_marker_selection()

        # Delete the given marker
        self._gradient.remove(marker)
        self._sort_gradient()

        # Emit that the marker selection has been updated
        self.marker_selected.emit(self.current_selected_marker)

    def _get_gradient_rect_size(self, width=None, height=None):
        """
        Get the X, Y, Width and Height of the gradient rectangle to draw
        """

        if not width:
            width = self.width()

        if not height:
            height = self.height()

        return (
            self.horizontal_spacing,
            self.vertical_spacing,
            max((width - (self.horizontal_spacing * 2)), self.min_gradient_width),
            max((height - (self.vertical_spacing * 2)), self.min_gradient_height)
        )

    def _sort_gradient(self):
        """
        Sort the gradient by the U value of each marker
        :return:
        """
        self._gradient = sorted(self._gradient, key=lambda d: d.u_value)

    @classmethod
    def _combine_hex_values(cls, d):
        """
        Helper method to combine Hex Values
        :param d: dict of hex values and their weights to blend
        :return: blended Hex Value
        """
        d_items = sorted(d.items())
        tot_weight = sum(d.values())
        red = int(sum([int(k[1:3], 16) * v for k, v in d_items]) / tot_weight)
        green = int(sum([int(k[3:5], 16) * v for k, v in d_items]) / tot_weight)
        blue = int(sum([int(k[5:7], 16) * v for k, v in d_items]) / tot_weight)
        zpad = lambda x: x if len(x) == 2 else '0' + x
        return f'#{zpad(hex(red)[2:]) + zpad(hex(green)[2:]) + zpad(hex(blue)[2:])}'

    # ---------------------------------------------------------------------- #
    # PUBLIC METHODS
    # ---------------------------------------------------------------------- #

    def color_at_u_value(self, value):
        """
        Given the U value, return the color at that U Position on the ramp
        :param float value: value between 0.0 and 1.0
        :return: Hex Value for colour at the given value
        :rtype: str
        """
        # Make sure the gradient is sorted
        self._sort_gradient()

        # If the value is marked already just return that
        for marker in self._gradient:
            if value == marker.u_value:
                return marker.color

        # If the value is smaller than the smallest U value
        if value < self._gradient[0].u_value:
            return self._gradient[0].color

        # If the value is bigger than the largest U value
        if value > self._gradient[-1].u_value:
            return self._gradient[-1].color

        # If we are here the u value is between two markers and must be calculated.
        # Find the markers on either side of the given value
        l_marker, r_marker = None, None
        for i, marker in enumerate(self._gradient):
            if marker.u_value > value:
                r_marker = marker
                l_marker = self._gradient[i - 1]
                break

        # Work out the blend weightings for both markers relative to the given value
        l_blend = (value - l_marker.u_value) / (r_marker.u_value - l_marker.u_value)
        r_blend = 1.0 - l_blend

        # Blend the colours and return the new hex value
        return self._combine_hex_values({r_marker.color: l_blend, l_marker.color: r_blend})

    def add_marker(self, u_value, colour):
        """
        Add a new marker to the gradient
        """
        # Deselect all the current markers
        for marker in self._gradient:
            marker.selected = False

        # Create the new marker and add it to the gradient
        new_marker = Marker(self._basic_marker_data)
        new_marker.selected = True
        new_marker.u_value = u_value
        new_marker.color = colour

        # Add the marker to the gradient
        self._gradient.append(new_marker)
        self._sort_gradient()

        # Make the new marker the current selection, let the user drag it and emit that it's been selected.
        self._current_marker_selection = new_marker

        # redraw the UI
        self.repaint()

    def remove_marker(self, index=None, u_value=None):
        """
        Given either the index or u_value find the corresponding marker and remove it.
        Once the marker has been removed safely redraw the UI.
        :param int index: Index of the Marker to delete
        :param float u_value: Value of the marker to delete.
        """
        # Make sure the gradient is sorted
        self._sort_gradient()
        marker_to_delete = None

        # If given an index attempt to delete the marker at that value
        if index:
            len_gradient = len(self._gradient)
            if len_gradient == 1:
                raise IndexError('Gradient must have at least one marker')
            if len_gradient < index - 1:
                raise IndexError('Index out of gradient range')

            marker_to_delete = self._gradient[index]

        # If we are given a u_vale then find any marker that has it and delete it
        if u_value is not None:
            for marker in self._gradient:
                if marker.u_value == float(u_value):
                    marker_to_delete = marker

        # Delete the marker
        if marker_to_delete:
            self._delete_marker(marker_to_delete)
            self.repaint()
            self.marker_deleted.emit(marker_to_delete)

    def edit_marker(self, index, new_u_value=None, new_color=None):
        """
        Alter the properties of an existing marker.

        :param index: Index of the marker to edit
        :param new_u_value: If given will alter the U Value of the marker.
        :param new_color: If given will alter the colour of the marker.
        """

        # Verify the given index is valid
        len_gradient = len(self._gradient)
        if len_gradient == 1:
            raise IndexError('Gradient must have at least one marker')
        if len_gradient < index - 1:
            raise IndexError('Index out of gradient range')

        target_marker = self._gradient[index]

        # Update the U Value
        if new_u_value is not None:
            if not 0.0 <= new_u_value <= 1.0:
                raise ValueError(f'U Value cannot be smaller than 0.0 or bigger than 1.0 - Given value: {new_u_value}')

            target_marker.u_value = new_u_value

        # Update the Color
        if new_color:
            match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', new_color)
            if not match:
                raise ValueError(f'Marker color must be given as a Hex value beginning with a hash. Got: {new_color}')

            target_marker.color = new_color

        # Update the Gradient and UI
        self._sort_gradient()
        self.repaint()

    def edit_current_marker(self, new_u_value=None, new_color=None):
        """
        Helper function to easily edit the currently selected marker.

        :param new_u_value: If given will alter the U Value of the marker.
        :param new_color: If given will alter the colour of the marker.
        """
        self.edit_marker(self.selected_marker_index, new_u_value, new_color)

    def paintEvent(self, event):
        """
        Called Each time the widget is painted.
        :param event: Paint Event
        """
        painter = QtGui.QPainter(self)
        rect_size = self._get_gradient_rect_size()

        # Draw the linear horizontal gradient.
        gradient = QtGui.QLinearGradient(
            rect_size[0],
            0,
            rect_size[0] + rect_size[2],
            0
        )

        # Add the colors to the gradient
        for marker in self._gradient:
            gradient.setColorAt(marker.u_value, QtGui.QColor(marker.color))

        # rect to hold the gradient
        rect = QtCore.QRect(*rect_size)
        painter.fillRect(rect, gradient)

        # Draw the circular markers
        pen = QtGui.QPen()
        pen.setWidth(self.circle_marker_margin)

        for marker in self._gradient:
            # color dictates if the marker widget is selected or not
            pen.setColor(marker.outline_color)
            painter.setPen(pen)

            brush = QtGui.QBrush()
            brush.setColor(QtGui.QColor(marker.color))
            brush.setStyle(QtCore.Qt.SolidPattern)
            painter.setBrush(brush)

            # Calculate the X center point for the circle
            x = marker.get_pos_from_u_value(rect_size)
            y = rect_size[1] - self.circle_marker_size

            marker_position = QtCore.QPoint(x, y)
            marker.position = marker_position

            painter.drawEllipse(
                marker_position,
                self.circle_marker_size,
                self.circle_marker_size)

            # # Create a box that when clicked will delete the marker
            del_rect = QtCore.QRect(0, 0, self.del_rect_size, self.del_rect_size)
            rect_y = rect_size[1] + rect_size[3] + (self.del_rect_size / 2)
            rect_position = QtCore.QPoint(x, rect_y)
            marker.del_rect_position = rect_position
            del_rect.moveCenter(rect_position)
            painter.drawRect(del_rect)

            # Add the cross lines through the rect
            painter.drawLine(del_rect.topLeft(), del_rect.bottomRight())
            painter.drawLine(del_rect.topRight(), del_rect.bottomLeft())

        painter.end()

    def mousePressEvent(self, event):
        """
        When the mouse button is pressed, see if it was over a marker and if so, select it.
        :param event: Mouse Event
        """
        # Do not drag the current widget unless we are certain the user selected it
        self._drag_marker = False

        if event.button() == QtCore.Qt.LeftButton:
            # Check if the selection was in the gradient rectangle. If so, add a new marker
            if QtCore.QRect(*self._get_gradient_rect_size()).contains(event.pos()):
                self._add_marker(event.pos())
                self.repaint()

            # Check if Any of the markers have been either selected or deleted
            else:
                self._marker_selection(event.pos())

    def mouseMoveEvent(self, event):
        """
        While the mouse button is held down, if we are currently dragging a marker update it's relative U value.
        :param event: Move Event
        """
        if self._drag_marker:
            rect_data = self._get_gradient_rect_size()
            current_marker_selection = self._current_marker_selection
            current_marker_selection.set_u_value(event.pos(), rect_data)
            self.repaint()

            # Emit that the marker was moved
            self.marker_moved.emit(current_marker_selection)

    def mouseReleaseEvent(self, event):
        """
        When the mouse button is released stop dragging the marker.
        :param event: Mouse Event
        """
        self._drag_marker = False
