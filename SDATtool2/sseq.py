import enum
import re
import typing
import dataclasses
from .named_struct import DataClass


class SNDSeqVal(enum.Enum):
    """Enum for SSEQ command param types"""
    SND_SEQ_VAL_U8 = 0
    SND_SEQ_VAL_U16 = 1
    SND_SEQ_VAL_VLV = 2
    SND_SEQ_VAL_RAN = 3
    SND_SEQ_VAL_VAR = 4
    SND_SEQ_VAL_NOINIT = -1


class SseqCommandId(enum.Enum):
    """Enum class mapping SSEQ commands."""
    Delay = 0x80
    Instrument = 0x81
    Pointer = 0x93
    Jump = 0x94
    Call = 0x95
    SetVar = 0xB0
    AddVar = 0xB1
    SubVar = 0xB2
    MulVar = 0xB3
    DivVar = 0xB4
    ShiftVar = 0xB5
    SetVarRnd = 0xB6
    VarEq = 0xB8
    VarGe = 0xB9
    VarGt = 0xBA
    VarLe = 0xBB
    VarLt = 0xBC
    VarNe = 0xBD
    Pan = 0xC0
    Volume = 0xC1
    MasterVolume = 0xC2
    Transpose = 0xC3
    PitchBlend = 0xC4
    PitchBlendRange = 0xC5
    Priority = 0xC6
    Poly = 0xC7
    Tie = 0xC8
    PortamentoControl = 0xC9
    ModDepth = 0xCA
    ModSpeed = 0xCB
    ModType = 0xCC
    ModRange = 0xCD
    PortamentoOnOff = 0xCE
    PortamentoTime = 0xCF
    Attack = 0xD0
    Decay = 0xD1
    Sustain = 0xD2
    Release = 0xD3
    LoopStart = 0xD4
    Expression = 0xD5
    Print = 0xD6
    ModDelay = 0xE0
    Tempo = 0xE1
    PitchSweep = 0xE3
    LoopEnd = 0xFC
    Return = 0xFD
    TrackEnd = 0xFF


@dataclasses.dataclass
class NNSSndSeqData(DataClass):
    signature: '4s'
    byteOrder: 'H'
    version: 'H'
    fileSize: 'L'
    headerSize: 'H'
    dataBlocks: 'H'
    kind: 'L'
    size_: 'L'
    baseOffset: 'L'

    def __post_init__(self):
        assert self.signature == b'SSEQ'
        assert self.byteOrder == 0xFEFF
        assert self.version == 0x0100
        assert self.kind == int.from_bytes(b'DATA', 'little')


class SeqConverter:
    """Base class to share the note names list."""
    note_names = ['C_', 'C#', 'D_', 'D#', 'E_', 'F_', 'F#', 'G_', 'G#', 'A_', 'A#', 'B_']


