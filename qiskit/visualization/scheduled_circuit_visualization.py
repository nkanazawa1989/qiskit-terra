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
import sys
from collections import defaultdict, namedtuple
from itertools import groupby
from shutil import get_terminal_size
from typing import Optional, List, Dict, Iterable

from numpy import ndarray
from qiskit.circuit import Barrier as BarrierInstruction
from qiskit.circuit import Delay
from qiskit.circuit import Gate, Instruction, Qubit, Clbit
from qiskit.circuit.tools.pi_check import pi_check
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGNode
from qiskit.extensions import IGate, UnitaryGate, HamiltonianGate
from qiskit.extensions.quantum_initializer.initializer import Initialize
from qiskit.visualization import exceptions

from .exceptions import VisualizationError

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
    """Minimum implementation (text mode only)"""
    if output is None:
        output = 'text'

    if output == 'text':
        if isinstance(qubits, int):
            qubits = [qubits]
        return _text_circuit_drawer(circuit, filename=filename,
                                    reverse_bits=reverse_bits,
                                    plot_barriers=plot_barriers,
                                    qubits=qubits,
                                    with_layout=with_layout,
                                    fold=fold,
                                    initial_state=initial_state)
    else:
        raise exceptions.VisualizationError(
            'Invalid output type %s selected. The only valid choices '
            'are latex, latex_source, text, and mpl' % output)


