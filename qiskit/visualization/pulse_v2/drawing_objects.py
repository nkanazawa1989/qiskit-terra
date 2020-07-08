# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
r"""
Drawing object IRs for pulse drawer.

Drawing IRs play two important roles:
    - Allowing unittests of visualization module. Usually it is hard for image files to be tested.
    - Removing program parser from each plotter interface. We can easily add new plotter.

IRs supported by this module are designed based on `matplotlob` since it is the primary plotter
of the pulse drawer. However IRs should be agnostic to the actual plotter.

Design concept
~~~~~~~~~~~~~~
When we think about the dynamic update of drawing objects, it will be efficient to
update only properties of drawings rather than regenerating all of them from scratch.
Thus the core drawing function generates all possible drawings in the beginning and
then updates the visibility and the offset coordinate of each item according to
the end-user request. Drawing properties are designed based on this line of thinking.

Data key
~~~~~~~~
In the abstract class ``ElementaryData`` common properties to represent a drawing object are
specified. In addition, IRs have the `data_key` property that returns an unique hash of
the object for comparison. This property should be defined in each sub-class by
considering necessary properties to identify that object, i.e. `visible` should not
be a part of the key, because any change on this property just sets the visibility of
the same drawing object.

Favorable IR
~~~~~~~~~~~~
To support not only `matplotlib` but also multiple plotters, those drawing IRs should be
universal and designed without strong dependency on modules in `matplotlib`.
This means IRs that represent primitive geometries are preferred.
It should be noted that there will be no unittest for a plotter interface, which takes
drawing IRs and output an image data, we should avoid adding a complicated data structure
that has a context of the pulse program.

For example, a pulse envelope is complex valued number array and may be represented
by two lines with different colors associated with the real and the imaginary component.
In this case, we can use two line-type IRs rather than defining a new IR that takes complex value.
Because many plotters don't support an API that visualizes complex valued data array.
If we introduce such IR and write a custom wrapper function on top of the existing plotter API,
it could be difficult to prevent bugs with the CI tools due to lack of the effective unittest.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Union

import numpy as np

from qiskit import pulse


class ElementaryData(ABC):
    """Abstract class of visualization intermediate representation."""
    def __init__(self,
                 data_type: str,
                 channel: pulse.channels.Channel,
                 meta: Union[Dict[str, Any], None],
                 offset: float,
                 visible: bool,
                 styles: Dict[str, Any]):
        """Create new visualization IR.
        Args:
            data_type: String representation of this drawing object.
            channel: Pulse channel object bound to this drawing.
            meta: Meta data dictionary of the object.
            offset: Offset coordinate of vertical axis.
            visible: Set ``True`` to show the component on the canvas.
            styles: Style keyword args of the object. This conforms to `matplotlib`.
        """
        self.data_type = data_type
        self.channel = channel
        self.meta = meta
        self.offset = offset
        self.visible = visible
        self.styles = styles

    @property
    @abstractmethod
    def data_key(self):
        """Return unique hash of this object."""
        pass

    def __repr__(self):
        return "{}(type={}, key={})".format(self.__class__.__name__,
                                            self.data_type,
                                            self.data_key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.data_key == other.data_key


class FilledAreaData(ElementaryData):
    """Drawing IR to represent object appears as a filled area.
    This is the counterpart of `matplotlib.axes.Axes.fill_between`.
    """
    # pylint: disable=invalid-name
    def __init__(self,
                 data_type: str,
                 channel: pulse.channels.Channel,
                 x: np.ndarray,
                 y1: np.ndarray,
                 y2: np.ndarray,
                 meta: Union[Dict[str, Any], None],
                 offset: float,
                 visible: bool,
                 styles: Dict[str, Any]):
        """Create new visualization IR.
        Args:
            data_type: String representation of this drawing object.
            channel: Pulse channel object bound to this drawing.
            x: Series of horizontal coordinate that the object is drawn.
            y1: Series of vertical coordinate of upper boundary of filling area.
            y2: Series of vertical coordinate of lower boundary of filling area.
            meta: Meta data dictionary of the object.
            offset: Offset coordinate of vertical axis.
            visible: Set ``True`` to show the component on the canvas.
            styles: Style keyword args of the object. This conforms to `matplotlib`.
        """
        self.x = x
        self.y1 = y1
        self.y2 = y2

        super().__init__(
            data_type=data_type,
            channel=channel,
            meta=meta,
            offset=offset,
            visible=visible,
            styles=styles
        )

    @property
    def data_key(self):
        """Return unique hash of this object."""
        return str(hash((self.__class__.__name__,
                         self.data_type,
                         self.channel,
                         tuple(self.x),
                         tuple(self.y1),
                         tuple(self.y2))))


class LineData(ElementaryData):
    """Drawing IR to represent object appears as a line.
    This is the counterpart of `matplotlib.pyploy.plot`.
    """
    # pylint: disable=invalid-name
    def __init__(self,
                 data_type: str,
                 channel: pulse.channels.Channel,
                 x: np.ndarray,
                 y: np.ndarray,
                 meta: Union[Dict[str, Any], None],
                 offset: float,
                 visible: bool,
                 styles: Dict[str, Any]):
        """Create new visualization IR.
        Args:
            data_type: String representation of this drawing object.
            channel: Pulse channel object bound to this drawing.
            x: Series of horizontal coordinate that the object is drawn.
            y: Series of vertical coordinate that the object is drawn.
            meta: Meta data dictionary of the object.
            offset: Offset coordinate of vertical axis.
            visible: Set ``True`` to show the component on the canvas.
            styles: Style keyword args of the object. This conforms to `matplotlib`.
        """
        self.x = x
        self.y = y

        super().__init__(
            data_type=data_type,
            channel=channel,
            meta=meta,
            offset=offset,
            visible=visible,
            styles=styles
        )

    @property
    def data_key(self):
        """Return unique hash of this object."""
        return str(hash((self.__class__.__name__,
                         self.data_type,
                         self.channel,
                         tuple(self.x),
                         tuple(self.y))))


class TextData(ElementaryData):
    """Drawing IR to represent object appears as a text.
    This is the counterpart of `matplotlib.pyploy.text`.
    """
    # pylint: disable=invalid-name
    def __init__(self,
                 data_type: str,
                 channel: pulse.channels.Channel,
                 x: float,
                 y: float,
                 text: str,
                 meta: Union[Dict[str, Any], None],
                 offset: float,
                 visible: bool,
                 styles: Dict[str, Any]):
        """Create new visualization IR.
        Args:
            data_type: String representation of this drawing object.
            channel: Pulse channel object bound to this drawing.
            x: A horizontal coordinate that the object is drawn.
            y: A vertical coordinate that the object is drawn.
            text: String to show in the canvas.
            meta: Meta data dictionary of the object.
            offset: Offset coordinate of vertical axis.
            visible: Set ``True`` to show the component on the canvas.
            styles: Style keyword args of the object. This conforms to `matplotlib`.
        """
        self.x = x
        self.y = y
        self.text = text

        super().__init__(
            data_type=data_type,
            channel=channel,
            meta=meta,
            offset=offset,
            visible=visible,
            styles=styles
        )

    @property
    def data_key(self):
        """Return unique hash of this object."""
        return str(hash((self.__class__.__name__,
                         self.data_type,
                         self.channel,
                         self.x,
                         self.y,
                         self.text)))
