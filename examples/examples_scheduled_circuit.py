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
import pprint
import numpy as np

from qiskit import QuantumCircuit

qc = QuantumCircuit(1, 1, name="t2_experiment")
qc.h(0)
qc.delay(100, 0, unit='ns')
qc.h(0)
qc.measure(0, 0)
print(qc.data)

# from qiskit import IBMQ
# IBMQ.load_account()
# provider = IBMQ.get_provider(hub='ibm-q-internal', group='deployed', project='default')
# backend = provider.get_backend("ibmq_paris")
from qiskit.test.mock.backends import FakeParis
backend = FakeParis()

from qiskit import transpile
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.transpiler.passes.scheduling.asap import ASAPSchedule

bell2 = QuantumCircuit(2, name="bell2")
bell2.h(0)
bell2.delay(1000, 1, unit='ns')
bell2.cx(0,1)
print(bell2.data)
transpiled = transpile(bell2, backend=backend, optimization_level=0, basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
print(transpiled.data)
dag = circuit_to_dag(transpiled)
dag_with_delays = ASAPSchedule(backend).run(dag)
scheduled_bell = dag_to_circuit(dag_with_delays)
print(scheduled_bell.data)


# Q1: Output delay when qasm()? Will delay be included in QASM3?
# Q2:

# 1- Adding a Delay instruction for circuits
# 2- Two scheduling passes for implementing ALAP and ASAP by inserting Delays on the DAGCircuit.
# from qiskit.transpiler.passes.scheduling import ASAPSchedule, ALAPSchedule
# dag_with_delays = ALAPSchedule(backend_properties).run(dag)
# 3- A simple scheduled_circuit.draw() to visualize timed blocks on the qubits


# from qiskit import assemble
# qboj = assemble(sc, backend=backend, shots=1000)
# print(qboj)