def _text_circuit_drawer(circuit, filename=None, qubits=None,
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
        nodes = [n for n in nodes if not isinstance(n, BarrierInstruction)]

    text_drawing = TextDrawing(nodes,
                               qubits=qubits,
                               layout=layout,
                               initial_state=initial_state)

    text_drawing.line_length = fold

    if filename:
        text_drawing.dump(filename)
    return text_drawing


TimedInstruction = namedtuple('TimedInstruction', 'op qargs start stop node')


class TextBlock:
    """ The text block for timelined drawer."""
    splitter = '|'

    def __init__(self,
                 label: str,
                 length: int,
                 qubit: Qubit,
                 node: Optional[DAGNode] = None,
                 fillchar: Optional[str] = None):
        # if length < len(label) + len(TextBlock.splitter):
        #     raise VisualizationError("length must be larger than len(label)")
        if fillchar and len(fillchar) != 1:
            raise VisualizationError("length of fillchar must be one")

        self.label = label
        self.length = length
        self.qubit = qubit
        self.node = node
        self.fillchar = fillchar or ' '

    @property
    def _width(self):
        return self.length - len(TextBlock.splitter)

    @classmethod
    def empty(cls, length: int, qubit: Qubit):
        """Empty text block"""
        return TextBlock(label="",
                         length=length,
                         qubit=qubit,
                         fillchar='*')

    def __str__(self):
        return f"{TextBlock.splitter}{self.label.center(self._width, self.fillchar)}"

    def __repr__(self):
        # TODO: elaorate
        return str(self) + f"({self.length})"


class TextDrawing:
    """ The text drawing"""

    def __init__(self, instructions, qubits,
                 line_length=None, layout=None, initial_state=True):
        self.qubits = qubits
        self.layout = layout
        self.initial_state = initial_state
        self.line_length = line_length
        instructions = TextDrawing.get_timed_instructions(instructions)
        # print(instructions)  # List[TimedInstruction]
        zeros, positives = TextDrawing.split_instructions(instructions)
        time_to_pos = TextDrawing.get_time_to_pos(positives)
        # print(time_to_pos)  # Dict[int, int]
        blocks_by_qubit = TextDrawing.get_blocks_by_qubit(instructions, time_to_pos)
        # print(blocks_by_qubit)  # Dict[Qubit, List[TextBlock]]
        blocks_by_qubit = TextDrawing.resolve_zero_length(blocks_by_qubit, zeros)
        # print(blocks_by_qubit)  # Dict[Qubit, List[TextBlock]]
        text_by_qubit = TextDrawing.to_text(blocks_by_qubit)
        # print(text_by_qubit)
        self.no_fold = self.add_boundary(text_by_qubit)  # List[str]

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
    def get_timed_instructions(instructions: List[DAGNode]):
        """Build the timed instructions from the instructions and return."""
        res = []
        qubit_time_available = defaultdict(int)
        for inst in instructions:
            start = max(qubit_time_available[q] for q in inst.qargs)
            stop = start + inst.op.duration
            res.append(TimedInstruction(op=inst.op,
                                        qargs=inst.qargs,
                                        start=start,
                                        stop=stop,
                                        node=inst))
            for q in inst.qargs:
                qubit_time_available[q] = stop

        return res

    @staticmethod
    def split_instructions(instructions: Iterable[TimedInstruction]):
        """Split the instructions into ones with zero duration and ones with positive duration."""
        zeros = [i for i in instructions if i.op.duration == 0]
        positives = [i for i in instructions if i.op.duration > 0]
        assert len(zeros) + len(positives) == len(instructions)
        return zeros, positives

    @staticmethod
    def get_time_to_pos(instructions: List[TimedInstruction]) -> Dict[int, int]:
        """Construct a dictionary that maps start times to positions in the timeline text"""
        time_to_pos = {0: 0}
        ordered = sorted(instructions, key=lambda x: x.stop)  # by stop time
        prev_time = 0
        qubit_pos_available = defaultdict(int)
        # group by stop time
        for time, group in groupby(ordered, key=lambda x: x.stop):
            group_end_pos = 0
            qubits = []
            for i in group:
                qubits.extend(i.qargs)
                begin_pos = max(qubit_pos_available[q] for q in i.qargs)
                end_pos = begin_pos + TextDrawing.get_min_length(i.node)
                group_end_pos = max(end_pos, group_end_pos)
                # print(inst.op.name, end_pos, group_end_pos)

            if time_to_pos[prev_time] >= group_end_pos:
                group_end_pos = time_to_pos[prev_time] + 2

            for q in qubits:
                qubit_pos_available[q] = group_end_pos
                # qubit_pos_available[q] = max(qubit_pos_available[q], group_end_pos)

            time_to_pos[time] = group_end_pos
            prev_time = time

        return time_to_pos

    @staticmethod
    def get_min_length(instruction: DAGNode):
        """Return the minimum text length of the instruction."""
        return len(TextDrawing.label_for_box(instruction)) + 1  # +1 for separator "|"

    @staticmethod
    def get_blocks_by_qubit(instructions: List[TimedInstruction],
                            time_to_pos: Dict[int, int]) -> Dict[Qubit, List[TextBlock]]:
        """Return a map from qubits to text blocks."""
        blocks_by_qubit = defaultdict(list)
        for i in instructions:
            for q in i.qargs:
                block = TextBlock(label=TextDrawing.label_for_box(i.node),
                                  length=time_to_pos[i.stop] - time_to_pos[i.start],
                                  qubit=q,
                                  node=i.node)
                blocks_by_qubit[q].append(block)

        return blocks_by_qubit

    @staticmethod
    def resolve_zero_length(blocks_by_qubit: Dict[Qubit, List[TextBlock]],
                            zero_instructions: List[TimedInstruction]
                            ) -> Dict[Qubit, List[TextBlock]]:
        """Insert zero duration instructions into a given text blocks."""
        news = defaultdict(list)
        blocks_by_begin = defaultdict(list)
        blocks_by_end = defaultdict(list)
        blocks_by_end[0] = []
        for q in blocks_by_qubit:
            pos = 0
            for b in blocks_by_qubit[q]:
                blocks_by_begin[pos].append(b)
                pos += b.length
                blocks_by_end[pos].append(b)

        actives = set()
        positions = sorted(blocks_by_end)
        for pos in positions:
            actives.update(blocks_by_begin[pos])
            blocks = blocks_by_end[pos]
            if not blocks:
                continue

            # 1. positives -> schedule first
            # 2. zeros -> schedule layer by layer
            # 3. positives -> pad with empty total_zero_length if its qubit ends with positive one
            # 4. actives -> stretch length by total_zero_length
            positives = [b for b in blocks if b.length > 0]
            zeros = [b for b in blocks if b.length == 0]
            actives -= set(blocks)

            # 1. positives -> schedule first
            for b in positives:
                news[b.qubit].append(b)

            if not zeros:
                continue

            # 2. zeros -> schedule layer by layer
            zero_qubits = {b.qubit for b in zeros}
            for b in zeros:
                b.length = TextDrawing.get_min_length(b.node)

            # decompose zeros into layers
            node_to_blocks = defaultdict(list)  # for barrier
            for b in zeros:
                node_to_blocks[b.node].append(b)
            layers = []  # layers on blocks
            wire = defaultdict(int)
            all_zero_nodes = [n.node for n in zero_instructions]
            zero_nodes = list(node_to_blocks)
            zero_nodes.sort(key=all_zero_nodes.index)
            for n in zero_nodes:  # must be sorted in the original order when scheduling
                qubits = n.qargs
                i = 1 + max(wire[q] for q in qubits)
                for q in qubits:
                    wire[q] = i
                if len(layers) > i:
                    layers[i].extend(node_to_blocks[n])
                else:
                    layers.append(node_to_blocks[n])

            total_zero_length = 0
            for layer in layers:
                layer_length = max(b.length for b in layer)
                for b in layer:
                    news[b.qubit].append(b)
                    if b.length < layer_length:
                        news[b.qubit].append(TextBlock.empty(length=layer_length - b.length,
                                                             qubit=b.qubit))

                residuals = zero_qubits - {b.qubit for b in layer}
                for q in residuals:
                    news[q].append(TextBlock.empty(length=layer_length, qubit=q))

                total_zero_length += layer_length

            # 3. positives -> pad with empty total_zero_length if its qubit ends with positive one
            for b in positives:
                if b.qubit not in zero_qubits:
                    empty = TextBlock.empty(length=total_zero_length, qubit=b.qubit)
                    news[b.qubit].append(empty)

            # 4. actives (not on zero_qubits) -> stretch length by total_zero_length
            for b in actives:
                if b.qubit not in zero_qubits:
                    b.length += total_zero_length

        return news

    @staticmethod
    def to_text(blocks_by_qubit: Dict[Qubit, List[TextBlock]]) -> Dict[Qubit, str]:
        """Convert text blocks into a text."""
        return {q: "".join([str(b) for b in blocks]) for q, blocks in blocks_by_qubit.items()}

    def add_boundary(self, text_by_qubit: Dict[Qubit, str]):
        """Add boundary texts."""
        def all_same(elems):
            return all([e == elems[0] for e in elems[1:]]) if elems else False

        # check validity
        lengths = [len(val) for val in text_by_qubit.values()]
        if not all_same(lengths):
            # TODO: use logger instead of print
            print("FIXME:", lengths)
            # import pprint
            # pprint.pprint(text_by_qubit)
            # raise VisualizationError("Invalid text_by_qubit")

        total_length = max(lengths)
        disp_qubits = [q for q in self.qubits if q in text_by_qubit]
        wire_names = {q: self.wire_name(q) for q in disp_qubits}
        max_name_length = max(len(name) for name in wire_names.values())
        wire_names = {q: name.rjust(max_name_length, ' ') for q, name in wire_names.items()}
        total_length += max_name_length
        boundary_text = "{}|".format(' ' * max_name_length).ljust(total_length, '-')
        res = [boundary_text]
        for q in disp_qubits:
            res.append(wire_names[q] + text_by_qubit[q])
        res.append(boundary_text)
        return res

    def wire_name(self, bit, with_initial_state=False):
        """Returns the name of the wire corresponding to the bit.

        Args:
            bit (Bit): A bit whose wire name should be returned.
            with_initial_state (bool): Optional (Default: False). If true, adds
                the initial value to the name.

        Returns:
            str: The wire name of the bit.

        Raises:
            VisualizationError: if invalid bit type is supplied.
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

        if params and not isinstance(instruction.op, Delay):
            label += "(%s)" % ','.join(params)

        if len(instruction.qargs) == 2:
            qubits = ",".join([str(q.index) for q in instruction.qargs])
            label += "({})".format(qubits)

        # duration = str(instruction.op.duration)
        # duration += "[{}]".format(instruction.op.unit if instruction.op.unit else "dt")

        label = " {}[{}] ".format(label, instruction.op.duration)
        return label
