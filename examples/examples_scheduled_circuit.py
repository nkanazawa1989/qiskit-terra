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
Examples of scheduled circuit (QuantumCircuit with duration).
"""

from qiskit import QuantumCircuit
from qiskit import transpile
from qiskit.test.mock.backends import FakeParis
backend = FakeParis()

qc = QuantumCircuit(1, 1, name="t2_experiment")
qc.h(0)
qc.delay(100, 0, unit='ns')
qc.h(0)
qc.measure(0, 0)
# print(qc.name, qc.data)
scheduled = transpile(qc,
                      backend=backend,
                      optimization_level=0,
                      scheduling_method='alap',
                      basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
print(scheduled.draw(qubits=[0]))

qc = QuantumCircuit(2, name="bell_with_delay")
qc.h(0)
qc.delay(500, 1, unit='ns')
qc.cx(0,1)
print(qc.name, qc.data)
# transpiled = transpile(qc,
#                        backend=backend,
#                        optimization_level=0,
#                        basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
# print(transpiled.data)
scheduled = transpile(qc,
                      backend=backend,
                      scheduling_method='alap_timestep',
                      basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
# print(scheduled.name, scheduled.data)
print(scheduled.draw(qubits=[0, 1]))

qc = QuantumCircuit(2, name="bell_with_delay_no_backend")
qc.h(0)
qc.delay(500, 1)
qc.cx(0,1)
# print(qc.name, qc.data)
scheduled = transpile(qc,
                      scheduling_method='asap',
                      instruction_durations=[('u2', [0], 100), ('cx', [0, 1], 1000)],
                      basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
print(scheduled.draw(qubits=[0, 1]))

# from qiskit import assemble
# qboj = assemble(transpiled, backend=backend, shots=1000)
# print(qboj)
# qboj = assemble(scheduled, backend=backend, shots=1000)
# print(qboj)

