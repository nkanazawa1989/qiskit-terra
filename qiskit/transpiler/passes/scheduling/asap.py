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

"""ASAP Scheduling."""
import warnings
from collections import defaultdict
from typing import List

from qiskit.circuit.delay import Delay
from qiskit.circuit.measure import Measure
from qiskit.extensions.standard import Barrier
from qiskit.dagcircuit import DAGCircuit, DAGNode
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError


class DurationMapper:
    def __init__(self, backend):
        # TODO: backend.properties() should let us know all about instruction durations
        if not backend.configuration().open_pulse:
            raise TranspilerError("DurationMapper needs backend.configuration().dt")
        self.dt = backend.configuration().dt
        self.backend_prop = backend.properties()
        self.all_qubits = tuple([i for i in range(backend.configuration().num_qubits)])
        self.inst_map = backend.defaults().instruction_schedule_map

    def get(self, node: DAGNode):
        duration = node.op.duration
        if duration is None:
            if isinstance(node.op, Barrier):
                duration = 0
            else:  # consult backend properties
                qubits = [q.index for q in node.qargs]
                if isinstance(node.op, Measure):
                    duration = self.inst_map.get(node.op.name, self.all_qubits).duration
                else:
                    duration = self.backend_prop.gate_length(node.op.name, qubits)

        # convert seconds (float) to dts (int)
        if isinstance(duration, float):
            org = duration
            duration = round(duration / self.dt)
            if isinstance(node.op, Delay):  # overwrite params! (tricky but necessary)
                node.op.params = [duration]
            rounding_error = abs(org - duration * self.dt)
            if rounding_error > 1e-15:
                warnings.warn("Duration of %s is rounded to %d dt = %e s from %e"
                              % (node.op.name, duration, duration * self.dt, org),
                              UserWarning)

        return duration


class ASAPSchedule(TransformationPass):
    """ASAP Scheduling."""

    def __init__(self, backend):
        """ASAPSchedule initializer.

        Args:
            backend (Backend): .
        """
        super().__init__()
        self.durations = DurationMapper(backend)

    def run(self, dag):
        """Run the ASAPSchedule pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to schedule.

        Returns:
            DAGCircuit: A scheduled DAG.

        Raises:
            TranspilerError: if ...
        """
        if len(dag.qregs) != 1 or dag.qregs.get('q', None) is None:
            raise TranspilerError('ASAP schedule runs on physical circuits only')

        new_dag = DAGCircuit()
        for qreg in dag.qregs.values():
            new_dag.add_qreg(qreg)
        for creg in dag.cregs.values():
            new_dag.add_creg(creg)

        qubit_time_available = defaultdict(int)

        def pad_with_delays(qubits: List[int], until) -> None:
            """Pad idle time-slots in ``qubits`` with delays until ``until``."""
            for q in qubits:
                if qubit_time_available[q] < until:
                    idle_duration = until - qubit_time_available[q]
                    new_dag.apply_operation_back(Delay(1, idle_duration), [q])

        for node in dag.topological_op_nodes():
            start_time = max(qubit_time_available[q] for q in node.qargs)
            pad_with_delays(node.qargs, until=start_time)

            duration = self.durations.get(node)
            node.op.duration = duration  # mutate original operation!
            new_dag.apply_operation_back(node.op, node.qargs, node.cargs, node.condition)

            stop_time = start_time + duration
            # update time table
            for q in node.qargs:
                qubit_time_available[q] = stop_time

        working_qubits = qubit_time_available.keys()  # FIXME: must include idle qubits?
        circuit_duration = max(qubit_time_available[q] for q in working_qubits)
        pad_with_delays(working_qubits, until=circuit_duration)

        new_dag.name = dag.name + '_asap'
        new_dag.duration = circuit_duration
        return new_dag
