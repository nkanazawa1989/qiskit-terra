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
Delay instruction.
"""
from qiskit.circuit.quantumcircuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.instruction import Instruction
from qiskit.circuit.exceptions import CircuitError


class Delay(Instruction):
    """Do nothing and just delay/wait/idle for a specified duration."""

    def __init__(self, num_qubits, duration):
        """Create new delay instruction."""
        super().__init__("delay", num_qubits, 0, params=[duration], duration=duration)

    def inverse(self):
        """Special case. Return self."""
        return self

    def broadcast_arguments(self, qargs, cargs):
        yield [qarg for sublist in qargs for qarg in sublist], []

    def c_if(self, classical, val):
        raise CircuitError('Conditional Delay is not yet implemented.')

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self.params = [duration]
        self._duration = duration


def delay(self, duration, *qargs, unit=None):
    """Apply delay with duration to circuit.

    Args:
        duration (int|float): duration. Integer type indicates duration is unitless, i.e.
            use dt of backend. In the case of float, its `unit` must be specified.
        qargs (QuantumRegister|list|range|slice): quantum register
        unit (str): unit of the duration

    Returns:
        qiskit.Instruction: the attached delay instruction.

    Raises:
        CircuitError: if arguments have bad format.
    """
    qubits = []

    if not qargs:  # None
        for qreg in self.qregs:
            for j in range(qreg.size):
                qubits.append(qreg[j])

    for qarg in qargs:
        if isinstance(qarg, QuantumRegister):
            qubits.extend([qarg[j] for j in range(qarg.size)])
        elif isinstance(qarg, list):
            qubits.extend(qarg)
        elif isinstance(qarg, range):
            qubits.extend(list(qarg))
        elif isinstance(qarg, slice):
            qubits.extend(self.qubits[qarg])
        else:
            qubits.append(qarg)

    if isinstance(duration, float):
        if not unit:
            raise CircuitError('unit must be supplied for float duration.')
    else:
        if not isinstance(duration, int):
            raise CircuitError('Invalid duration type.')

    if unit:
        if unit == 'ns':
            duration *= 1e-9
        elif unit == 's':
            duration = float(duration)
        else:
            raise CircuitError('Unknown unit is specified.')

    return self.append(Delay(len(qubits), duration), qubits)


QuantumCircuit.delay = delay
