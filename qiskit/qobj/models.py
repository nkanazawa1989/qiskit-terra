# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.

"""Models for Qobj and its related components."""

from marshmallow.validate import Length, Range, Regexp, OneOf

from qiskit.validation.base import BaseModel, BaseSchema, bind_schema
from qiskit.validation.fields import (Integer, List, Nested, String,
                                      InstructionParameter, Number, Complex, Dict)

from .utils import MeasReturnType


class QobjConditionalSchema(BaseSchema):
    """Schema for QobjConditional."""

    # Required properties.
    mask = String(required=True, validate=Regexp('^0x([0-9A-Fa-f])+$'))
    type = String(required=True)
    val = String(required=True, validate=Regexp('^0x([0-9A-Fa-f])+$'))


class QobjMeasurementOptionSchema(BaseSchema):
    """Schema for QobjMeasOptiton."""

    # Required properties.
    name = String(required=True)
    # TODO : Need to prepare custom model for nested params?
    params = Dict(keys=String(), values=Number(), required=True)


class QobjPulseLibrarySchema(BaseSchema):
    """Schema for QobjPulseLibrary."""

    # Required properties.
    name = String(required=True)
    samples = List(Complex(), required=True, validate=Length(min=1))


class BaseQobjInstructionSchema(BaseSchema):
    """Base Schema for QobjInstruction."""

    # Required properties
    name = String(required=True)


class BaseQobjExperimentHeaderSchema(BaseSchema):
    """Base Schema for QobjExperimentHeader."""
    pass


class BaseQobjExperimentConfigSchema(BaseSchema):
    """Base Schema for QobjExperimentConfig."""
    pass


class BaseQobjExperimentSchema(BaseSchema):
    """Base Schema for QobjExperiment."""
    pass


class BaseQobjConfigSchema(BaseSchema):
    """Base Schema for QobjConfig."""

    # Optional properties.
    max_credits = Integer()
    seed = Integer()
    memory_slots = Integer(validate=Range(min=0))
    shots = Integer(validate=Range(min=1))


class BaseQobjHeaderSchema(BaseSchema):
    """Base Schema for QobjHeader."""

    # Optional properties.
    backend_name = String()
    backend_version = String()


class QASMQobjInstructionSchema(BaseQobjInstructionSchema):
    """Schema for QASMQobjInstruction."""

    # Optional properties.
    qubits = List(Integer(validate=Range(min=0)),
                  validate=Length(min=1))
    params = List(InstructionParameter())
    memory = List(Integer(validate=Range(min=0)),
                  validate=Length(min=1))
    conditional = Nested(QobjConditionalSchema)


class QASMQobjExperimentHeaderSchema(BaseQobjExperimentHeaderSchema):
    """Schema for QASMQobjExperimentHeader."""
    pass


class QASMQobjExperimentConfigSchema(BaseQobjExperimentConfigSchema):
    """Schema for QASMQobjExperimentConfig."""

    # Optional properties.
    memory_slots = Integer(validate=Range(min=0))
    n_qubits = Integer(validate=Range(min=1))


class QASMQobjExperimentSchema(BaseQobjExperimentSchema):
    """Schema for QASMQobjExperiment."""

    # Required properties.
    instructions = Nested(QASMQobjInstructionSchema, required=True, many=True,
                          validate=Length(min=1))

    # Optional properties.
    header = Nested(QASMQobjExperimentHeaderSchema)
    config = Nested(QASMQobjExperimentConfigSchema)


class QASMQobjConfigSchema(BaseQobjConfigSchema):
    """Schema for QASMQobjConfig."""

    # Optional properties.
    n_qubits = Integer(validate=Range(min=1))


class QASMQobjHeaderSchema(BaseQobjHeaderSchema):
    """Schema for QASMQobjHeader."""
    pass


class PulseQobjInstructionSchema(BaseQobjInstructionSchema):
    """Schema for PulseQobjInstruction."""
    # pylint: disable=invalid-name

    # Required properties
    t0 = Integer(required=True, validate=Range(min=0))

    # Optional properties.
    ch = String(validate=Regexp('[dum]([0-9])+'))
    conditional = Integer(validate=Range(min=0))
    phase = Number()
    val = Complex()
    duration = Integer(validate=Range(min=1))
    qubits = List(Integer(validate=Range(min=0)), validate=Length(min=1))
    memory_slot = List(Integer(validate=Range(min=0)), validate=Length(min=1))
    register_slot = List(Integer(validate=Range(min=0)), validate=Length(min=1))
    kernels = Nested(QobjMeasurementOptionSchema, many=True)
    discriminators = Nested(QobjMeasurementOptionSchema, many=True)
    label = String()
    type = String()


