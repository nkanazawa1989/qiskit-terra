# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=invalid-name

"""
Specification of the device.
"""
from typing import List

from .channels import AcquireChannel, MemorySlot, RegisterSlot
from .pulse_channels import DriveChannel, ControlChannel, MeasureChannel
from .qubit import Qubit


class PulseSpecification:
    """A helper class to support assembling channel objects and their mapping to qubits.
    This class can be initialized with two methods shown as below.

    1. When you have BaseBackend object of the target quantum device.
        ```python
        device = PulseSpecification.from_device(backend)
        ```

    2. When you know the number of elements constituting the target quantum device.
        ```python
        device = PulseSpecification(n_qubits=5, n_control=6, n_registers=1, buffer=10)
        ```

    A quantum device consists of pulse channels, acquires, memory slots, and register slots.
    Drive, control and measure channels compose the pulse channels.
    All these channels generate microwave pulses mixed with their local oscillators.
    Each measure channels, acquires, and memory slots are tightly bound to construct
    a measurement chain. Readout microwave pulses are generated by measurement channels,
    and signals from the device are acquired by acquires. The result is stored in memory slots.
    Discriminated quantum state can be transferred to arbitrary register slots.
    The aggregation of above channels is automatically assembled within `PulseSpecification`.

    When you provide a drive channel object to create `Schedule`, you can refer the channel by
        ```python
        device.drives[0]
        ```
    or if the channel is connected to qubit0,
        ```python
        device.qubits[0].drive
        ```
    In above example, both commands refer the same object.
    """
    def __init__(self,
                 n_qubits: int,
                 n_control: int,
                 n_registers: int,
                 buffer: int = 0):
        """
        Create pulse specification with number of channels.

        Args:
            n_qubits: Number of qubits.
            n_control: Number of control channels.
            n_registers: Number of classical registers.
            buffer: Buffer that should be placed between instructions on channel.
        """
        self._drives = [DriveChannel(idx, buffer) for idx in range(n_qubits)]
        self._controls = [ControlChannel(idx, buffer) for idx in range(n_control)]
        self._measures = [MeasureChannel(idx, buffer) for idx in range(n_qubits)]
        self._acquires = [AcquireChannel(idx, buffer) for idx in range(n_qubits)]
        self._mem_slots = [MemorySlot(idx) for idx in range(n_qubits)]
        self._reg_slots = [RegisterSlot(idx) for idx in range(n_registers)]

        # TODO: allow for more flexible mapping of channels by using device Hamiltonian.
        self._qubits = []
        for ii, (drive, measure, acquire) in enumerate(zip(self._drives,
                                                           self._measures,
                                                           self._acquires)):
            self._qubits.append(Qubit(ii, drive, measure, acquire))

    @classmethod
    def from_device(cls, backend):
        """
        Create pulse specification with values from backend.

        Args:
            backend (BaseBackend): Backend configuration.

        Returns:
            PulseSpecification: New PulseSpecification configured by backend.
        """
        configuration = backend.configuration()
        defaults = backend.defaults()

        # TODO: allow for drives/measures which are not identical to number of qubit
        n_qubits = configuration.n_qubits
        n_controls = configuration.n_uchannels
        n_registers = configuration.n_registers
        buffer = defaults.buffer

        return PulseSpecification(n_qubits=n_qubits, n_control=n_controls,
                                  n_registers=n_registers, buffer=buffer)

    @property
    def drives(self) -> List[DriveChannel]:
        """Return drive channel in this device."""
        return self._drives

    @property
    def controls(self):
        """Return control channel in this device."""
        return self._controls

    @property
    def measures(self):
        """Return measure channel in this device."""
        return self._measures

    @property
    def acquires(self):
        """Return acquire channel in this device."""
        return self._acquires

    @property
    def qubits(self) -> List[Qubit]:
        """Return qubits in this device."""
        return self._qubits

    @property
    def registers(self) -> List[RegisterSlot]:
        """Return register slots in this device."""
        return self._reg_slots

    @property
    def memoryslots(self) -> List[MemorySlot]:
        """Return memory slots in this device."""
        return self._mem_slots
