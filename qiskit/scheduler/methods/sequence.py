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
TODO: TO be filled.
"""
from collections import defaultdict

from qiskit.circuit.barrier import Barrier
from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.pulse.schedule import Schedule
from qiskit.pulse.transforms import pad

from qiskit.scheduler.config import ScheduleConfig
from qiskit.scheduler.methods.lowering import lower_gates


def sequence(scheduled_circuit: QuantumCircuit, schedule_config: ScheduleConfig) -> Schedule:
    """
    Return the pulse Schedule which implements the input circuit using an "as soon as possible"
    (asap) scheduling policy.

    Circuit instructions are first each mapped to equivalent pulse
    Schedules according to the command definition given by the schedule_config.

    Args:
        scheduled_circuit: The scheduled quantum circuit to translate.
        schedule_config: Backend specific parameters used for building the Schedule.

    Returns:
        A schedule corresponding to the input ``circuit``.
    """
    # trace start times
    qubit_time_available = defaultdict(int)
    start_times = []
    for inst, qubits, _ in scheduled_circuit.data:
        start_time = qubit_time_available[qubits[0]]
        # for q in qubits:
        #     if qubit_time_available[q] != start_time:
        #         raise Exception("Bug in scheduling pass.")

        start_times.append(start_time)
        for q in qubits:
            qubit_time_available[q] += inst.duration

    circ_pulse_defs = lower_gates(scheduled_circuit, schedule_config)
    timed_schedules = [(time, cpd.schedule) for time, cpd in zip(start_times, circ_pulse_defs)
                       if not isinstance(cpd.schedule, Barrier)]
    # for time, sched in timed_schedules:
    #     print(time, sched.name, sched.duration, sched.channels)
    sched = Schedule(*timed_schedules, name=scheduled_circuit.name)
    assert sched.duration == scheduled_circuit.duration
    return pad(sched)
