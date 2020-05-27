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
Test cases of scheduled circuit (QuantumCircuit with duration).
"""

from qiskit import QuantumCircuit
from qiskit import transpile
from qiskit.compiler.sequence import sequence

from qiskit.test.mock.backends import FakeParis
backend = FakeParis()

# from qiskit import IBMQ
# IBMQ.load_account()
# provider = IBMQ.get_provider(hub='ibm-q-internal', group='deployed', project='default')
# backend = provider.get_backend('ibmq_paris')

# enhance instruction_durations for the [('cx', None, 300), ('cx', [1, 2], 350)] case
qc = QuantumCircuit(2)
qc.h(0)
qc.delay(500, 1)
qc.cx(0,1)
scheduled = transpile(qc,
                      backend=backend,
                      scheduling_method='alap',
                      instruction_durations=[('cx', [0, 1], 1000)]
                      )
assert scheduled.duration == 1500
scheduled = transpile(qc,
                      basis_gates=['h', 'cx', 'delay'],
                      scheduling_method='alap',
                      instruction_durations=[('h', 0, 200), ('cx', None, 900)]
                      )
assert scheduled.duration == 1400
scheduled = transpile(qc,
                      basis_gates=['h', 'cx', 'delay'],
                      scheduling_method='alap',
                      instruction_durations=[('h', 0, 200), ('cx', None, 900), ('cx', [0, 1], 800)]
                      )
assert scheduled.duration == 1300

# invalidate circuit.duration if a new instruction is appended
qc = QuantumCircuit(2)
qc.h(0)
qc.delay(500, 1)
qc.cx(0,1)
scheduled = transpile(qc,
                      backend=backend,
                      scheduling_method='alap')
assert scheduled.duration == 1908
scheduled.h(0)
assert scheduled.duration is None

