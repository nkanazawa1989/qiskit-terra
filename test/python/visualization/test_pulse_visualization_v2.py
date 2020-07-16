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

# pylint: disable=missing-docstring, invalid-name

"""Tests for IR generation of pulse visualization."""

import numpy as np

from qiskit import pulse
from qiskit.test import QiskitTestCase
from qiskit.visualization.pulse_v2 import (drawing_objects,
                                           events,
                                           core,
                                           generators,
                                           layouts,
                                           data_types,
                                           PULSE_STYLE)
from qiskit.visualization.pulse_v2.style import stylesheet


class TestChannelEvents(QiskitTestCase):
    """Tests for ChannelEvents."""
    def test_parse_program(self):
        """Test typical pulse program."""
        test_pulse = pulse.Gaussian(10, 0.1, 3)

        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.SetPhase(3.14, pulse.DriveChannel(0)))
        sched = sched.insert(0, pulse.Play(test_pulse, pulse.DriveChannel(0)))
        sched = sched.insert(10, pulse.ShiftPhase(-1.57, pulse.DriveChannel(0)))
        sched = sched.insert(10, pulse.Play(test_pulse, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))

        # check waveform data
        waveforms = list(ch_events.get_waveforms())
        inst_data0 = waveforms[0]
        self.assertEqual(inst_data0.t0, 0)
        self.assertEqual(inst_data0.frame.phase, 3.14)
        self.assertEqual(inst_data0.frame.freq, 0)
        self.assertEqual(inst_data0.inst, pulse.Play(test_pulse, pulse.DriveChannel(0)))

        inst_data1 = waveforms[1]
        self.assertEqual(inst_data1.t0, 10)
        self.assertEqual(inst_data1.frame.phase, 1.57)
        self.assertEqual(inst_data1.frame.freq, 0)
        self.assertEqual(inst_data1.inst, pulse.Play(test_pulse, pulse.DriveChannel(0)))

        # check frame data
        frames = list(ch_events.get_frame_changes())
        inst_data0 = frames[0]
        self.assertEqual(inst_data0.t0, 0)
        self.assertEqual(inst_data0.frame.phase, 3.14)
        self.assertEqual(inst_data0.frame.freq, 0)
        self.assertListEqual(inst_data0.inst, [pulse.SetPhase(3.14, pulse.DriveChannel(0))])

        inst_data1 = frames[1]
        self.assertEqual(inst_data1.t0, 10)
        self.assertEqual(inst_data1.frame.phase, -1.57)
        self.assertEqual(inst_data1.frame.freq, 0)
        self.assertListEqual(inst_data1.inst, [pulse.ShiftPhase(-1.57, pulse.DriveChannel(0))])

    def test_empty(self):
        """Test is_empty check."""
        test_pulse = pulse.Gaussian(10, 0.1, 3)

        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.ShiftPhase(1.57, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))
        self.assertTrue(ch_events.is_empty())

        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.Play(test_pulse, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))
        self.assertFalse(ch_events.is_empty())

    def test_multiple_frames_at_the_same_time(self):
        """Test multiple frame instruction at the same time."""
        # shift phase followed by set phase
        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.ShiftPhase(-1.57, pulse.DriveChannel(0)))
        sched = sched.insert(0, pulse.SetPhase(3.14, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))
        frames = list(ch_events.get_frame_changes())
        inst_data0 = frames[0]
        self.assertAlmostEqual(inst_data0.frame.phase, 3.14)

        # set phase followed by shift phase
        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.SetPhase(3.14, pulse.DriveChannel(0)))
        sched = sched.insert(0, pulse.ShiftPhase(-1.57, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))
        frames = list(ch_events.get_frame_changes())
        inst_data0 = frames[0]
        self.assertAlmostEqual(inst_data0.frame.phase, 1.57)

    def test_frequency(self):
        """Test parse frequency."""
        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.ShiftFrequency(1.0, pulse.DriveChannel(0)))
        sched = sched.insert(5, pulse.SetFrequency(5.0, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))
        ch_events.config(dt=0.1, init_frequency=3.0, init_phase=0)
        frames = list(ch_events.get_frame_changes())

        inst_data0 = frames[0]
        self.assertAlmostEqual(inst_data0.frame.freq, 1.0)

        inst_data1 = frames[1]
        self.assertAlmostEqual(inst_data1.frame.freq, 1.0)

    def test_min_max(self):
        """Test get min max value of channel."""
        test_pulse = pulse.Gaussian(10, 0.1, 3)

        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.Play(test_pulse, pulse.DriveChannel(0)))

        ch_events = events.ChannelEvents.load_program(sched, pulse.DriveChannel(0))

        min_v, max_v = ch_events.get_min_max((0, sched.duration))

        samples = test_pulse.get_sample_pulse().samples

        self.assertAlmostEqual(min_v, min(*samples.real, *samples.imag))
        self.assertAlmostEqual(max_v, max(*samples.real, *samples.imag))