class PulseQobjExperimentHeaderSchema(BaseQobjExperimentHeaderSchema):
    """Schema for PulseQobjExperimentHeader."""
    pass


class PulseQobjExperimentConfigSchema(BaseQobjExperimentConfigSchema):
    """Schema for PulseQobjExperimentConfig."""

    # Optional properties.
    qubit_lo_freq = List(Number())
    meas_lo_freq = List(Number())


class PulseQobjExperimentSchema(BaseQobjExperimentSchema):
    """Schema for PulseQobjExperiment."""

    # Required properties.
    instructions = Nested(PulseQobjInstructionSchema, required=True, many=True,
                          validate=Length(min=1))

    # Optional properties.
    header = Nested(PulseQobjExperimentHeaderSchema)
    config = Nested(PulseQobjExperimentConfigSchema)


class PulseQobjConfigSchema(BaseQobjConfigSchema):
    """Schema for PulseQobjConfig."""

    # Required properties.
    # TODO : check if they are always required by backend
    meas_level = Integer(required=True, validate=Range(min=0, max=2))
    memory_slot_size = Integer(required=True)
    pulse_library = Nested(QobjPulseLibrarySchema, many=True)
    qubit_lo_freq = List(Number(), required=True)
    meas_lo_freq = List(Number(), required=True)
    rep_time = Integer(required=True)
    meas_return = String(validate=OneOf(MeasReturnType.AVERAGE,
                                        MeasReturnType.SINGLE))


class PulseQobjHeaderSchema(BaseQobjHeaderSchema):
    """Schema for PulseQobjHeader."""
    pass


@bind_schema(QobjConditionalSchema)
class QobjConditional(BaseModel):
    """Model for QobjConditional.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QobjConditionalSchema``.

    Attributes:
        mask (str): hexadecimal mask of the conditional
        type (str): type of the conditional
        val (str): hexadecimal value of the conditional
    """
    def __init__(self, mask, type, val, **kwargs):
        # pylint: disable=redefined-builtin
        self.mask = mask
        self.type = type
        self.val = val

        super().__init__(**kwargs)


@bind_schema(QobjMeasurementOptionSchema)
class QobjMeasurementOption(BaseModel):
    """Model for QobjMeasurementOption.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QobjMeasurementOptionSchema``.

    Attributes:
        name (str): name of option specified in the backend
        params (dict): measurement parameter
    """
    def __init__(self, name, params, **kwargs):
        self.name = name
        self.params = params

        super().__init__(**kwargs)


@bind_schema(QobjPulseLibrarySchema)
class QobjPulseLibrary(BaseModel):
    """Model for QobjPulseLibrary.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QobjPulseLibrarySchema``.

    Attributes:
        name (str): name of pulse
        samples (list[complex]]): list of complex values defining pulse shape
    """

    def __init__(self, name, samples, **kwargs):
        self.name = name
        self.samples = samples

        super().__init__(**kwargs)


@bind_schema(BaseQobjInstructionSchema)
class QobjInstruction(BaseModel):
    """Model for QobjInstruction.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``BaseQobjInstructionSchema``.

    Attributes:
        name (str): name of the instruction
    """
    def __init__(self, name, **kwargs):
        self.name = name

        super().__init__(**kwargs)


@bind_schema(BaseQobjExperimentHeaderSchema)
class QobjExperimentHeader(BaseModel):
    """Model for QobjExperimentHeader.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``BaseQobjExperimentHeaderSchema``.
    """
    pass


@bind_schema(BaseQobjExperimentConfigSchema)
class QobjExperimentConfig(BaseModel):
    """Model for QobjExperimentConfig.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``BaseQobjExperimentConfigSchema``.
    """
    pass


@bind_schema(BaseQobjExperimentSchema)
class QobjExperiment(BaseModel):
    """Model for QobjExperiment.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``BaseQobjExperimentSchema``.

    Attributes:
        instructions (list[QobjInstruction]): list of instructions.
    """
    def __init__(self, instructions, **kwargs):
        self.instructions = instructions

        super().__init__(**kwargs)


@bind_schema(BaseQobjConfigSchema)
class QobjConfig(BaseModel):
    """Model for QobjConfig.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``BaseQobjConfigSchema``.
    """
    pass


@bind_schema(BaseQobjHeaderSchema)
class QobjHeader(BaseModel):
    """Model for QobjHeader.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``BaseQASMQobjHeaderSchema``.
    """
    pass


@bind_schema(QASMQobjInstructionSchema)
class QASMQobjInstruction(QobjInstruction):
    """Model for QASMQobjInstruction inherit from QobjInstruction.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QASMQobjInstructionSchema``.

    Attributes:
        name (str): name of the instruction
    """
    def __init__(self, name, **kwargs):
        super().__init__(name=name,
                         **kwargs)


