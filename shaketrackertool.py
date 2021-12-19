#!/usr/bin/env python3

import struct
from collections import OrderedDict, namedtuple
from io import BytesIO
from pprint import pprint as pp
import os
import sys

class FileWriter:
    def __init__(self, fobj):
        self.fobj = fobj

    def store_byte(self, b):
        self.fobj.write(struct.pack('B', b))

    def store_pascal_string(self, s):
        return self.store_pascal_bytes(s.encode('ascii'))

    def store_pascal_bytes(self, b):
        b = b[:255]
        self.fobj.write(struct.pack('B', len(b)) + b)

class FileReader:
    def __init__(self, fobj):
        self.fobj = fobj

    def read_byte(self):
        b = self.fobj.read(1)
        if not b:
            return None

        return struct.unpack('B', b)[0]

    def read_word_le(self):
        b = self.fobj.read(2)
        if len(b) < 2:
            return None

        return struct.unpack('<H', b)[0]

    def read_dword_le(self):
        b = self.fobj.read(4)
        if len(b) < 4:
            return None

        return struct.unpack('<I', b)[0]

    def read_word_be(self):
        b = self.fobj.read(2)
        if len(b) < 2:
            return None

        return struct.unpack('>H', b)[0]

    def read_pascal_string(self):
        return self.read_pascal_bytes().decode('ascii')

    def read_pascal_bytes(self):
        length = self.read_byte()
        if length is None:
            return None

        return self.fobj.read(length)

    def read_c_string(self, length):
        return self.read_c_bytes(length).decode('ascii')

    def read_c_bytes(self, length):
        b = self.fobj.read(length)
        if len(b) < length:
            return None

        return b.split(b'\x00')[0] # support null-terminated and not-null-terminated input


class Section:
    def __init__(self, properties, section_name):
        self._properties = properties
        self._section_name = section_name

    def add_property(self, property_name, value):
        self._properties.add_property(self._section_name, property_name, value)

class Properties:
    CHUNK_SECTION = 0
    CHUNK_VARIABLE = 1

    @classmethod
    def load_from_fobj(cls, fobj, header_check=None):
        props = Properties(header_check)
        reader = FileReader(fobj)

        if header_check is not None:
            header_tag = reader.read_pascal_string()
            if header_tag != header_check:
                raise Exception(f'Expected to read {header_check} but read {header_tag} instead')

        section = None

        while True:
            chunk = reader.read_byte()

            if chunk is None:
                # done/eof
                break

            elif chunk == Properties.CHUNK_SECTION:
                section = props.add_section(reader.read_pascal_string())

            elif chunk == Properties.CHUNK_VARIABLE:
                section.add_property(reader.read_pascal_string(), reader.read_pascal_string())

        return props

    def __init__(self, header_check=None):
        self.header_check = header_check

        self._sections = OrderedDict()

    def sort(self):
        for k in sorted(self._sections.keys()):
            self._sections.move_to_end(k)

            for sub_k in sorted(self._sections[k].keys()):
                self._sections[k].move_to_end(sub_k)

    def add_section(self, section_name):
        self._sections.setdefault(section_name, OrderedDict())
        return Section(self, section_name)

    def add_property(self, section_name, property_name, value):
        self._sections.setdefault(section_name, OrderedDict()).setdefault(property_name, str(value))

    def update(self, other_properties):
        self._sections.update(other_properties._sections)

    def save_to_fobj(self, fobj):
        writer = FileWriter(fobj)

        if self.header_check is not None:
            writer.store_pascal_string(self.header_check)

        for section_name, properties in self._sections.items():
            writer.store_byte(Properties.CHUNK_SECTION)
            writer.store_pascal_string(section_name)

            for property_name, property_value in properties.items():
                writer.store_byte(Properties.CHUNK_VARIABLE)

                writer.store_pascal_string(property_name)
                writer.store_pascal_string(property_value)


