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
Only support Ascii art mode.
"""

import logging
from collections import defaultdict, namedtuple

from qiskit.visualization import exceptions
from qiskit.visualization import utils

logger = logging.getLogger(__name__)

def scheduled_circuit_drawer(circuit,
                             filename=None,
                             output=None,
                             plot_barriers=True,
                             reverse_bits=False,
                             justify=None,
                             idle_wires=True,
                             with_layout=True,
                             fold=None,
                             initial_state=False,
                             proportional=False):
    """Minimum implementation (text mode only)"""
    if output is None:
        output = 'text'

    if output == 'text':
        return _text_circuit_drawer(circuit, filename=filename,
                                    reverse_bits=reverse_bits,
                                    plot_barriers=plot_barriers,
                                    justify=justify,
                                    idle_wires=idle_wires,
                                    with_layout=with_layout,
                                    fold=fold,
                                    initial_state=initial_state)
    else:
        raise exceptions.VisualizationError(
            'Invalid output type %s selected. The only valid choices '
            'are latex, latex_source, text, and mpl' % output)


# -----------------------------------------------------------------------------
# _text_circuit_drawer
# -----------------------------------------------------------------------------
from shutil import get_terminal_size
import sys
from itertools import groupby
from numpy import ndarray

from qiskit.circuit import Gate, Instruction, Qubit, Clbit
from qiskit.extensions import IGate, UnitaryGate, HamiltonianGate
from qiskit.extensions import Barrier as BarrierInstruction
from qiskit.extensions.quantum_initializer.initializer import Initialize
from .tools.pi_check import pi_check
from .exceptions import VisualizationError


def _text_circuit_drawer(circuit, filename=None, reverse_bits=False,
                         plot_barriers=True, justify=None,
                         idle_wires=True, with_layout=True, fold=None, initial_state=True,
                         proportional=False):
    """Draws a circuit using ascii art.

    Args:
        circuit (QuantumCircuit): Input circuit
        filename (str): optional filename to write the result
        reverse_bits (bool): Rearrange the bits in reverse order.
        plot_barriers (bool): Draws the barriers when they are there.
        justify (str) : `left`, `right` or `none`. Defaults to `left`. Says how
                        the circuit should be justified.
        idle_wires (bool): Include idle wires. Default is True.
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
    """
    qregs, cregs, layers = utils._get_layered_instructions(circuit,
                                                        reverse_bits=reverse_bits,
                                                        justify=justify,
                                                        idle_wires=idle_wires)
    if with_layout:
        layout = circuit._layout
    else:
        layout = None

    # flatten nodes
    nodes = [n for nodes in layers for n in nodes]

    if not plot_barriers:
        # exclude barriers from ops
        nodes = [n for n in nodes if not isinstance(n, BarrierInstruction)]

    text_drawing = TextDrawing(qregs, cregs, nodes,
                               layout=layout,
                               initial_state=initial_state,
                               proportional=proportional)

    text_drawing.line_length = fold

    if filename:
        text_drawing.dump(filename)
    return text_drawing


Interval = namedtuple('Interval', 'start stop')


class TextDrawing():
    """ The text drawing"""

    def __init__(self, qregs, cregs, instructions,
                 line_length=None, layout=None, initial_state=True,
                 proportional=False, fuse_neighbor=True):
        self.qubits = qregs
        self.clbits = cregs
        self.layout = layout
        self.initial_state = initial_state
        self.line_length = line_length
        intervals = TextDrawing.get_intervals(instructions)  # List[Interval]
        # print(intervals)
        time_to_pos = TextDrawing.get_time_to_pos(instructions, intervals)  # Dict[int, int]
        # print(time_to_pos)
        text_by_qubit = TextDrawing.get_text_by_qubit(instructions, intervals, time_to_pos)  # Dict[Qubit, str]
        self.no_fold = self.add_boundary(text_by_qubit, fuse_neighbor=False)  # List[str]

    def __str__(self):
        return self.single_string()

    def __repr__(self):
        return self.single_string()

    def single_string(self):
        """Creates a long string with the ascii art.

        Returns:
            str: The lines joined by a newline (``\\n``)
        """
        return "\n".join(self.lines())

    def dump(self, filename, encoding="utf8"):
        """Dumps the ascii art in the file.

        Args:
            filename (str): File to dump the ascii art.
            encoding (str): Optional. Default "utf-8".
        """
        with open(filename, mode='w', encoding=encoding) as text_file:
            text_file.write(self.single_string())

    def lines(self, line_length=None):
        """Generates a list with lines. These lines form the text drawing.

        Args:
            line_length (int): Optional. Breaks the circuit drawing to this length. This
                               useful when the drawing does not fit in the console. If
                               None (default), it will try to guess the console width using
                               shutil.get_terminal_size(). If you don't want pagination
                               at all, set line_length=-1.

        Returns:
            list: A list of lines with the text drawing.
        """
        if line_length is None:
            line_length = self.line_length
        if not line_length:
            if ('ipykernel' in sys.modules) and ('spyder' not in sys.modules):
                line_length = 80
            else:
                line_length, _ = get_terminal_size()

        lines = []
        width = len(self.no_fold)
        total_length = len(self.no_fold[0])
        n_folds = total_length // line_length
        for i in range(n_folds):
            pos_begin = i * line_length
            pos_end = (i+1) * line_length
            for j in range(width):
                lines.append(self.no_fold[j][pos_begin:pos_end])

        for j in range(width):
            lines.append(self.no_fold[j][n_folds * line_length:] + "|")

        return lines

    @staticmethod
    def get_intervals(instructions):
        intervals = []
        qubit_time_available = defaultdict(int)
        for inst in instructions:
            start = max(qubit_time_available[q] for q in inst.qargs)
            stop = start + inst.op.duration
            intervals.append(Interval(start, stop))
            for q in inst.qargs:
                qubit_time_available[q] = stop

        return intervals

    @staticmethod
    def get_time_to_pos(instructions, intervals):
        time_to_pos = {0: 0}
        ordered = sorted(zip(instructions, intervals), key=lambda x: x[1].stop)  # by stop time
        prev_time = 0
        qubit_pos_available = defaultdict(int)
        # group by stop time
        for time, group in groupby(ordered, key=lambda x: x[1].stop):
            group_end_pos = 0
            qubits = []
            for inst, _ in group:
                qubits.extend(inst.qargs)
                begin_pos = max(qubit_pos_available[q] for q in inst.qargs)
                length = TextDrawing.get_length(inst)
                end_pos = begin_pos + length
                group_end_pos = max(end_pos, group_end_pos)
                # print(inst.op.name, end_pos, group_end_pos)

            if time_to_pos[prev_time] >= group_end_pos:
                group_end_pos = time_to_pos[prev_time] + 2

            for q in qubits:
                qubit_pos_available[q] = max(qubit_pos_available[q], group_end_pos)

            time_to_pos[time] = group_end_pos
            prev_time = time

        return time_to_pos

    @staticmethod
    def get_length(inst):
        return len(TextDrawing.label_for_box(inst)) + 1  # +1 for separator "|"

    @staticmethod
    def get_text_by_qubit(instructions, intervals, time_to_pos):
        lines_by_qubit = defaultdict(list)
        for inst, i in zip(instructions, intervals):
            inst_str = TextDrawing.label_for_box(inst)
            inst_str = inst_str.center(time_to_pos[i.stop] - time_to_pos[i.start] - 1, ' ')
            inst_str = '|' + inst_str
            for q in inst.qargs:
                lines_by_qubit[q].append(inst_str)

        text_by_qubit = {k: "".join(v) for k, v in lines_by_qubit.items()}
        return text_by_qubit

    def add_boundary(self, text_by_qubit, fuse_neighbor=True):
        if fuse_neighbor:
            raise VisualizationError("Not yet implemented.")

        def all_same(es):
            return all([e == es[0] for e in es[1:]]) if es else False

        # check validity
        lengths = [len(val) for val in text_by_qubit.values()]
        if not all_same(lengths):
            print(lengths)
            import pprint
            pprint.pprint(text_by_qubit)
            raise VisualizationError("Invalid text_by_qubit")

        total_length = lengths[0]
        disp_qubits = [q for q in self.qubits if q in text_by_qubit]
        wire_names = {q: self.wire_name(q) for q in disp_qubits}
        max_name_length = max(len(name) for name in wire_names.values())
        wire_names = {q: name.rjust(max_name_length, ' ') for q, name in wire_names.items()}
        total_length += max_name_length
        boundary_text = "{}|".format(' ' * max_name_length).ljust(total_length, '-')
        res = []
        for q in disp_qubits:
            res.append(boundary_text)
            res.append(wire_names[q] + text_by_qubit[q])
        res.append(boundary_text)
        return res

    def wire_name(self, bit, with_initial_state=False):
        """Returns a list of names for each wire.

        Args:
            with_initial_state (bool): Optional (Default: False). If true, adds
                the initial value to the name.

        Returns:
            List: The list of wire names.
        """
        if with_initial_state:
            initial_qubit_value = '|0>'
            initial_clbit_value = '0 '
        else:
            initial_qubit_value = ''
            initial_clbit_value = ''

        if isinstance(bit, Qubit):
            if self.layout is None:
                label = '{name}_{index}: ' + initial_qubit_value
                return label.format(name=bit.register.name,
                                    index=bit.index,
                                    physical='')
            else:
                label = '{name}_{index} -> {physical} ' + initial_qubit_value
                return label.format(name=self.layout[bit.index].register.name,
                                    index=self.layout[bit.index].index,
                                    physical=bit.index)
        elif isinstance(bit, Clbit):
            label = '{name}_{index}: ' + initial_clbit_value
            return label.format(name=bit.register.name, index=bit.index)
        else:
            raise VisualizationError("Invalid bit type")

    @staticmethod
    def label_for_conditional(instruction):
        """ Creates the label for a conditional instruction."""
        return "= %s" % instruction.condition[1]

    @staticmethod
    def params_for_label(instruction):
        """Get the params and format them to add them to a label. None if there
         are no params or if the params are numpy.ndarrays."""
        op = instruction.op
        if not hasattr(op, 'params'):
            return None
        if any([isinstance(param, ndarray) for param in op.params]):
            return None

        ret = []
        for param in op.params:
            try:
                str_param = pi_check(param, ndigits=5)
                ret.append('%s' % str_param)
            except TypeError:
                ret.append('%s' % param)
        return ret

    @staticmethod
    def special_label(instruction):
        """Some instructions have special labels"""
        labels = {IGate: 'I',
                  Initialize: 'initialize',
                  UnitaryGate: 'unitary',
                  HamiltonianGate: 'Hamiltonian'}
        instruction_type = type(instruction)
        if instruction_type in {Gate, Instruction}:
            return instruction.name
        return labels.get(instruction_type, None)

    @staticmethod
    def label_for_box(instruction, controlled=False):
        """ Creates the label for a box."""
        if controlled:
            raise VisualizationError("Not yet implemented.")

        if getattr(instruction.op, 'label', None) is not None:
            return instruction.op.label

        if controlled:
            label = TextDrawing.special_label(instruction.op.base_gate) or \
                    instruction.op.base_gate.name.upper()
        else:
            label = TextDrawing.special_label(instruction.op) or instruction.name.upper()
        params = TextDrawing.params_for_label(instruction)

        if params:
            label += "(%s)" % ','.join(params)

        label = " {}[{}] ".format(label, instruction.op.duration)
        return label