@bind_schema(QASMQobjExperimentHeaderSchema)
class QASMQobjExperimentHeader(QobjExperimentHeader):
    """Model for QASMQobjExperimentHeader inherit from QobjExperimentHeader.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QASMQobjExperimentHeaderSchema``.
    """
    pass


@bind_schema(QASMQobjExperimentConfigSchema)
class QASMQobjExperimentConfig(QobjExperimentConfig):
    """Model for QASMQobjExperimentConfig inherit from QobjExperimentConfig.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QASMQobjExperimentConfigSchema``.
    """
    pass


@bind_schema(QASMQobjExperimentSchema)
class QASMQobjExperiment(QobjExperiment):
    """Model for QASMQobjExperiment inherit from QobjExperiment.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QASMQobjExperimentSchema``.

    Attributes:
        instructions (list[QASMQobjInstruction]): list of instructions.
    """
    def __init__(self, instructions, **kwargs):
        super().__init__(instructions=instructions,
                         **kwargs)


@bind_schema(QASMQobjConfigSchema)
class QASMQobjConfig(QobjConfig):
    """Model for QASMQobjConfig inherit from QobjConfig.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QASMQobjConfigSchema``.
    """
    pass


@bind_schema(QASMQobjHeaderSchema)
class QASMQobjHeader(QobjHeader):
    """Model for QASMQobjHeader inherit from QobjHeader.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``QASMQobjHeaderSchema``.
    """
    pass


@bind_schema(PulseQobjInstructionSchema)
class PulseQobjInstruction(QobjInstruction):
    """Model for PulseQobjInstruction inherit from QobjInstruction.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``PulseQobjInstructionSchema``.

    Attributes:
        name (str): name of the instruction
        t0 (int): timing of executing the instruction
    """
    def __init__(self, name, t0, **kwargs):
        # pylint: disable=invalid-name
        super().__init__(name=name,
                         t0=t0,
                         **kwargs)


@bind_schema(PulseQobjExperimentHeaderSchema)
class PulseQobjExperimentHeader(QobjExperimentHeader):
    """Model for PulseQobjExperimentHeader inherit from QobjExperimentHeader.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``PulseQobjExperimentHeaderSchema``.
    """
    pass


@bind_schema(PulseQobjExperimentConfigSchema)
class PulseQobjExperimentConfig(QobjExperimentConfig):
    """Model for PulseQobjExperimentConfig inherit from QobjExperimentConfig.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``PulseQobjExperimentConfigSchema``.
    """
    pass


@bind_schema(PulseQobjExperimentSchema)
class PulseQobjExperiment(QobjExperiment):
    """Model for PulseQobjExperiment inherit from QobjExperiment.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``PulseQobjExperimentSchema``.

    Attributes:
        instructions (list[PulseQobjInstruction]): list of instructions.
    """
    def __init__(self, instructions, **kwargs):
        super().__init__(instructions=instructions,
                         **kwargs)


@bind_schema(PulseQobjConfigSchema)
class PulseQobjConfig(QobjConfig):
    """Model for PulseQobjConfig inherit from QobjConfig.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``PulseQobjConfigSchema``.

    Attributes:
        meas_level (int): a value represents the level of measurement.
        memory_slot_size (int): size of memory slot
        meas_return (str): a level of measurement information.
        pulse_library (list[QobjPulseLibrary]): a pulse library.
        qubit_lo_freq (list): the list of frequencies for qubit drive LO's in GHz.
        meas_lo_freq (list): the list of frequencies for measurement drive LO's in GHz.
        rep_time (int): the value of repetition time of experiment in us.
    """
    def __init__(self, meas_level, memory_slot_size, meas_return,
                 pulse_library, qubit_lo_freq, meas_lo_freq, rep_time,
                 **kwargs):
        super().__init__(meas_level=meas_level,
                         memory_slot_size=memory_slot_size,
                         meas_return=meas_return,
                         pulse_library=pulse_library,
                         qubit_lo_freq=qubit_lo_freq,
                         meas_lo_freq=meas_lo_freq,
                         rep_time=rep_time,
                         **kwargs)


@bind_schema(PulseQobjHeaderSchema)
class PulseQobjHeader(QobjHeader):
    """Model for PulseQobjHeader inherit from QobjHeader.

    Please note that this class only describes the required fields. For the
    full description of the model, please check ``PulseQobjHeaderSchema``.
    """
    pass


class QobjConfig(QASMQobjConfig):
    """Fake for qiskit provider."""
    pass