_standard_device_properties_raw = b'\x00\rDEVICE 0 INFO\x01\x10bank_0_patch_122\tSea Shore\x01\x10bank_0_patch_117\x0bMelodic Tom\x01\x0fbank_0_patch_96\x0bFX 1 (Rain)\x01\x10bank_0_patch_123\nBird Tweet\x01\x10bank_0_patch_118\nSynth Drum\x01\x0fbank_0_patch_97\x11FX 2 (Soundtrack)\x01\x10bank_0_patch_124\x0eTelephone Ring\x01\x10bank_0_patch_119\x0eReverse Cymbal\x01\x0fbank_0_patch_98\x0eFX 3 (Crystal)\x01\x10bank_0_patch_125\nHelicopter\x01\x0fbank_0_patch_99\x11FX 4 (Atmosphere)\x01\x10bank_0_patch_126\x08Applause\x01\x10bank_0_patch_127\x08Gun Shot\x01\x14bank_0_select_string\x00\x01\nbank_0_MSB\x010\x01\x0ebank_0_patch_0\x14Acoustic Grand Piano\x01\x0ebank_0_patch_1\x15Brigth Acoustic Piano\x01\x0ebank_0_patch_2\x0eElectric Grand\x01\x04name\x0bNull Output\x01\x0ebank_0_patch_3\x10Honky Tonk Piano\x01\x0ebank_0_patch_4\x10Electric Piano 1\x01\x0ebank_0_patch_5\x10Electric Piano 2\x01\x0ebank_0_patch_6\x0bHarpsichord\x01\x0ebank_0_patch_7\x08Clavinet\x01\x0ebank_0_patch_8\x07Celesta\x01\x0ebank_0_patch_9\x0cGlockenspiel\x01\x0bbank_0_name\x0cGeneral Midi\x01\x0ehardware_index\x010\x01\x0fbank_0_patch_10\tMusic Box\x01\x0fbank_0_patch_11\nVibraphone\x01\x0fbank_0_patch_12\x07Marimba\x01\x0fbank_0_patch_13\tXylophone\x01\x0fbank_0_patch_14\rTubular Bells\x01\x0fbank_0_patch_20\nReed Organ\x01\x0fbank_0_patch_15\x08Dulcimer\x01\x0fbank_0_patch_21\tAccordion\x01\x0fbank_0_patch_16\rDrawbar Organ\x01\x0fbank_0_patch_22\tHarmonica\x01\x0fbank_0_patch_17\x0fPercusive Organ\x01\x05banks\x011\x01\x0fbank_0_patch_23\x0fTango Accordion\x01\x0fbank_0_patch_18\nRock Organ\x01\x0fbank_0_patch_24\x13Nylon String Guitar\x01\x0fbank_0_patch_19\x0cChurch Organ\x01\x0fbank_0_patch_30\x11Distortion Guitar\x01\x0fbank_0_patch_25\x13Steel String Guitar\x01\x0fbank_0_patch_31\x10Guitar Harmonics\x01\x0fbank_0_patch_26\x14Electric Jazz Guitar\x01\x0fbank_0_patch_32\rAcoustic Bass\x01\x0fbank_0_patch_27\x15Electric Clean Guitar\x01\x0fbank_0_patch_33\x14Electric Bass(pluck)\x01\x0fbank_0_patch_28\x15Electric Muted Guitar\x01\x0fbank_0_patch_34\x15Electric Bass(finger)\x01\x0fbank_0_patch_29\x11Overdriven Guitar\x01\x0fbank_0_patch_40\x06Violin\x01\x0fbank_0_patch_35\rFretless Bass\x01\x0fbank_0_patch_41\x05Viola\x01\x0fbank_0_patch_36\x0bSlap Bass 1\x01\x0fbank_0_patch_42\x05Cello\x01\x0fbank_0_patch_37\x0bSlap Bass 2\x01\x0fbank_0_patch_43\x0bCounterBass\x01\x0fbank_0_patch_38\x0cSynth Bass 1\x01\x0fbank_0_patch_44\x0fTremolo Strings\x01\x0fbank_0_patch_39\x0cSynth Bass 2\x01\rbank_0_method\x010\x01\x0fbank_0_patch_50\x0fSynth Strings 1\x01\x0fbank_0_patch_45\x11Pizzicato Strings\x01\x0fbank_0_patch_51\x0fSynth Strings 2\x01\x0fbank_0_patch_46\x0fOrchestral Harp\x01\x0fbank_0_patch_52\nChoir Aahs\x01\x0fbank_0_patch_47\x07Timpani\x01\x0fbank_0_patch_53\nVoice Oohs\x01\x0fbank_0_patch_48\x11String Ensemble 1\x01\x0fbank_0_patch_54\x0bSynth Voice\x01\x0fbank_0_patch_49\x11String Ensemble 2\x01\x0fbank_0_patch_60\x0bFrench Horn\x01\x0fbank_0_patch_55\rOrchestra Hit\x01\x0fbank_0_patch_61\rBrass Section\x01\x0fbank_0_patch_56\x07Trumpet\x01\x0fbank_0_patch_62\x0cSynthBrass 1\x01\x0fbank_0_patch_57\x08Trombone\x01\x0fbank_0_patch_63\x0cSynthBrass 2\x01\x0fbank_0_patch_58\x04Tuba\x01\x0fbank_0_patch_64\x0bSoprano Sax\x01\x0fbank_0_patch_59\rMuted Trumpet\x01\x0fbank_0_patch_70\x07Bassoon\x01\x0fbank_0_patch_65\tTenor Sax\x01\x0fbank_0_patch_71\x08Clarinet\x01\x0fbank_0_patch_66\x08Alto Sax\x01\x0fbank_0_patch_72\x07Piccolo\x01\x0fbank_0_patch_67\x0cBaritone Sax\x01\x0fbank_0_patch_73\x05Flute\x01\x0fbank_0_patch_68\x04Oboe\x01\x10bank_0_patch_100\x11FX 5 (Brightness)\x01\x0fbank_0_patch_74\x08Recorder\x01\x0fbank_0_patch_69\x0cEnglish Horn\x01\x10bank_0_patch_101\x0eFX 6 (Goblins)\x01\x0fbank_0_patch_80\x0fLead 1 (Square)\x01\x0fbank_0_patch_75\tPan Flute\x01\x10bank_0_patch_102\rFX 7 (echoes)\x01\x0fbank_0_patch_81\x11Lead 2 (SawTooth)\x01\x0fbank_0_patch_76\x0cBlown Bottle\x01\x10bank_0_patch_103\rFX 8 (sci-fi)\x01\x0fbank_0_patch_82\x11Lead 3 (Calliope)\x01\x0fbank_0_patch_77\nSkakukachi\x01\x10bank_0_patch_104\x05Sitar\x01\x0fbank_0_patch_83\x0eLead 4 (Chiff)\x01\x0fbank_0_patch_78\x07Whistle\x01\x10bank_0_patch_110\x06Fiddle\x01\x10bank_0_patch_105\x05Banjo\x01\x0fbank_0_patch_84\x10Lead 5 (Charang)\x01\x0fbank_0_patch_79\x07Ocarina\x01\x10bank_0_patch_111\x06Shanai\x01\x10bank_0_patch_106\x08Shamisen\x01\x0fbank_0_patch_90\x11Pad 3 (PolySynth)\x01\x0fbank_0_patch_85\x0eLead 6 (Voice)\x01\x10bank_0_patch_112\x0bTinkle Bell\x01\x10bank_0_patch_107\x04Koto\x01\x0fbank_0_patch_91\rPad 4 (Choir)\x01\x0fbank_0_patch_86\x0fLead 7 (Fifths)\x01\x10bank_0_patch_113\x05Agogo\x01\x10bank_0_patch_108\x07Kalimba\x01\x0fbank_0_patch_92\rPad 5 (Bowed)\x01\x0fbank_0_patch_87\x12Lead 8 (Bass+Lead)\x01\x10bank_0_patch_114\x0bSteel Drums\x01\x10bank_0_patch_109\x07BagPipe\x01\x0fbank_0_patch_93\x10Pad 6 (Metallic)\x01\x0fbank_0_patch_88\x0fPad 1 (New Age)\x01\x10bank_0_patch_120\x11Guitar Fret Noise\x01\x10bank_0_patch_115\nWood Block\x01\x0fbank_0_patch_94\rPad 7 (Hallo)\x01\x0fbank_0_patch_89\x0cPad 2 (Warm)\x01\x10bank_0_patch_121\x0cBreath Noise\x01\x10bank_0_patch_116\nTaiko Drum\x01\x0fbank_0_patch_95\rPad 8 (Sweep)\x01\nbank_0_LSB\x010'
_standard_device_properties = Properties.load_from_fobj(BytesIO(_standard_device_properties_raw))

