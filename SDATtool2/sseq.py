import enum
import typing
import dataclasses
from .named_struct import DataClass


class SNDSeqVal(enum.Enum):
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


class SeqParser:
    note_names = ['C_', 'C#', 'D_', 'D#', 'E_', 'F_', 'F#', 'G_', 'G#', 'A_', 'A#', 'B_']

    def __init__(self, buffer: typing.ByteString = None):
        self.labels = {}
        self.commands = {}
        self.ntracks = 0
        self.trackMask = 0
        if buffer is not None:
            self.header = NNSSndSeqData.unpack_from(buffer)
            self.view = bytes(buffer).rstrip(b'\0')
            self.cursor = self.header.baseOffset
            cmd = self.read_u8()
            if cmd == 0xFE:
                self.trackMask = self.read_u16()
                self.ntracks = sum(1 for i in range(16) if ((self.trackMask >> i) & 1))
            else:
                self.cursor -= 1
            self.labels[self.cursor - self.header.baseOffset] = f'{{seqname:s}}_Tk00'
        else:
            self.header = None
            self.view = None
            self.cursor = -1

    def set_buffer(self, buffer: typing.ByteString):
        self.__init__(buffer)

    def rewind(self):
        self.cursor = self.header.baseOffset

    def read_unsigned(self, nbytes):
        x = int.from_bytes(self.view[self.cursor:self.cursor + nbytes], 'little')
        self.cursor += nbytes
        return x

    def read_u8(self):
        return self.read_unsigned(1)

    def read_u16(self):
        return self.read_unsigned(2)

    def read_u24(self):
        return self.read_unsigned(3)

    def read_value(self, valueType: SNDSeqVal, default: SNDSeqVal):
        if valueType is SNDSeqVal.SND_SEQ_VAL_NOINIT:
            valueType = default
        if valueType is SNDSeqVal.SND_SEQ_VAL_U8:
            ret = self.read_u8(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_U16:
            ret = self.read_u16(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_VLV:
            ret = 0
            while True:
                b = self.read_u8()
                ret = (ret << 7) | (b & 0x7F)
                if not (b & 0x80):
                    break
            assert ret <= 0xFFFFFFFF
            ret = ret,
        elif valueType is SNDSeqVal.SND_SEQ_VAL_VAR:
            ret = self.read_u8(),
        elif valueType is SNDSeqVal.SND_SEQ_VAL_RAN:
            lo = self.read_u16()
            hi = self.read_u16()
            ret = (lo, hi)
        else:
            raise ValueError(f'invalid {valueType=}')
        return ret
    
    def parse_note(self, cmd, valueType: SNDSeqVal):
        pitch = SeqParser.note_names[cmd % 12]
        octave = cmd // 12
        velocity = self.read_u8()
        length = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U8)
        return f'{pitch}{octave}', (velocity,) + length
    
    def get_command(self):
        valueType = SNDSeqVal.SND_SEQ_VAL_NOINIT
        cmd = self.read_u8()
        if cmd == 0xA2:
            cmd = self.read_u8()
        if cmd == 0xA0:
            cmd = self.read_u8()
            valueType = SNDSeqVal.SND_SEQ_VAL_RAN
        if cmd == 0xA1:
            cmd = self.read_u8()
            valueType = SNDSeqVal.SND_SEQ_VAL_VAR
        return cmd, valueType

    def parse_cmd(self, cmd, valueType: SNDSeqVal):
        try:
            command = SseqCommandId(cmd)
        except ValueError:
            command = None
        arg = ()
        high = cmd & 0xF0
        validx = -1
        if high == 0x80:
            arg = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_VLV)
            validx = 0
        elif high == 0x90:
            if command is SseqCommandId.Pointer:
                trackno = self.read_u8()
                address = self.read_u24()
                arg = (trackno, address)
            elif command is SseqCommandId.Jump or command is SseqCommandId.Call:
                arg = (self.read_u24(),)
        elif high in (0xC0, 0xD0):
            arg = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U8)
            validx = 0
        elif high == 0xE0:
            arg = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U16)
            validx = 0
        elif high == 0xB0:
            varnum = self.read_u8()
            param = self.read_value(valueType, SNDSeqVal.SND_SEQ_VAL_U16)
            arg = (varnum,) + param
            validx = 1
        if command is None:
            arg = (cmd,) + arg
        return command, arg, validx

    def parse_track(self):
        while self.cursor < len(self.view):
            addr = self.cursor
            cmd, valueType = self.get_command()
            if (cmd & 0x80) == 0:
                cmdstr, params = self.parse_note(cmd, valueType)
                validx = -1
            else:
                cmdstr, params, validx = self.parse_cmd(cmd, valueType)
            yield addr, cmdstr, params, valueType, validx

    def scan_commands(self):
        for addr, cmdstr, params, valueType, validx in self.parse_track():
            self.commands[addr] = (cmdstr, params, valueType, validx)
            if cmdstr is SseqCommandId.Pointer:
                trkno, addr = params
                self.labels[addr] = f'{{seqname:s}}_Tk{trkno:02d}'
            elif cmdstr is SseqCommandId.Jump or cmdstr is SseqCommandId.Call:
                addr, = params
                self.labels[addr] = f'{{seqname:s}}_Sub{addr:04X}'

    def iter_format_commands(self):
        # Trust that dicts are ordered in Python3
        for addr, (cmdstr, params, valueType, validx) in self.commands.items():
            if addr - self.header.baseOffset in self.labels:
                yield f'{self.labels[addr - self.header.baseOffset]}: @ 0x{addr - self.header.baseOffset:04X}'
            if isinstance(cmdstr, SseqCommandId):
                if params:
                    params_l = [x for x in params]
                    if cmdstr is SseqCommandId.Pointer:
                        params_l[1] = f'{self.labels[params_l[1]]} @ 0x{params_l[1]:04X}'
                    elif cmdstr is SseqCommandId.Jump or cmdstr is SseqCommandId.Call:
                        params_l[0] = self.labels[params_l[0]]
                    if validx != -1 and valueType is not SNDSeqVal.SND_SEQ_VAL_NOINIT:
                        valueType_s = valueType.name.replace('SND_SEQ_VAL_', '')
                        params_l = params_l[:validx] + [f'{valueType_s}({", ".join(map(str, params_l[validx:]))})']
                    yield f'\t{cmdstr.name} {", ".join(map(str, params_l))}'
                else:
                    yield f'\t{cmdstr.name}'
                if cmdstr is SseqCommandId.Return or cmdstr is SseqCommandId.TrackEnd:
                    yield ''
            elif isinstance(cmdstr, str):
                yield f'\t{cmdstr}, {params[0]}, {params[1]}'
            elif cmdstr is None:
                cmdidx, *params = params
                cmdstr = f'SeqUnkCmd_x{cmdidx:02X}'
                if params:
                    yield f'\t{cmdstr} {", ".join(str(x) for x in params)}'
                else:
                    yield f'\t{cmdstr}'

    def parse(self):
        # First pass to get labels
        self.scan_commands()
        # Second pass to print
        return self.iter_format_commands()
