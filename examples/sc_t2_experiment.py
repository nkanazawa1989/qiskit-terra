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
T2 noise simulation with Aer example.
"""
import pprint
import numpy as np

from qiskit import IBMQ
from qiskit import assemble
from qiskit import QuantumCircuit
from qiskit.circuit.delay import Delay

# IBMQ.load_account()
# provider = IBMQ.providers()[-1]
# backend = provider.get_backend("ibmq_cambridge")

qc = QuantumCircuit(1, 1, name="t2_experiment")
qc.h(0)
qc.delay(100, 0, unit='ns')
qc.h(0)
qc.measure(0, 0)
print(qc.data)


# 1- Adding a Delay instruction for circuits
# 2- Two scheduling passes for implementing ALAP and ASAP by inserting Delays on the DAGCircuit.
# from qiskit.transpiler.passes.scheduling import ASAPSchedule, ALAPSchedule
# dag_with_delays = ALAPSchedule(backend_properties).run(dag)
# 3- A simple scheduled_circuit.draw() to visualize timed blocks on the qubits


# qboj = assemble(sc, backend=backend, shots=1000)
# print(qboj)