PatternMetrics = namedtuple('PatternMetrics', ('length', 'highlight_major', 'highlight_minor'))

Instrument = namedtuple('Instrument', ('name', 'track_width', 'device', 'bank', 'patch', 'channel', 'pitch_bend_sensitivity', 'default_volume', 'global_volume'))

CLEAR = '<CLEAR>'
OFF = '<OFF>'

class Row(namedtuple('Row', ('note', 'vol', 'command', 'parameter', 'controller_set', 'controller_value'))):
    def _is_empty(self):
        return self.note == CLEAR and self.vol == CLEAR and self.command == CLEAR and self.parameter == 0 and self.controller_set == CLEAR and self.controller_value == 0

def decode_pattern_data(reader, num_columns, num_rows):
    pattern_data_length = reader.read_dword_le()
    bytes_read = 0

    total_rows_added = 0
    total_rows_expected = num_rows * num_columns

    rows_added = 0
    all_rows = []

    last_row = None

    while rows_added < total_rows_expected:
        repeat_count = 1

        frame_header = reader.read_byte()
        bytes_read += 1

        if frame_header & 0x80:
            note = reader.read_byte()
            if note > 128:
                note = OFF
            elif note == 0:
                note = CLEAR
            else:
                note -= 1
            bytes_read += 1
        else:
            note = last_row.note

        if frame_header & 0x40:
            vol = reader.read_byte()
            if vol > 64:
                vol = CLEAR
            bytes_read += 1
        else:
            vol = last_row.vol

        if frame_header & 0x20:
            command = reader.read_byte()
            if command == 0:
                command = CLEAR
            bytes_read += 1
        else:
            command = last_row.command

        if frame_header & 0x10:
            parameter = reader.read_byte()
            bytes_read += 1
        else:
            parameter = last_row.parameter

        if frame_header & 0x08:
            controller_set = reader.read_byte()
            if controller_set == 0:
                controller_set = CLEAR
            else:
                controller_set -= 1
            bytes_read += 1
        else:
            controller_set = last_row.controller_set

        if frame_header & 0x04:
            controller_value = reader.read_byte()
            bytes_read += 1
        else:
            controller_value = last_row.controller_value

        if frame_header & 0x02:
            repeat_count = reader.read_word_be() + 1
            bytes_read += 2

        row = Row(note, vol, command, parameter, controller_set, controller_value)
        all_rows.extend([row] * repeat_count)
        rows_added += repeat_count

        last_row = row

    if bytes_read != pattern_data_length:
        raise Exception(f'Expected {pattern_data_length} bytes of pattern data, actually read {bytes_read}')

    columns = []

    for column_idx in range(num_columns):
        columns.append(all_rows[num_rows * column_idx:num_rows * (column_idx + 1)])

    return columns