class SseqToTxtConverter(SeqConverter):
    """Dumps a binary SSEQ file to asm-like text file"""
    def __init__(self, buffer: typing.ByteString = None):
        self.labels = {}
        self.commands = {}
        self.ntracks = 0
        self.trackMask = 0
        if buffer is not None:
            self.header = NNSSndSeqData.unpack_from(buffer)
            self.view = bytes(buffer).rstrip(b'\0')
            self.cursor = self.header.baseOffset
            cmd = self.read_8bit()
            if cmd == 0xFE:
                self.trackMask = self.read_16bit()
                self.ntracks = sum(1 for i in range(16) if ((self.trackMask >> i) & 1))
            else:
                self.cursor -= 1
            self.labels[self.cursor - self.header.baseOffset] = f'{{seqname:s}}_Tk00'
        else:
            self.header = None
            self.view = None
            self.cursor = -1

    def set_buffer(self, buffer: typing.ByteString):
        """Resets the disassembler with a new input file"""
        self.__init__(buffer)

    def read_integer(self, nbytes, *, signed=False):
        """Reads an integer of given length and signedness (default: unsigned)"""
        x = int.from_bytes(self.view[self.cursor:self.cursor + nbytes], 'little', signed=signed)
        self.cursor += nbytes
        return x

    def read_8bit(self, *, signed=False):
        """Reads an (un)signed 8-bit integer"""
        return self.read_integer(1, signed=signed)

    def read_16bit(self, *, signed=False):
        """Reads an (un)signed 16-bit integer"""
        return self.read_integer(2, signed=signed)

    def read_24bit(self, *, signed=False):
        """Reads an (un)signed 8-bit integer. Used for offset values."""
        return self.read_integer(3, signed=signed)

    def read_varlen(self):
        """Reads a variable length big-endian integer"""
        ret = 0
        while True:
            b = self.read_8bit()
            ret = (ret << 7) | (b & 0x7F)
            if not (b & 0x80):
                break
        assert ret <= 0xFFFFFFFF
        return ret

    def read_value(self, valueType: SNDSeqVal, default: SNDSeqVal):
        """Reads an argument of given type. May be overridden to be a var idx or a rand range."""

        # py3.10: match valueType
        if valueType is SNDSeqVal.SND_SEQ_VAL_NOINIT:
            valueType = default
        if valueType is SNDSeqVal.SND_SEQ_VAL_U8:
            ret = self.read_8bit(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_U16:
            ret = self.read_16bit(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_VLV:
            ret = self.read_varlen(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_VAR:
            ret = self.read_8bit(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_RAN:
            lo = self.read_16bit(signed=True)
            hi = self.read_16bit(signed=True)
            ret = (lo, hi)
        else:
            raise ValueError(f'invalid {valueType=}')
        return ret
    
    def parse_note(self, cmd, valueType: SNDSeqVal):
        """Parse a note command from the buffer"""
        pitch = SseqToTxtConverter.note_names[cmd % 12]
        octave = cmd // 12
        velocity = self.read_8bit()
        length = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_VLV)
        return f'{pitch}{octave}', (velocity,) + length
    
    def get_command(self):
        """Get the command index from the buffer. Handles descriptors which determine whether the command
        is conditional or has a random or variable-defined
        value."""
        conditional = False
        valueType = SNDSeqVal.SND_SEQ_VAL_NOINIT
        cmd = self.read_8bit()
        if cmd == 0xA2:
            cmd = self.read_8bit()
            conditional = True
        if cmd == 0xA0:
            cmd = self.read_8bit()
            valueType = SNDSeqVal.SND_SEQ_VAL_RAN
        if cmd == 0xA1:
            cmd = self.read_8bit()
            valueType = SNDSeqVal.SND_SEQ_VAL_VAR
        return cmd, valueType, conditional

    def parse_cmd(self, cmd, valueType: SNDSeqVal):
        """Parse a track script command from the buffer"""
        try:
            command = SseqCommandId(cmd)
        except ValueError:
            command = None
        arg = ()
        # Replicate the logic of the ARM7 component
        high = cmd & 0xF0
        validx = -1
        if high == 0x80:
            # Commands with variable-length-value arg
            arg = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_VLV)
            validx = 0
        elif high == 0x90:
            # Branching logic
            if command is SseqCommandId.Pointer:
                trackno = self.read_8bit()
                address = self.read_24bit()
                arg = (trackno, address)
            elif command is SseqCommandId.Jump or command is SseqCommandId.Call:
                arg = (self.read_24bit(),)
        elif high in (0xC0, 0xD0):
            # Commands with u8 arg
            arg = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U8)
            # The Pan command arg is offset by 0x40
            if command is SseqCommandId.Pan and valueType in (SNDSeqVal.SND_SEQ_VAL_NOINIT, SNDSeqVal.SND_SEQ_VAL_RAN):
                arg = tuple(x - 0x40 for x in arg)
            validx = 0
        elif high == 0xE0:
            # Commands with u16 arg
            arg = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U16)
            validx = 0
        elif high == 0xB0:
            # Commands involving variables
            varnum = self.read_8bit()
            param = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U16)
            arg = (varnum,) + param
            validx = 1
        if command is None:
            arg = (cmd,) + arg
        return command, arg, validx

    def parse_track(self):
        """Core logic for first pass over the binary.
        Consumes the entire buffer"""
        while self.cursor < len(self.view):
            addr = self.cursor
            cmd, valueType, conditional = self.get_command()
            if (cmd & 0x80) == 0:
                cmdstr, params = self.parse_note(cmd, valueType)
                validx = -1
            else:
                cmdstr, params, validx = self.parse_cmd(cmd, valueType)
            yield addr, cmdstr, params, valueType, validx, conditional

    def scan_commands(self):
        """Stores the sseq commands in a dict, as well as
        any branch targets."""
        for addr, cmdstr, params, valueType, validx, conditional in self.parse_track():
            self.commands[addr] = (cmdstr, params, valueType, validx, conditional)
            if cmdstr is SseqCommandId.Pointer:
                # Track header
                trkno, addr = params
                self.labels[addr] = f'{{seqname:s}}_Tk{trkno:02d}'
            elif cmdstr is SseqCommandId.Jump or cmdstr is SseqCommandId.Call:
                # Branching logic
                addr, = params
                self.labels[addr] = f'{{seqname:s}}_Sub{addr:04X}'

    def iter_format_commands(self):
        # Trust that dicts are ordered in Python3
        for addr, (cmdstr, params, valueType, validx, conditional) in self.commands.items():
            addr -= self.header.baseOffset
            if addr in self.labels:
                yield f'{self.labels[addr]}: @ 0x{addr:04X}'
            cond_s = 'IFTRUE ' if conditional else ''
            if isinstance(cmdstr, SseqCommandId):
                # Convert an sseq command statement to str
                if params:
                    # The command has args, let's parse them
                    params_l = [x for x in params]
                    if cmdstr is SseqCommandId.Pointer:
                        params_l[1] = f'{self.labels[params_l[1]]} @ 0x{params_l[1]:04X}'
                    elif cmdstr is SseqCommandId.Jump or cmdstr is SseqCommandId.Call:
                        params_l[0] = self.labels[params_l[0]]
                    if validx != -1 and valueType is not SNDSeqVal.SND_SEQ_VAL_NOINIT:
                        # VAR takes one u8, but RAN takes two u16
                        # Logic handles both cases seamlessly.
                        valueType_s = valueType.name.replace('SND_SEQ_VAL_', '')
                        args_s = ', '.join(map(str, params_l[validx:]))
                        params_l = params_l[:validx] + [f'{valueType_s}({args_s})']
                    yield f'\t{cond_s}{cmdstr.name} {", ".join(map(str, params_l))}'
                else:
                    yield f'\t{cond_s}{cmdstr.name}'
                if cmdstr is SseqCommandId.Return or cmdstr is SseqCommandId.TrackEnd:
                    yield ''
            elif isinstance(cmdstr, str):
                # Convert a note command to str
                yield f'\t{cond_s}{cmdstr}, {params[0]}, {params[1]}'
            elif cmdstr is None:
                # Convert an unknown command to str
                # This should be unreachable
                cmdidx, *params = params
                cmdstr = f'SeqUnkCmd_x{cmdidx:02X}'
                if params:
                    yield f'\t{cond_s}{cmdstr} {", ".join(str(x) for x in params)}'
                else:
                    yield f'\t{cond_s}{cmdstr}'

    def parse(self):
        # First pass to get labels
        self.scan_commands()
        # Second pass to print
        return self.iter_format_commands()


