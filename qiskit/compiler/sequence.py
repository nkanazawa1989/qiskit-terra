# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
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
import logging
from collections import defaultdict
from typing import List, Optional, Union

from qiskit.circuit.barrier import Barrier
from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.exceptions import QiskitError
from qiskit.providers import BaseBackend
from qiskit.pulse import InstructionScheduleMap, Schedule
from qiskit.pulse.transforms import pad
from qiskit.scheduler import ScheduleConfig
from qiskit.scheduler.methods.basic import translate_gates_to_pulse_defs

LOG = logging.getLogger(__name__)


def sequence(scheduled_circuits: Union[QuantumCircuit, List[QuantumCircuit]],
             backend: Optional[BaseBackend] = None,
             inst_map: Optional[InstructionScheduleMap] = None,
             meas_map: Optional[List[List[int]]] = None,
             dt: Optional[float] = None) -> Union[Schedule, List[Schedule]]:
    """
    Schedule a scheduled circuit to a pulse ``Schedule``, using the backend.

    Args:
        scheduled_circuits: The scheduled quantum circuit or circuits to translate
        backend: A backend instance, which contains hardware-specific data required for scheduling
        inst_map: Mapping of circuit operations to pulse schedules. If ``None``, defaults to the
                  ``backend``\'s ``instruction_schedule_map``
        meas_map: List of sets of qubits that must be measured together. If ``None``, defaults to
                  the ``backend``\'s ``meas_map``
        dt: For scheduled circuits which contain time information, dt is required. If not provided,
            it will be obtained from the backend configuration

    Returns:
        A pulse ``Schedule`` that implements the input circuit

    Raises:
        QiskitError: If ``inst_map`` and ``meas_map`` are not passed and ``backend`` is not passed
    """
    if inst_map is None:
        if backend is None:
            raise QiskitError("Must supply either a backend or InstructionScheduleMap for "
                              "scheduling passes.")
        inst_map = backend.defaults().instruction_schedule_map
    if meas_map is None:
        if backend is None:
            raise QiskitError("Must supply either a backend or a meas_map for scheduling passes.")
        meas_map = backend.configuration().meas_map
    if dt is None:
        if backend is None:
            raise QiskitError("Must supply either a backend or the value of dt.")
        dt = backend.configuration().dt

    schedule_config = ScheduleConfig(inst_map=inst_map, meas_map=meas_map, dt=dt)
    circuits = scheduled_circuits if isinstance(scheduled_circuits, list) else [scheduled_circuits]
    schedules = [_sequence(circuit, schedule_config) for circuit in circuits]
    return schedules[0] if len(schedules) == 1 else schedules


def _sequence(scheduled_circuit: QuantumCircuit, schedule_config: ScheduleConfig) -> Schedule:
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
        for q in qubits:
            if qubit_time_available[q] != start_time:
                raise Exception("Bug in scheduling pass.")

        start_times.append(start_time)
        for q in qubits:
            qubit_time_available[q] += inst.duration

    circ_pulse_defs = translate_gates_to_pulse_defs(scheduled_circuit, schedule_config)
    timed_schedules = [(time, cpd.schedule) for time, cpd in zip(start_times, circ_pulse_defs)
                       if not isinstance(cpd.schedule, Barrier)]
    # for time, sched in timed_schedules:
    #     print(time, sched.name, sched.duration, sched.channels)
    sched = Schedule(*timed_schedules, name=scheduled_circuit.name)
    assert(sched.duration == scheduled_circuit.duration)
    return pad(sched)