class Song:
    @classmethod
    def load_from_sht2(self, fobj):
        reader = FileReader(fobj)

        if reader.read_c_string(10) != 'SHKT-SONG':
            raise Exception('Missing SHKT-SONG signature')

        song = Song()

        # import pdb; pdb.set_trace()

        version = reader.read_word_le() # guessed meaning

        song.author = reader.read_pascal_string() # guessed meaning
        song.name = reader.read_pascal_string() # guessed meaning

        song.tempo = reader.read_byte()
        song.speed = reader.read_byte()

        #
        # - pattern metrics -
        #

        pattern_count = reader.read_word_le()

        pattern_metrics = []

        for pattern_idx in range(pattern_count):

            length = reader.read_word_le()
            hlminor = reader.read_word_le()
            hlmajor = reader.read_word_le()

            pattern_metrics.append(PatternMetrics(length, hlmajor, hlminor))

        song.pattern_metrics = pattern_metrics

        #
        # - orders -
        #

        order_count = reader.read_word_le()

        order_list = []

        for order_idx in range(order_count):
            pattern_idx = reader.read_word_le() - 5 # 4 => no order, 5 => pattern 0, 6 => pattern 1, ... // never saw values < 3
            if pattern_idx < 0:
                order_list.append(None)
            else:
                order_list.append(pattern_idx)

        song.order_list = order_list

        #
        # - instruments (and pattern data) -
        #

        instrument_count = reader.read_word_le()
        instruments = []
        rows = []

        for instrument_idx in range(instrument_count):
            name = reader.read_pascal_string()
            device = reader.read_byte()
            bank = reader.read_byte()
            patch = reader.read_byte()
            channel = reader.read_byte()
            pbs = reader.read_byte()
            reader.read_byte() # ?
            default_volume = reader.read_byte()
            global_volume = reader.read_byte()
            reader.read_byte() # ?
            reader.read_byte() # ?
            reader.read_byte() # ?

            reader.fobj.read(128) # initial values? don't care
            reader.fobj.read(130) # don't care

            width = reader.read_byte()

            instruments.append(Instrument(name, width, device, bank, patch, channel, pbs, default_volume, global_volume))

            #
            # load pattern data
            #

            instrument_rows = []

            for pattern_idx, pattern_metrics in enumerate(song.pattern_metrics):
                instrument_rows.append(decode_pattern_data(reader, width, pattern_metrics.length))

            rows.append(instrument_rows)

        song.instruments = instruments
        song.rows = rows

        return song


    def __init__(self):
        self.name = ''
        self.author = ''

        self.speed = 1 # typ 4
        self.tempo = 1 # typ 150

        self.pattern_metrics = []
        self.order_list = []
        self.instruments = []
        self.rows = [] # rows[instrument_idx][pattern_idx][column_idx][row_idx]


    def save_to_file(self, filename):
        props = Properties("ShakeTracker Module")

        section = props.add_section('VERSION')
        section.add_property('version', '0.3.99') # my files are tagged 0.3.9, but shaketracker 0.4.x ignores this property on load anyway

        section = props.add_section('INFO')
        section.add_property('name', self.name)
        section.add_property('author', self.author)

        section = props.add_section('SPEED')
        section.add_property('rpq', self.speed)
        section.add_property('tempo', self.tempo)

        #
        # TRACKS
        #

        section = props.add_section('TRACKS')
        section.add_property('amount', len(self.instruments))

        for instrument_idx, instrument in enumerate(self.instruments):
            section = props.add_section(f'TRACK {instrument_idx} INFO')

            section.add_property('default_volume', instrument.default_volume)
            section.add_property('global_volume', instrument.global_volume)
            section.add_property('midi_bank', instrument.bank)
            section.add_property('midi_channel', instrument.channel)
            section.add_property('midi_device', instrument.device)
            section.add_property('midi_patch', instrument.patch)
            section.add_property('midi_pitch_bend_sensitivity', instrument.pitch_bend_sensitivity)
            section.add_property('name', instrument.name)
            section.add_property('width', instrument.track_width)

            # constants copied from a new file
            section.add_property('PNVA_controller', 11)
            section.add_property('PNVA_type', 3)
            section.add_property('initial_values', 5)
            section.add_property('initial_value_0_number', 7)
            section.add_property('initial_value_0_type', 0)
            section.add_property('initial_value_0_value', 127)
            section.add_property('initial_value_1_number', 10)
            section.add_property('initial_value_1_type', 0)
            section.add_property('initial_value_1_value', 64)
            section.add_property('initial_value_2_number', 91)
            section.add_property('initial_value_2_type', 0)
            section.add_property('initial_value_2_value', 24)
            section.add_property('initial_value_3_number', 94)
            section.add_property('initial_value_3_type', 0)
            section.add_property('initial_value_3_value', 10)
            section.add_property('initial_value_4_number', 11)
            section.add_property('initial_value_4_type', 0)
            section.add_property('initial_value_4_value', 127)
            section.add_property('mute', 0)


        #
        # ORDER LIST
        #

        section = props.add_section('ORDER LIST')

        # TODO: When we include all 500 orders in the output, shaketracker
        # 0.4.6 sets song->pattern_data[i].rowlength to -1 for all patterns.
        # (Why does this happen??? It seems to be caused by unrelated code
        # that resizes the order list. Memory corruption maybe?)
        #
        # That causes a crash if the first pattern's length is less than the
        # number of patterns, which happens when the pattern length is 48
        # (a somewhat uncommon value, typical is 64) and there are 50 patterns
        # (typical number) because 48 + (-1 * 50) < 0, and then an STL resize()
        # call fails.
        #
        # So we limit orders to 200, which is really enough, and that's the
        # normal maximum for shaketracker 0.4.6 anyway.
        order_list = self.order_list[:200]

        section.add_property('max_order', len(order_list))
        for order_idx, order in enumerate(order_list):
            if order is None:
                order_value = -1
            else:
                order_value = order
            section.add_property(f'order_{order_idx}', order_value)

        #
        # PATTERNS
        #

        section = props.add_section('PATTERNS')
        section.add_property('amount', len(self.pattern_metrics))

        for pattern_idx, pattern_metrics in enumerate(self.pattern_metrics):
            section = props.add_section(f'PATTERN {pattern_idx} DATA')
            section.add_property('length', pattern_metrics.length)
            section.add_property('hl_major', pattern_metrics.highlight_major)
            section.add_property('hl_minor', pattern_metrics.highlight_minor)

            pattern_column_offset = 0
            pattern_note_count = 0

            for instrument_idx, instrument_patterns in enumerate(self.rows):
                instrument_pattern_columns = instrument_patterns[pattern_idx]

                for column_idx, rows in enumerate(instrument_pattern_columns):
                    for row_idx, row in enumerate(rows):
                        if row._is_empty():
                            # skip empty notes
                            continue

                        note = row.note
                        if note == OFF:
                            note = 254
                        elif note == CLEAR:
                            note = 255

                        vol = row.vol
                        if vol == CLEAR:
                            vol = 65

                        command = row.command
                        if command == CLEAR:
                            command = 255

                        parameter = row.parameter

                        controller_set = row.controller_set
                        if controller_set == CLEAR:
                            controller_set = 255

                        controller_value = row.controller_value

                        row_bytes = (
                            sht4_byte_to_bytestring(note) +
                            sht4_byte_to_bytestring(vol) +
                            sht4_byte_to_bytestring(command) +
                            sht4_byte_to_bytestring(parameter) +
                            sht4_byte_to_bytestring(controller_set) +
                            sht4_byte_to_bytestring(controller_value) +
                            sht4_byte_to_bytestring(pattern_column_offset) +
                            sht4_byte_to_bytestring(row_idx)
                        )

                        section.add_property(f'note_{pattern_note_count}', row_bytes.decode('ascii'))

                        pattern_note_count += 1

                    pattern_column_offset += 1

            section.add_property('note_count', pattern_note_count)




        #
        # DEVICES
        #

        section = props.add_section('DEVICES')
        section.add_property('amount', 1)

        props.update(_standard_device_properties)

        #
        # DONE
        #

        with open(filename, 'wb') as fobj:
            props.save_to_fobj(fobj)

