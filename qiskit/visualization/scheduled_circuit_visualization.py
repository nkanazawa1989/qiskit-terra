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


"""
Module for the primary interface to the scheduled circuit drawers.
Support timeline mode only.
"""

import logging

from qiskit.circuit import Barrier
from qiskit.converters import circuit_to_dag
from qiskit.visualization import exceptions

from .timeline import TextDrawing

logger = logging.getLogger(__name__)


def scheduled_circuit_drawer(circuit,
                             filename=None,
                             output=None,
                             qubits=None,
                             plot_barriers=True,
                             reverse_bits=False,
                             with_layout=True,
                             fold=None,
                             initial_state=False):
    """Minimum implementation (timeline mode only)"""
    if output == 'timeline':
        if isinstance(qubits, int):
            qubits = [qubits]
        return _timeline_circuit_drawer(circuit, filename=filename,
                                        reverse_bits=reverse_bits,
                                        plot_barriers=plot_barriers,
                                        qubits=qubits,
                                        with_layout=with_layout,
                                        fold=fold,
                                        initial_state=initial_state)
    else:
        raise exceptions.VisualizationError(
            'Invalid output type %s selected. The only the valid choice '
            'is timeline' % output)


def _timeline_circuit_drawer(circuit, filename=None, qubits=None,
                             reverse_bits=False, plot_barriers=True,
                             with_layout=True, fold=None, initial_state=True):
    """Draws a circuit using ascii art.

    Args:
        circuit (QuantumCircuit): Input circuit
        filename (str): optional filename to write the result
        qubits (list): Qubit indices to display. If not specified, all are displayed.
        reverse_bits (bool): Rearrange the bits in reverse order.
        plot_barriers (bool): Draws the barriers when they are there.
        with_layout (bool): Include layout information, with labels on the physical
            layout. Default: True
        fold (int): Optional. Breaks the circuit drawing to this length. This
                    useful when the drawing does not fit in the console. If
                    None (default), it will try to guess the console width using
                    `shutil.get_terminal_size()`. If you don't want pagination
                   at all, set `fold=-1`.
        initial_state (bool): Optional. Adds |0> in the beginning of the line. Default: `True`.

    Returns:
        TextDrawing: An instances that, when printed, draws the circuit in ascii art.

    Raises:
        VisualizationError: If qubits has invalid type.
    """
    dag = circuit_to_dag(circuit)
    nodes = list(dag.topological_op_nodes())

    if qubits is None:
        qubits = dag.qubits()
    elif isinstance(qubits, list):
        qubits = [q for q in dag.qubits() if q.index in qubits]
    else:
        raise exceptions.VisualizationError("Invalid qubits type: {}".format(type(qubits)))

    if reverse_bits:
        qubits.reverse()

    if with_layout:
        layout = circuit._layout
    else:
        layout = None

    if not plot_barriers:
        # exclude barriers from ops
        nodes = [n for n in nodes if not isinstance(n, Barrier)]

    text_drawing = TextDrawing(nodes,
                               qubits=qubits,
                               layout=layout,
                               initial_state=initial_state)

    text_drawing.line_length = fold

    if filename:
        text_drawing.dump(filename)
    return text_drawing
