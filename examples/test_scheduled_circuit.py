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

# circuit.duration is invalidated if scheduled_circuit.data gets modified
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