# implements get_str_from_char
def sht4_byte_to_bytestring(b):
    return bytes([ord(b'A') + ((b >> 4) & 0xf),
                  ord(b'A') + (b & 0xf)])

def sht4_bytestring_to_byte(bs):
    return ((ord(bs[0]) - ord(b'A')) << 4) | (ord(bs[1]) - ord(b'A'))

def print_interesting_sht4_bytestrings():
    print('0 = ' + sht4_byte_to_bytestring(0))
    print('64 = ' + sht4_byte_to_bytestring(64))
    print('65 = ' + sht4_byte_to_bytestring(65))
    print('CUT(253) = ' + sht4_byte_to_bytestring(253))
    print('OFF(254) = ' + sht4_byte_to_bytestring(254))
    print('CLEAR(255) = ' + sht4_byte_to_bytestring(255))

def convert2to4(input_filename, output_filename, overwrite_ok=False):
    if os.path.exists(output_filename) and not overwrite_ok:
        return False

    with open(input_filename, 'rb') as fobj:
        song = Song.load_from_sht2(fobj)
    song.save_to_file(output_filename)

    return True

def show4(input_filename):
    with open(input_filename, 'rb') as fobj:
        props = Properties.load_from_fobj(fobj)

    props.sort()

    pp(props._sections)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='command', required=True)

    convert_parser = subparsers.add_parser('convert', help='Convert Shaketracker 0.2.x (or 0.3.x?) file to 0.4.x format')
    convert_parser.add_argument('input_filename', help='Shaketracker 0.2.x file to be converted')
    convert_parser.add_argument('output_filename', help='Filename for Shaketracker 0.4.x output')
    convert_parser.add_argument('--overwrite', help='Overwrite output file if it already exists', action='store_true', default=False)

    show4_parser = subparsers.add_parser('show', help='Read a Shaketracker 0.4.x file and display its contents')
    show4_parser.add_argument('input_filename', help='Shaketracker 0.4.x file to read')

    args = parser.parse_args()

    if args.command == 'convert':
        if not convert2to4(args.input_filename, args.output_filename, args.overwrite):
            print(f'{args.output_filename} already exists; refusing to overwrite. Pass --overwrite if you want to do it anyway.', file=sys.stderr)
            raise SystemExit(1)
    elif args.command == 'show':
        show4(args.input_filename)
