# -*- coding: utf-8 -*-

# Copyright 2018, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.


"""Tests for all BasicAer  simulators."""

import unittest

import qiskit
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.compiler import transpile, assemble_circuits
from qiskit.compiler import TranspileConfig, RunConfig
from qiskit.qobj import QASMQobjHeader
from qiskit.test import QiskitTestCase, requires_aer_provider


@requires_aer_provider
class TestBasicAerQobj(QiskitTestCase):
    """Tests for all the Terra simulators."""

    def setUp(self):
        super().setUp()

        qr = QuantumRegister(1)
        cr = ClassicalRegister(1)
        self.qc1 = QuantumCircuit(qr, cr, name='circuit0')
        self.qc1.h(qr[0])

    def test_qobj_headers_in_result(self):
        """Test that the qobj headers are passed onto the results."""
        custom_qobj_header = {'x': 1, 'y': [1, 2, 3], 'z': {'a': 4}}
        for backend in qiskit.providers.aer.Aer.backends():
            with self.subTest(backend=backend):
                qc1_new = transpile(self.qc1, TranspileConfig(backend=backend))
                qobj = assemble_circuits(qc1_new, RunConfig(shots=1000))

                # Update the Qobj header.
                qobj.header = QASMQobjHeader.from_dict(custom_qobj_header)
                # Update the Qobj.experiment header.
                qobj.experiments[0].header.some_field = 'extra info'

                result = backend.run(qobj).result()
                self.assertEqual(result.header.to_dict(), custom_qobj_header)
                self.assertEqual(result.results[0].header.some_field,
                                 'extra info')

    @unittest.skip("skipping as aer does not support. I made an issue")
    def test_job_qobj(self):
        """Test job.qobj()."""
        for backend in qiskit.providers.aer.Aer.backends():
            with self.subTest(backend=backend):
                qc1_new = transpile(self.qc1, TranspileConfig(backend=backend))
                qobj = assemble_circuits(qc1_new, RunConfig(shots=1000))

                job = backend.run(qobj)
                self.assertEqual(job.qobj(), qobj)