class TestDrawingObjects(QiskitTestCase):
    """Tests for DrawingObjects."""
    def test_filled_area_data(self):
        """Test FilledAreaData."""
        data1 = drawing_objects.FilledAreaData(data_type='waveform',
                                               channel=pulse.DriveChannel(0),
                                               x=np.array([0, 1, 2]),
                                               y1=np.array([3, 4, 5]),
                                               y2=np.array([0, 0, 0]),
                                               meta={'test_val': 0},
                                               offset=0,
                                               scale=1,
                                               visible=True,
                                               styles={'color': 'red'})

        data2 = drawing_objects.FilledAreaData(data_type='waveform',
                                               channel=pulse.DriveChannel(0),
                                               x=np.array([0, 1, 2]),
                                               y1=np.array([3, 4, 5]),
                                               y2=np.array([0, 0, 0]),
                                               meta={'test_val': 1},
                                               offset=1,
                                               scale=2,
                                               visible=False,
                                               styles={'color': 'blue'})

        self.assertEqual(data1, data2)

    def test_line_data(self):
        """Test for LineData."""
        data1 = drawing_objects.LineData(data_type='baseline',
                                         channel=pulse.DriveChannel(0),
                                         x=np.array([0, 1, 2]),
                                         y=np.array([0, 0, 0]),
                                         meta={'test_val': 0},
                                         offset=0,
                                         scale=1,
                                         visible=True,
                                         styles={'color': 'red'})

        data2 = drawing_objects.LineData(data_type='baseline',
                                         channel=pulse.DriveChannel(0),
                                         x=np.array([0, 1, 2]),
                                         y=np.array([0, 0, 0]),
                                         meta={'test_val': 1},
                                         offset=1,
                                         scale=2,
                                         visible=False,
                                         styles={'color': 'blue'})

        self.assertEqual(data1, data2)

    def test_vertical_line_data(self):
        """Test for VerticalLineData."""
        data1 = drawing_objects.VerticalLineData(data_type='test_vline',
                                                 channel=pulse.DriveChannel(0),
                                                 x0=0,
                                                 meta={'test_val': 0},
                                                 offset=0,
                                                 scale=1,
                                                 visible=True,
                                                 styles={'color': 'red'})

        data2 = drawing_objects.VerticalLineData(data_type='test_vline',
                                                 channel=pulse.DriveChannel(0),
                                                 x0=0,
                                                 meta={'test_val': 1},
                                                 offset=1,
                                                 scale=2,
                                                 visible=False,
                                                 styles={'color': 'blue'})

        self.assertEqual(data1, data2)

    def test_horizontal_line_data(self):
        """Test for HorizontalLineData."""
        data1 = drawing_objects.HorizontalLineData(data_type='test_hline',
                                                   channel=pulse.DriveChannel(0),
                                                   y0=0,
                                                   meta={'test_val': 0},
                                                   offset=0,
                                                   scale=1,
                                                   visible=True,
                                                   styles={'color': 'red'})

        data2 = drawing_objects.HorizontalLineData(data_type='test_hline',
                                                   channel=pulse.DriveChannel(0),
                                                   y0=0,
                                                   meta={'test_val': 1},
                                                   offset=1,
                                                   scale=2,
                                                   visible=False,
                                                   styles={'color': 'blue'})

        self.assertEqual(data1, data2)

    def test_text_data(self):
        """Test for TextData."""
        data1 = drawing_objects.TextData(data_type='pulse_label',
                                         channel=pulse.DriveChannel(0),
                                         x=0,
                                         y=0,
                                         text='my_text1',
                                         latex='my_syntax1',
                                         meta={'test_val': 0},
                                         offset=0,
                                         scale=1,
                                         visible=True,
                                         styles={'color': 'red'})

        data2 = drawing_objects.TextData(data_type='pulse_label',
                                         channel=pulse.DriveChannel(0),
                                         x=0,
                                         y=0,
                                         text='my_text2',
                                         latex='my_syntax2',
                                         meta={'test_val': 1},
                                         offset=1,
                                         scale=2,
                                         visible=False,
                                         styles={'color': 'blue'})

        self.assertEqual(data1, data2)


