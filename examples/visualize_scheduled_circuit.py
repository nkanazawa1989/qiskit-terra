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

# qc = QuantumCircuit(1, 1, name="t2_experiment")
# qc.h(0)
# qc.delay(100, 0, unit='ns')
# qc.h(0)
# qc.measure(0, 0)
# print(qc.name, qc.data)

from qiskit.test.mock.backends import FakeParis
backend = FakeParis()

from qiskit import transpile
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.transpiler.passes.scheduling.asap import ASAPSchedule
from qiskit.transpiler.passes.scheduling.alap import ALAPSchedule

# qc = QuantumCircuit(2, name="bell")
# qc.h(0)
# qc.delay(1000, 1, unit='ns')
# qc.cx(0,1)
# # print(qc.name, qc.data)
# transpiled = transpile(qc, backend=backend, optimization_level=0, basis_gates=['u1', 'u2', 'u3', 'cx', 'delay'])
# # print(transpiled.data)
# dag = circuit_to_dag(transpiled)
# dag_with_delays = ASAPSchedule(backend).run(dag)
# scheduled = dag_to_circuit(dag_with_delays)
# # print(scheduled.name, scheduled.data)
# print(scheduled.name)
# print(scheduled)
#
# qc = QuantumCircuit(2, name="h2")
# qc.h(0)
# qc.x(1)
# # print(qc.draw())
# dag = circuit_to_dag(transpile(qc, backend=backend, optimization_level=0))
# # ASAP
# dag_with_delays = ASAPSchedule(backend).run(dag)
# scheduled = dag_to_circuit(dag_with_delays)
# print(scheduled.name)
# print(scheduled)
#
# # ALAP
# dag_with_delays = ALAPSchedule(backend).run(dag)
# scheduled = dag_to_circuit(dag_with_delays)
# print(scheduled.name)
# print(scheduled)
#
# qc = QuantumCircuit(1, 1, name="t2")
# qc.h(0)
# qc.delay(1000, 0)
# qc.h(0)
# qc.measure(0, 0)
# print(qc.schedule(backend))

# qc = QuantumCircuit(3, name="ghz")
# qc.h(0)
# qc.cx(0,1)
# qc.cx(1,2)
# print(qc.schedule(backend).data)
# print(qc.schedule(backend))

# qc = QuantumCircuit(2, name="reserve_time_order_in_pos")
# qc.h(0)
# qc.delay(300, 0)
# qc.h(0)
# qc.x(1)
# qc.delay(50, 1)
# print(qc.schedule(backend))

# qc = QuantumCircuit(2, name="zero_duration_instruction")
# qc.z(0)
# qc.h(0)
# qc.cx(0,1)
# print(qc)
# print(qc.schedule(backend))

# qc = QuantumCircuit(2, name="double_zero_duration_instructions")
# qc.h(0)
# qc.z(0)
# qc.barrier()
# qc.cx(0,1)
# print(qc)
# print(qc.schedule(backend))

qc = QuantumCircuit(2, name="double_zero_duration_instructions")
qc.z(0)
qc.h(0)
qc.z(1)
qc.barrier()
qc.z(0)
qc.cx(0,1)
print(qc)
print(qc.schedule(backend).data)
print(qc.schedule(backend))