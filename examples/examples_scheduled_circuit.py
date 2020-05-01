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
print(qc.name, qc.data)

# from qiskit import IBMQ
# IBMQ.load_account()
# provider = IBMQ.get_provider(hub='ibm-q-internal', group='deployed', project='default')
# backend = provider.get_backend("ibmq_paris")
from qiskit.test.mock.backends import FakeParis
backend = FakeParis()

from qiskit import transpile
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.transpiler.passes.scheduling.asap import ASAPSchedule
from qiskit.transpiler.passes.scheduling.alap import ALAPSchedule

qc = QuantumCircuit(2, name="bell")
qc.h(0)
qc.delay(999, 1, unit='ns')
qc.cx(0,1)
print(qc.name, qc.data)
transpiled = transpile(qc, backend=backend, optimization_level=0, basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
# print(transpiled.data)
dag = circuit_to_dag(transpiled)
dag_with_delays = ASAPSchedule(backend).run(dag)
scheduled = dag_to_circuit(dag_with_delays)
print(scheduled.name, scheduled.data)
print(scheduled)
#
# qc = QuantumCircuit(2, name="h2")
# qc.h(0)
# qc.x(1)
# print(qc.name, qc.data)
# dag = circuit_to_dag(transpile(qc, backend=backend, optimization_level=0, basis_gates=['u1', 'u2', 'u3', 'cx', 'delay']))
# #ASAP
# dag_with_delays = ASAPSchedule(backend).run(dag)
# scheduled = dag_to_circuit(dag_with_delays)
# print(scheduled.name, scheduled.data)
# #ALAP
# dag_with_delays = ALAPSchedule(backend).run(dag)
# scheduled = dag_to_circuit(dag_with_delays)
# print(scheduled.name, scheduled.data)


from qiskit.transpiler.passes.scheduling.timestepsasap import TimestepsASAPSchedule
qc = QuantumCircuit(2, name="bell_with_delay")
qc.h(0)
qc.delay(100, 1, unit='ns')
qc.cx(0,1)
# print(qc.name, qc.data)
transpiled = transpile(qc, backend=backend, optimization_level=0, basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
# print(transpiled.data)
dag = circuit_to_dag(transpiled)
dag_with_delays = TimestepsASAPSchedule(backend).run(dag)
scheduled = dag_to_circuit(dag_with_delays)
print(scheduled.draw(qubits=[0, 1]))

# from qiskit import assemble
# qboj = assemble(transpiled, backend=backend, shots=1000)
# print(qboj)
# qboj = assemble(scheduled, backend=backend, shots=1000)
# print(qboj)