class TestStylesheet(QiskitTestCase):
    """Tests for stylesheet."""
    def test_key_flatten(self):
        """Test flatten dictionary generation."""
        input_dict = {
            'key1': {
                'key2': {
                    'key3-1': 0,
                    'key3-2': 1
                }
            }
        }
        flatten_dict = {
            'key1.key2.key3-1': 0,
            'key1.key2.key3-2': 1

        }

        test_style = stylesheet.QiskitPulseStyle()
        test_style.style = input_dict

        self.assertDictEqual(test_style.style, flatten_dict)


class TestGenerators(QiskitTestCase):
    """Tests for generators."""

    def setUp(self) -> None:
        self.style = stylesheet.init_style_from_file().style

    @staticmethod
    def create_instruction(inst, phase, freq, t0, dt):
        """A helper function to create InstructionTuple."""
        frame = data_types.PhaseFreqTuple(phase=phase, freq=freq)
        return data_types.InstructionTuple(t0=t0, dt=dt, frame=frame, inst=inst)

    def test_gen_filled_waveform_stepwise_play(self):
        """Test gen_filled_waveform_stepwise with play instruction."""
        my_pulse = pulse.Waveform(samples=[0, 0.5+0.5j, 0.5+0.5j, 0], name='my_pulse')
        play = pulse.Play(my_pulse, pulse.DriveChannel(0))
        inst_data = self.create_instruction(play, np.pi/2, 5e9, 5, 0.1)
        objs = generators.gen_filled_waveform_stepwise(inst_data)

        self.assertEqual(len(objs), 2)

        # type check
        self.assertEqual(type(objs[0]), drawing_objects.FilledAreaData)
        self.assertEqual(type(objs[1]), drawing_objects.FilledAreaData)

        y1_ref = np.array([0, 0, -0.5, -0.5, -0.5, -0.5, 0, 0])
        y2_ref = np.array([0, 0, 0, 0, 0, 0, 0, 0])

        # data check
        self.assertEqual(objs[0].channel, pulse.DriveChannel(0))
        self.assertListEqual(list(objs[0].x), [5, 6, 6, 7, 7, 8, 8, 9])
        np.testing.assert_array_almost_equal(objs[0].y1, y1_ref)
        np.testing.assert_array_almost_equal(objs[0].y2, y2_ref)

        # meta data check
        ref_meta = {'duration (cycle time)': 4,
                    'duration (sec)': 0.4,
                    't0 (cycle time)': 5,
                    't0 (sec)': 0.5,
                    'phase': np.pi/2,
                    'frequency': 5e9,
                    'name': 'my_pulse',
                    'data': 'real'}
        self.assertDictEqual(objs[0].meta, ref_meta)

        # style check
        ref_style = {'alpha': self.style['formatter.alpha.fill_waveform'],
                     'zorder': self.style['formatter.layer.fill_waveform'],
                     'linewidth': self.style['formatter.line_width.fill_waveform'],
                     'linestyle': self.style['formatter.line_style.fill_waveform'],
                     'color': self.style['formatter.color.fill_waveform_d'][0]}
        self.assertDictEqual(objs[0].styles, ref_style)

    def test_gen_filled_waveform_stepwise_acquire(self):
        """Test gen_filled_waveform_stepwise with acquire instruction."""
        acquire = pulse.Acquire(duration=4,
                                channel=pulse.AcquireChannel(0),
                                mem_slot=pulse.MemorySlot(0),
                                discriminator=pulse.Discriminator(name='test_discr'),
                                name='acquire')
        inst_data = self.create_instruction(acquire, 0, 7e9, 5, 0.1)

        objs = generators.gen_filled_waveform_stepwise(inst_data)

        # imaginary part is empty and not returned
        self.assertEqual(len(objs), 1)

        # type check
        self.assertEqual(type(objs[0]), drawing_objects.FilledAreaData)

        y1_ref = np.array([1, 1, 1, 1, 1, 1, 1, 1])
        y2_ref = np.array([0, 0, 0, 0, 0, 0, 0, 0])

        # data check
        self.assertEqual(objs[0].channel, pulse.AcquireChannel(0))
        self.assertListEqual(list(objs[0].x), [5, 6, 6, 7, 7, 8, 8, 9])
        np.testing.assert_array_almost_equal(objs[0].y1, y1_ref)
        np.testing.assert_array_almost_equal(objs[0].y2, y2_ref)

        # meta data check
        ref_meta = {'memory slot': 'm0',
                    'register slot': 'N/A',
                    'discriminator': 'test_discr',
                    'kernel': 'N/A',
                    'duration (cycle time)': 4,
                    'duration (sec)': 0.4,
                    't0 (cycle time)': 5,
                    't0 (sec)': 0.5,
                    'phase': 0,
                    'frequency': 7e9,
                    'name': 'acquire',
                    'data': 'real'}

        self.assertDictEqual(objs[0].meta, ref_meta)

        # style check
        ref_style = {'alpha': self.style['formatter.alpha.fill_waveform'],
                     'zorder': self.style['formatter.layer.fill_waveform'],
                     'linewidth': self.style['formatter.line_width.fill_waveform'],
                     'linestyle': self.style['formatter.line_style.fill_waveform'],
                     'color': self.style['formatter.color.fill_waveform_a'][0]}
        self.assertDictEqual(objs[0].styles, ref_style)

    def test_gen_iqx_latex_waveform_name_x90(self):
        """Test gen_iqx_latex_waveform_name with x90 waveform."""
        iqx_pulse = pulse.Waveform(samples=[0, 0, 0, 0], name='X90p_d0_1234567')
        play = pulse.Play(iqx_pulse, pulse.DriveChannel(0))
        inst_data = self.create_instruction(play, 0, 0, 0, 0.1)

        obj = generators.gen_iqx_latex_waveform_name(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.text, 'X90p_d0_1234567')
        self.assertEqual(obj.latex, r'{\rm X}(\frac{\pi}{2})')

        # style check
        ref_style = {'zorder': self.style['formatter.layer.annotate'],
                     'color': self.style['formatter.color.annotate'],
                     'size': self.style['formatter.text_size.annotate'],
                     'va': 'center',
                     'ha': 'center'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_iqx_latex_waveform_name_x180(self):
        """Test gen_iqx_latex_waveform_name with x180 waveform."""
        iqx_pulse = pulse.Waveform(samples=[0, 0, 0, 0], name='Xp_d0_1234567')
        play = pulse.Play(iqx_pulse, pulse.DriveChannel(0))
        inst_data = self.create_instruction(play, 0, 0, 0, 0.1)

        obj = generators.gen_iqx_latex_waveform_name(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.text, 'Xp_d0_1234567')
        self.assertEqual(obj.latex, r'{\rm X}(\pi)')

    def test_gen_iqx_latex_waveform_name_cr(self):
        """Test gen_iqx_latex_waveform_name with CR waveform."""
        iqx_pulse = pulse.Waveform(samples=[0, 0, 0, 0], name='CR90p_u0_1234567')
        play = pulse.Play(iqx_pulse, pulse.ControlChannel(0))
        inst_data = self.create_instruction(play, 0, 0, 0, 0.1)

        obj = generators.gen_iqx_latex_waveform_name(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.ControlChannel(0))
        self.assertEqual(obj.text, 'CR90p_u0_1234567')
        self.assertEqual(obj.latex, r'{\rm CR}(\frac{\pi}{4})')

    def test_gen_iqx_latex_waveform_name_compensation_tone(self):
        """Test gen_iqx_latex_waveform_name with CR compensation waveform."""
        iqx_pulse = pulse.Waveform(samples=[0, 0, 0, 0], name='CR90p_d0_u0_1234567')
        play = pulse.Play(iqx_pulse, pulse.DriveChannel(0))
        inst_data = self.create_instruction(play, 0, 0, 0, 0.1)

        obj = generators.gen_iqx_latex_waveform_name(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.text, 'CR90p_d0_u0_1234567')
        self.assertEqual(obj.latex, r'\overline{\rm CR}(\frac{\pi}{4})')

    def test_gen_baseline(self):
        """Test gen_baseline."""
        channel_info = data_types.ChannelTuple(channel=pulse.DriveChannel(0), scaling=1)

        obj = generators.gen_baseline(channel_info)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.HorizontalLineData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.y0, 0)

        # style check
        ref_style = {'alpha': self.style['formatter.alpha.baseline'],
                     'zorder': self.style['formatter.layer.baseline'],
                     'linewidth': self.style['formatter.line_width.baseline'],
                     'linestyle': self.style['formatter.line_style.baseline'],
                     'color': self.style['formatter.color.baseline']}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_latex_channel_name(self):
        """Test gen_latex_channel_name."""
        channel_info = data_types.ChannelTuple(channel=pulse.DriveChannel(0), scaling=0.5)

        obj = generators.gen_latex_channel_name(channel_info)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.latex, 'D_0')
        self.assertEqual(obj.text, 'D0')

        # style check
        ref_style = {'zorder': self.style['formatter.layer.axis_label'],
                     'color': self.style['formatter.color.axis_label'],
                     'size': self.style['formatter.text_size.axis_label'],
                     'va': 'center',
                     'ha': 'right'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_gen_scaling_info(self):
        """Test gen_scaling_info."""
        channel_info = data_types.ChannelTuple(channel=pulse.DriveChannel(0), scaling=0.5)

        obj = generators.gen_scaling_info(channel_info)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.text, 'x0.5')

        # style check
        ref_style = {'zorder': self.style['formatter.layer.axis_label'],
                     'color': self.style['formatter.color.axis_label'],
                     'size': self.style['formatter.text_size.annotate'],
                     'va': 'center',
                     'ha': 'right'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_latex_vz_label(self):
        """Test gen_latex_vz_label."""
        fcs = [pulse.ShiftPhase(np.pi/2, pulse.DriveChannel(0)),
               pulse.ShiftFrequency(1e6, pulse.DriveChannel(0))]
        inst_data = self.create_instruction(fcs, np.pi/2, 1e6, 5, 0.1)

        obj = generators.gen_latex_vz_label(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.latex, r'{\rm VZ}(-\frac{\pi}{2})')
        self.assertEqual(obj.text, r'VZ(-1.57 rad.)')

        # style check
        ref_style = {'zorder': self.style['formatter.layer.frame_change'],
                     'color': self.style['formatter.color.frame_change'],
                     'size': self.style['formatter.text_size.annotate'],
                     'va': 'center',
                     'ha': 'center'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_latex_frequency_mhz_value(self):
        """Test gen_latex_frequency_mhz_value."""
        fcs = [pulse.ShiftPhase(np.pi/2, pulse.DriveChannel(0)),
               pulse.ShiftFrequency(1e6, pulse.DriveChannel(0))]
        inst_data = self.create_instruction(fcs, np.pi/2, 1e6, 5, 0.1)

        obj = generators.gen_latex_frequency_mhz_value(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.latex, r'\Delta f = 1.00 ~{\rm MHz}')
        self.assertEqual(obj.text, u'\u0394' + 'f=1.00 MHz')

        # style check
        ref_style = {'zorder': self.style['formatter.layer.frame_change'],
                     'color': self.style['formatter.color.frame_change'],
                     'size': self.style['formatter.text_size.annotate'],
                     'va': 'center',
                     'ha': 'center'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_raw_frame_operand_values(self):
        """Test gen_raw_frame_operand_values."""
        fcs = [pulse.ShiftPhase(np.pi/2, pulse.DriveChannel(0)),
               pulse.ShiftFrequency(1e6, pulse.DriveChannel(0))]
        inst_data = self.create_instruction(fcs, np.pi/2, 1e6, 5, 0.1)

        obj = generators.gen_raw_frame_operand_values(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.text, r'(1.57, 1.0e+06)')

        # style check
        ref_style = {'zorder': self.style['formatter.layer.frame_change'],
                     'color': self.style['formatter.color.frame_change'],
                     'size': self.style['formatter.text_size.annotate'],
                     'va': 'center',
                     'ha': 'center'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_frame_symbol(self):
        """Test gen_frame_symbol."""
        fcs = [pulse.ShiftPhase(np.pi/2, pulse.DriveChannel(0)),
               pulse.ShiftFrequency(1e6, pulse.DriveChannel(0))]
        inst_data = self.create_instruction(fcs, np.pi/2, 1e6, 5, 0.1)

        obj = generators.gen_frame_symbol(inst_data)[0]

        # type check
        self.assertEqual(type(obj), drawing_objects.TextData)

        # data check
        self.assertEqual(obj.channel, pulse.DriveChannel(0))
        self.assertEqual(obj.latex, self.style['formatter.latex_symbol.frame_change'])
        self.assertEqual(obj.text, self.style['formatter.unicode_symbol.frame_change'])

        # metadata check
        ref_meta = {
            'total phase change': np.pi/2,
            'total frequency change': 1e6,
            'program': ['ShiftPhase(1.57 rad.)', 'ShiftFrequency(1.00e+06 Hz)'],
            't0 (cycle time)': 5,
            't0 (sec)': 0.5
        }
        self.assertDictEqual(obj.meta, ref_meta)

        # style check
        ref_style = {'zorder': self.style['formatter.layer.frame_change'],
                     'color': self.style['formatter.color.frame_change'],
                     'size': self.style['formatter.text_size.frame_change'],
                     'va': 'center',
                     'ha': 'center'}
        self.assertDictEqual(obj.styles, ref_style)

    def test_gen_snapshot_symbol(self):
        """Test gen_snapshot_symbol."""
        snapshot = pulse.instructions.Snapshot(label='test_snapshot', snapshot_type='statevector')
        inst_data = data_types.NonPulseTuple(5, 0.1, snapshot)
        symbol, label = generators.gen_snapshot_symbol(inst_data)

        # type check
        self.assertEqual(type(symbol), drawing_objects.TextData)
        self.assertEqual(type(label), drawing_objects.TextData)

        # data check
        self.assertEqual(symbol.channel, pulse.channels.SnapshotChannel())
        self.assertEqual(symbol.text, self.style['formatter.unicode_symbol.snapshot'])
        self.assertEqual(symbol.latex, self.style['formatter.latex_symbol.snapshot'])

        self.assertEqual(label.channel, pulse.channels.SnapshotChannel())
        self.assertEqual(label.text, 'test_snapshot')

        # metadata check
        ref_meta = {'snapshot type': 'statevector',
                    't0 (cycle time)': 5,
                    't0 (sec)': 0.5}
        self.assertDictEqual(symbol.meta, ref_meta)

        # style check
        ref_style = {'zorder': self.style['formatter.layer.snapshot'],
                     'color': self.style['formatter.color.snapshot'],
                     'size': self.style['formatter.text_size.snapshot'],
                     'va': 'bottom',
                     'ha': 'center'}
        self.assertDictEqual(symbol.styles, ref_style)

        ref_style = {'zorder': self.style['formatter.layer.snapshot'],
                     'color': self.style['formatter.color.snapshot'],
                     'size': self.style['formatter.text_size.annotate'],
                     'va': 'bottom',
                     'ha': 'center'}
        self.assertDictEqual(label.styles, ref_style)

    def test_gen_barrier(self):
        """Test gen_barrier."""
        barrier = pulse.instructions.RelativeBarrier(pulse.DriveChannel(0),
                                                     pulse.ControlChannel(0))
        inst_data = data_types.NonPulseTuple(5, 0.1, barrier)
        lines = generators.gen_barrier(inst_data)

        self.assertEqual(len(lines), 2)

        # type check
        self.assertEqual(type(lines[0]), drawing_objects.VerticalLineData)
        self.assertEqual(type(lines[1]), drawing_objects.VerticalLineData)

        # data check
        self.assertEqual(lines[0].channel, pulse.channels.DriveChannel(0))
        self.assertEqual(lines[1].channel, pulse.channels.ControlChannel(0))
        self.assertEqual(lines[0].x0, 5)

        # style check
        ref_style = {'alpha': self.style['formatter.alpha.barrier'],
                     'zorder': self.style['formatter.layer.barrier'],
                     'linewidth': self.style['formatter.line_width.barrier'],
                     'linestyle': self.style['formatter.line_style.barrier'],
                     'color': self.style['formatter.color.barrier']}
        self.assertDictEqual(lines[0].styles, ref_style)


class TestLayout(QiskitTestCase):
    """Tests for layout generation functions."""

    def setUp(self) -> None:
        self.channels = [pulse.DriveChannel(0),
                         pulse.DriveChannel(1),
                         pulse.DriveChannel(2),
                         pulse.MeasureChannel(1),
                         pulse.MeasureChannel(2),
                         pulse.AcquireChannel(1),
                         pulse.AcquireChannel(2),
                         pulse.ControlChannel(0),
                         pulse.ControlChannel(2),
                         pulse.ControlChannel(5)]

    def test_channel_type_grouped_sort(self):
        """Test channel_type_grouped_sort."""
        channels = layouts.channel_type_grouped_sort(self.channels)

        ref_channels = [pulse.DriveChannel(0),
                        pulse.DriveChannel(1),
                        pulse.DriveChannel(2),
                        pulse.ControlChannel(0),
                        pulse.ControlChannel(2),
                        pulse.ControlChannel(5),
                        pulse.MeasureChannel(1),
                        pulse.MeasureChannel(2),
                        pulse.AcquireChannel(1),
                        pulse.AcquireChannel(2)]

        self.assertListEqual(channels, ref_channels)

    def test_channel_index_sort(self):
        """Test channel_index_sort."""
        channels = layouts.channel_index_sort(self.channels)

        ref_channels = [pulse.DriveChannel(0),
                        pulse.ControlChannel(0),
                        pulse.DriveChannel(1),
                        pulse.MeasureChannel(1),
                        pulse.AcquireChannel(1),
                        pulse.DriveChannel(2),
                        pulse.ControlChannel(2),
                        pulse.MeasureChannel(2),
                        pulse.AcquireChannel(2),
                        pulse.ControlChannel(5)]

        self.assertListEqual(channels, ref_channels)

    def test_channel_index_sort_grouped_control(self):
        """Test channel_index_sort_grouped_control."""
        channels = layouts.channel_index_sort_grouped_control(self.channels)

        ref_channels = [pulse.DriveChannel(0),
                        pulse.DriveChannel(1),
                        pulse.MeasureChannel(1),
                        pulse.AcquireChannel(1),
                        pulse.DriveChannel(2),
                        pulse.MeasureChannel(2),
                        pulse.AcquireChannel(2),
                        pulse.ControlChannel(0),
                        pulse.ControlChannel(2),
                        pulse.ControlChannel(5)]

        self.assertListEqual(channels, ref_channels)


class TestDrawDataContainer(QiskitTestCase):
    """Tests for draw data container."""

    def setUp(self) -> None:
        # draw only waveform, fc symbol, channel name, scaling, baseline, snapshot and barrier
        default_style = stylesheet.init_style_from_file()
        callbacks_for_test = {
            'generator': {
                'waveform': [generators.gen_filled_waveform_stepwise],
                'frame': [generators.gen_frame_symbol],
                'channel': [generators.gen_latex_channel_name,
                            generators.gen_scaling_info,
                            generators.gen_baseline],
                'snapshot': [generators.gen_snapshot_symbol],
                'barrier': [generators.gen_barrier]
            },
            'layout': {
                'channel': layouts.channel_index_sort_grouped_control
            }}
        default_style.style = callbacks_for_test
        PULSE_STYLE.style = default_style.style

        gaussian = pulse.Gaussian(40, 0.3, 10)
        square = pulse.Constant(100, 0.2)

        self.sched = pulse.Schedule()
        self.sched = self.sched.insert(0, pulse.Play(pulse=gaussian,
                                                     channel=pulse.DriveChannel(0)))
        self.sched = self.sched.insert(0, pulse.ShiftPhase(phase=np.pi/2,
                                                           channel=pulse.DriveChannel(0)))
        self.sched = self.sched.insert(50, pulse.Play(pulse=square,
                                                      channel=pulse.MeasureChannel(0)))
        self.sched = self.sched.insert(50, pulse.Acquire(duration=100,
                                                         channel=pulse.AcquireChannel(0),
                                                         mem_slot=pulse.MemorySlot(0)))

    def test_loading_backend(self):
        """Test loading backend."""
        from qiskit.test.mock import FakeAthens

        config = FakeAthens().configuration()
        defaults = FakeAthens().defaults()

        ddc = core.DrawDataContainer(backend=FakeAthens())

        # check dt
        self.assertEqual(ddc.dt, config.dt)

        # check drive los
        self.assertEqual(ddc.d_los[0], defaults.qubit_freq_est[0])

        # check measure los
        self.assertEqual(ddc.m_los[0], defaults.meas_freq_est[0])

        # check control los
        self.assertEqual(ddc.c_los[0], defaults.qubit_freq_est[1])

    def test_simple_sched_loading(self):
        """Test data generation with simple schedule."""

        ddc = core.DrawDataContainer()
        ddc.load_program(self.sched)

        # 4 waveform shapes (re, im of gaussian, re of square, re of acquire)
        # 3 channel names
        # 1 fc symbol
        # 3 baselines
        self.assertEqual(len(ddc.drawings), 11)

    def test_simple_sched_reloading(self):
        """Test reloading of the same schedule."""
        ddc = core.DrawDataContainer()
        ddc.load_program(self.sched)

        # the same data should be overwritten
        list_drawing1 = ddc.drawings.copy()
        list_drawing2 = ddc.drawings.copy()

        self.assertListEqual(list_drawing1, list_drawing2)

    def test_update_channels(self):
        """Test update channels."""
        ddc = core.DrawDataContainer()
        ddc.load_program(self.sched)

        ddc.update_channel_property()

        # 2 scale factors are added for d channel and m channel
        self.assertEqual(len(ddc.drawings), 13)

        d_scale = 1 / 0.3
        m_scale = 1 / 0.2
        a_scale = 1

        top_margin = PULSE_STYLE.style['formatter.margin.top']
        interval = PULSE_STYLE.style['formatter.margin.between_channel']
        min_h = np.abs(PULSE_STYLE.style['formatter.channel_scaling.min_height'])

        d_offset = - (top_margin + 1)
        m_offset = - (top_margin + 1 + min_h + interval + 1)
        a_offset = - (top_margin + 1 + min_h + interval + 1 + min_h + interval + 1)

        # check if auto scale factor is correct
        for drawing in ddc.drawings:
            if drawing.channel == pulse.DriveChannel(0):
                self.assertAlmostEqual(drawing.scale, d_scale, places=1)
                self.assertAlmostEqual(drawing.offset, d_offset, places=1)
            elif drawing.channel == pulse.MeasureChannel(0):
                self.assertAlmostEqual(drawing.scale, m_scale, places=1)
                self.assertAlmostEqual(drawing.offset, m_offset, places=1)
            elif drawing.channel == pulse.AcquireChannel(0):
                self.assertAlmostEqual(drawing.scale, a_scale, places=1)
                self.assertAlmostEqual(drawing.offset, a_offset, places=1)

    def test_update_channels_only_drive_channel(self):
        """Test update channels with filtered channels."""
        ddc = core.DrawDataContainer()
        ddc.load_program(self.sched)

        # update
        ddc.update_channel_property(visible_channels=[pulse.DriveChannel(0)])

        # 1 scale factor is added for d channel
        self.assertEqual(len(ddc.drawings), 12)

        # check if visible is updated
        for drawing in ddc.drawings:
            if drawing.channel == pulse.DriveChannel(0):
                self.assertTrue(drawing.visible)
            else:
                self.assertFalse(drawing.visible)

    def test_snapshot(self):
        """Test snapshot instructions."""
        ddc = core.DrawDataContainer()

        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.Snapshot(label='test'))

        ddc.load_program(sched)

        # only snapshot symbol and label text
        self.assertEqual(len(ddc.drawings), 2)

    def test_relative_barrier(self):
        """Test relative barrier instructions."""
        ddc = core.DrawDataContainer()

        sched = pulse.Schedule()
        sched = sched.insert(0, pulse.instructions.RelativeBarrier(pulse.DriveChannel(0)))

        ddc.load_program(sched)

        # barrier line, baseline, channel name
        self.assertEqual(len(ddc.drawings), 3)
