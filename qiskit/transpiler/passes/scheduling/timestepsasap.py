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

"""Timesteps ASAP Scheduling."""
import copy

from qiskit.circuit.delay import Delay
from qiskit.circuit.timestep import Timestep
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError

from .utils import DurationMapper


class TimestepsASAPSchedule(TransformationPass):
    """Timesteps ASAP Scheduling."""

    def __init__(self, backend):
        """TimestepsASAPSchedule initializer.

        Args:
            backend (Backend): .
        """
        super().__init__()
        self.durations = DurationMapper(backend)

    def run(self, dag):
        """Run the TimestepsASAPSchedule pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to schedule.

        Returns:
            DAGCircuit: A scheduled DAG.

        Raises:
            TranspilerError: if ...
        """
        if len(dag.qregs) != 1 or dag.qregs.get('q', None) is None:
            raise TranspilerError('TimestepsASAPSchedule runs on physical circuits only')

        new_dag = DAGCircuit()
        for qreg in dag.qregs.values():
            new_dag.add_qreg(qreg)
        for creg in dag.cregs.values():
            new_dag.add_creg(creg)

        circuit_duration = 0

        # track frontier
        residual_dag = copy.deepcopy(dag)
        for n in residual_dag.op_nodes():  # compute durations at first
            duration = self.durations.get(n)
            n.op.duration = duration  # overwrite duration (tricky but necessary)
            if isinstance(n.op, Delay):  # overwrite params! (tricky but necessary)
                n.op.params = [duration]

        frontier = residual_dag.leading_op_nodes()
        print([(n.op.name, [q.index for q in n.qargs[:2]]) for n in frontier])
        max_n_iteration = dag.size()
        for k in range(1, max_n_iteration + 1):  # escape infinite loop
            if not frontier:
                break

            # find dominant node
            frontier = sorted(frontier, key=lambda x: x.op.duration, reverse=True)
            dominant = frontier[0]
            timestep_duration = dominant.op.duration

            # process nodes within dominant.op.duration complying with dependency constraint
            timelimit = {q: timestep_duration for q in residual_dag.qubits()}
            dones = []
            news = frontier
            while news:
                dones.extend(news)
                for n in news:
                    for q in n.qargs:
                        timelimit[q] -= n.op.duration
                    residual_dag.remove_op_node(n)

                news = []
                frontier = residual_dag.leading_op_nodes()
                for n in frontier:
                    if n.op.duration <= timelimit[q]:
                        news.append(n)

            # TODO: split deley in frontier

            # schedule dones
            for n in dones:
                new_dag.apply_operation_back(n.op, n.qargs, n.cargs, n.condition)

            # pad with delays if positive idle duration in the qubit
            for q, idle_duration in timelimit.items():
                if idle_duration > 0:
                    new_dag.apply_operation_back(Delay(1, idle_duration), [q])

            # append timestep
            new_dag.apply_operation_back(Timestep(num_qubits=new_dag.num_qubits(),
                                                  length=timestep_duration),
                                         new_dag.qubits())

            circuit_duration += timestep_duration

            if k == max_n_iteration:
                raise TranspilerError("Unknown error: #iteration reached max_n_iteration")

        new_dag.name = dag.name
        new_dag.duration = circuit_duration
        return new_dag
