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

"""Durations of instructions, one of transpiler configurations."""
import warnings
from typing import Optional, List, Tuple, Iterable

from qiskit.transpiler.exceptions import TranspilerError


class InstructionDurations:
    def __init__(self,
                 instruction_durations: Optional[List[Tuple[str, Iterable[int], int]]] = None,
                 dt=None):
        self.duration_dic = {}
        self.dt = dt
        if instruction_durations:
            for name, qubits, duration in instruction_durations:
                # TODO: value check
                self.duration_dic[(name, tuple(qubits))] = duration

    @classmethod
    def from_backend(cls, backend):
        if backend is None:
            return InstructionDurations()
        # TODO: backend.properties() should let us know all about instruction durations
        if not backend.configuration().open_pulse:
            raise TranspilerError("DurationMapper needs backend.configuration().dt")
        dt = backend.configuration().dt
        instruction_durations = []
        # backend.properties._gates -> instruction_durations
        for gate, insts in backend.properties()._gates.items():
            for qubits, props in insts.items():
                if 'gate_length' in props:
                    gate_length = props['gate_length'][0]  # Throw away datetime at index 1
                    duration = round(gate_length / dt)
                    rounding_error = abs(gate_length - duration * dt)
                    if rounding_error > 1e-15:
                        warnings.warn("Duration of %s is rounded to %d dt = %e s from %e"
                                      % (gate, duration, duration * dt, gate_length),
                                      UserWarning)
                    instruction_durations.append((gate, qubits, duration))
        # To know duration of measures, to be removed
        inst_map = backend.defaults().instruction_schedule_map
        all_qubits = tuple([i for i in range(backend.configuration().num_qubits)])
        meas_duration = inst_map.get('measure', all_qubits).duration
        for q in all_qubits:
            instruction_durations.append(('measure', [q], meas_duration))
        return InstructionDurations(instruction_durations, dt)

    def update(self,
               instruction_durations: Optional[List[Tuple[str, Iterable[int], int]]] = None,
               dt=None):
        if self.dt and dt and self.dt != dt:
            raise TranspilerError("dt must be the same to update")

        self.dt = dt or self.dt

        if instruction_durations:
            for name, qubits, duration in instruction_durations:
                self.duration_dic[(name, tuple(qubits))] = duration

        return self

    def get(self, name, qubits):
        if name in {'barrier', 'timestep'}:
            return 0

        return self.duration_dic[(name, tuple(qubits))]