class TxtToSseqConverter(SeqConverter):
    """Convert a text dump of an sseq back to binary format"""

    LABEL_PAT = re.compile(r'(?P<symbol>\w+):')
    NOTE_PAT = re.compile(r'\t(?P<conditional>IFTRUE )?(?P<note>[A-G][_#])(?P<octave>\d), (?P<velocity>\d+), (?P<length>.+)')
    CMD_PAT = re.compile(r'\t(?P<conditional>IFTRUE )?(?P<command>\w+)(?P<args>.*)')
    ARG_LEN = re.compile(r'(?P<kind>\w+)\((?P<args>.+?)\)')
    UNK_COMMAND = re.compile(r'SeqUnkCmd_x(?P<index>[0-9A-F]{2})')
    CMD_ARGS = re.compile(r'\w+\(.+?\)|[^, ]+')

    def __init__(self):
        self.labels = {}
        self.relocs = {}
        self.compiled = bytearray()
        self.tracks_mask = 1

    def write_integer(self, value: int, nbytes, offset=None):
        """Sets an arbitrary integer value to the buffer"""
        if value < 0:
            value += 1 << (8 * nbytes)
        buffer = value.to_bytes(nbytes, 'little')
        if offset is None:
            self.compiled += buffer
        else:
            self.compiled[offset:offset + nbytes] = buffer

    def write_8bits(self, value: int, offset=None):
        """Sets an 8-bit integer to the buffer"""
        self.write_integer(value, 1, offset=offset)

    def write_16bits(self, value: int, offset=None):
        """Sets a 16-bit integer to the buffer"""
        self.write_integer(value, 2, offset=offset)

    def write_24bits(self, value: int, offset=None):
        """Sets a 24-bit integer to the buffer"""
        self.write_integer(value, 3, offset=offset)

    def write_varlen(self, value: int, offset=None):
        """Sets a big-endian variable-length value to the buffer"""
        buffer = bytearray()
        while value:
            buffer += ((value & 0x7F) | 0x80).to_bytes(1, 'little')
            value >>= 7
        buffer[0] &= 0x7F
        buffer = buffer[::-1]
        nbytes = len(buffer)
        if offset is None:
            self.compiled += buffer
        else:
            self.compiled[offset:offset + nbytes] = buffer

    def handle_prefix(self, match: re.Match, var_arg: re.Match):
        """Encodes whether the command is conditional, and whether the
        arg is VAR or RAN"""
        if match['conditional']:
            self.write_8bits(0xA2)
        if var_arg is not None:
            if var_arg['kind'] == 'RAN':
                self.write_8bits(0xA0)
            elif var_arg['kind'] == 'VAR':
                self.write_8bits(0xA1)
            else:
                raise ValueError('invalid overridden arg type')

    def handle_var_arg(self, raw: str, var_arg: re.Match, default: SNDSeqVal):
        """For many commands, the last argument is a flex value.
        A default type is supplied, but if a var_arg pattern is
        found, it will encode that logic instead."""
        if var_arg is None:
            if default is SNDSeqVal.SND_SEQ_VAL_VLV:
                self.write_varlen(int(raw))
            elif default is SNDSeqVal.SND_SEQ_VAL_U8:
                self.write_8bits(int(raw))
            elif default is SNDSeqVal.SND_SEQ_VAL_U16:
                self.write_16bits(int(raw))
            else:
                raise ValueError('invalid default arg type')
        elif var_arg['kind'] == 'RAN':
            for value in var_arg['args'].split(', '):
                self.write_16bits(int(value))
        else:
            self.write_8bits(int(var_arg['args']))

    def add_reloc(self, label):
        """Used in the first parsing phase to define a relocatable symbol."""
        self.relocs[len(self.compiled)] = label
        self.write_24bits(0)

    def dispatch_relocs(self):
        """Used in the second parsing phase to assign all
        relocatable symbols to their final offsets."""
        for addr, label in self.relocs.items():
            target = self.labels[label]
            self.write_24bits(target, offset=addr)

    def write_note(self, match: re.Match):
        """Encode a note command"""
        pitch = TxtToSseqConverter.note_names.index(match['note']) + 12 * int(match['octave'])
        velocity = int(match['velocity'])
        var_arg = TxtToSseqConverter.ARG_LEN.match(match['length'])
        self.handle_prefix(match, var_arg)
        self.write_8bits(pitch)
        self.write_8bits(velocity)
        self.handle_var_arg(match['length'], var_arg, SNDSeqVal.SND_SEQ_VAL_VLV)

    def write_command(self, match: re.Match):
        """Encode an sseq script command"""
        try:
            cmd = getattr(SseqCommandId, match['command'])
            cmd_idx = cmd.value
        except AttributeError:
            # This should be unreachable
            cmd_match = TxtToSseqConverter.UNK_COMMAND.match(match['command'])
            if cmd_match is None:
                raise
            cmd = None
            cmd_idx = int(cmd_match['index'], 16)
        args = TxtToSseqConverter.CMD_ARGS.findall(match['args'])
        if args:
            var_arg = TxtToSseqConverter.ARG_LEN.match(args[-1])
        else:
            var_arg = None
        self.handle_prefix(match, var_arg)
        self.write_8bits(cmd_idx)
        # Replicate the logic from the ARM7 binary
        high = cmd_idx & 0xF0
        if high == 0x80:
            # Commands with a variable-length-value arg
            self.handle_var_arg(args[0], var_arg, SNDSeqVal.SND_SEQ_VAL_VLV)
        elif high == 0x90:
            # Commands relating to branching logic
            if cmd is SseqCommandId.Pointer:
                trackno, label = args
                trackno = int(trackno)
                if self.tracks_mask == 1:
                    # If there's more than just the one track,
                    # a command is emitted to encode this information.
                    # This is excluded from the text file, so
                    # its presence is inferred from the Pointer
                    # commands that follow.
                    # As a consequence, all labels and relocs
                    # should be shifted by 3 bytes.
                    # Usually the relocs dict is empty, and the
                    # labels dict only has the first track's pointer.
                    self.compiled = bytearray(3) + self.compiled
                    self.labels = {key: value + 3 for key, value in self.labels.items()}
                    self.relocs = {key + 3: value for key, value in self.relocs.items()}
                self.tracks_mask |= 1 << trackno
                self.write_8bits(trackno)
                self.add_reloc(label)
            elif cmd is SseqCommandId.Jump or cmd is SseqCommandId.Call:
                label, = args
                self.add_reloc(label)
        elif high in (0xC0, 0xD0):
            # Commands with a u8 arg
            arg, = args
            self.handle_var_arg(arg, var_arg, SNDSeqVal.SND_SEQ_VAL_U8)
            if cmd is SseqCommandId.Pan:
                # The Pan argument is offset by 0x40
                if var_arg is None:
                    self.compiled[-1] = (self.compiled[-1] + 0x40) & 0xFF
                elif var_arg['kind'] == 'RAN':
                    low = int.from_bytes(self.compiled[-4:-2], 'little', signed=True)
                    high = int.from_bytes(self.compiled[-2:], 'little', signed=True)
                    low += 0x40
                    high += 0x40
                    self.write_16bits(low, len(self.compiled) - 4)
                    self.write_16bits(high, len(self.compiled) - 2)
        elif high == 0xE0:
            # Commands with a u16 arg
            arg, = args
            self.handle_var_arg(arg, var_arg, SNDSeqVal.SND_SEQ_VAL_U16)
        elif high == 0xB0:
            # Commands related to variables
            varnum, param = args
            self.write_8bits(int(varnum))
            self.handle_var_arg(param, var_arg, SNDSeqVal.SND_SEQ_VAL_U16)

    def compile(self, file: typing.TextIO):
        """Logic for assembling a text file to SSEQ."""

        # The main parsing loop. Single-pass.
        for line in file:
            line = line.split('@')[0].rstrip()
            match = TxtToSseqConverter.LABEL_PAT.match(line)
            if match is not None:
                self.labels[match['symbol']] = len(self.compiled)
                continue
            match = TxtToSseqConverter.NOTE_PAT.match(line)
            if match is not None:
                self.write_note(match)
                continue
            match = TxtToSseqConverter.CMD_PAT.match(line)
            if match is not None:
                self.write_command(match)
                continue

        # Now that all labels are known, assign their offsets
        # within the seq.
        self.dispatch_relocs()
        # If there's more than one track, encode that information here.
        if self.tracks_mask != 1:
            self.write_8bits(0xFE, 0)
            self.write_16bits(self.tracks_mask, 1)
        # Pad to 32-bit alignment
        if len(self.compiled) & 3:
            self.compiled += bytes(4 - (len(self.compiled) & 3))
        # Build the header
        header = NNSSndSeqData(
            # SNDBinaryFileHeader
            b'SSEQ',
            0xFEFF,
            0x0100,
            NNSSndSeqData.size + len(self.compiled),
            0x0010,
            1,
            # SNDBinaryBlockHeader
            int.from_bytes(b'DATA', 'little'),
            12 + len(self.compiled),
            NNSSndSeqData.size
        )
        return header.pack() + self.compiled
