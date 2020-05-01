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
Timestep instruction.
"""
from qiskit.circuit.quantumcircuit import QuantumCircuit, QuantumRegister
from qiskit.circuit.instruction import Instruction
from qiskit.circuit.exceptions import CircuitError


class Timestep(Instruction):
    """Do nothing and just delay/wait/idle for a specified duration."""

    def __init__(self, num_qubits, length):
        """Create new timestep instruction."""
        super().__init__("timestep", num_qubits, 0, params=[length], duration=0)

    def inverse(self):
        """Special case. Return self."""
        return self

    def broadcast_arguments(self, qargs, cargs):
        yield [qarg for sublist in qargs for qarg in sublist], []

    def c_if(self, classical, val):
        raise CircuitError('Conditional Timestep is not supported.')


def timestep(self, length, *qargs):
    """Apply timestep to circuit.

    Args:
        length (int): length of the timestep
        qargs (QuantumRegister|list|range|slice): quantum register

    Returns:
        qiskit.Instruction: the attached timestep instruction.

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

    return self.append(Timestep(len(qubits), length), qubits)


QuantumCircuit.timestep = timestep
