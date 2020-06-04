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

"""ALAP Timestep Scheduling."""

from qiskit.circuit.timestep import Timestep
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError

from .asaptimestep import ASAPTimestepSchedule


class ALAPTimestepSchedule(TransformationPass):
    """ALAP Timestep Scheduling."""

    def __init__(self, backend):
        """ALAPTimestepSchedule initializer.

        Args:
            backend (Backend): .
        """
        super().__init__()
        self.asap = ASAPTimestepSchedule(backend)

    def run(self, dag):
        """Run the ALAPTimestepSchedule pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to schedule.

        Returns:
            DAGCircuit: A scheduled DAG.

        Raises:
            TranspilerError: if ...
        """
        if len(dag.qregs) != 1 or dag.qregs.get('q', None) is None:
            raise TranspilerError('ALAPTimestepSchedule runs on physical circuits only')

        new_dag = DAGCircuit()
        for qreg in dag.qregs.values():
            new_dag.add_qreg(qreg)
        for creg in dag.cregs.values():
            new_dag.add_creg(creg)

        tmp_dag = dag.mirror()
        tmp_dag = self.asap.run(tmp_dag)
        tmp_dag = tmp_dag.mirror()

        # shift timesteps
        prev = None
        for node in tmp_dag.topological_op_nodes():
            if isinstance(node.op, Timestep):
                if prev:
                    new_dag.apply_operation_back(prev.op, prev.qargs, prev.cargs, prev.condition)
                prev = node
            else:
                new_dag.apply_operation_back(node.op, node.qargs, node.cargs, node.condition)

        if prev:
            new_dag.apply_operation_back(prev.op, prev.qargs, prev.cargs, prev.condition)

        new_dag.name = dag.name
        new_dag.duration = tmp_dag.name
        return new_dag
