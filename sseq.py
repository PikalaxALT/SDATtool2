import enum
import typing


class SseqCommand(typing.NamedTuple):
    """Data class for an SSEQ command"""
    name: str = ''
    nargs: int = 0


sseq_commands = [
    SseqCommand('Delay', -1),
    SseqCommand('Instrument', -1),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand('Pointer', 4),
    SseqCommand('Jump', 3),
    SseqCommand('Call', 3),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand('Pan', 1),
    SseqCommand('Volume', 1),
    SseqCommand('MasterVolume', 1),
    SseqCommand('Transpose', 1),
    SseqCommand('PitchBend', 1),
    SseqCommand('PitchBendRange', 1),
    SseqCommand('Priority', 1),
    SseqCommand('Poly', 1),
    SseqCommand('Tie', 1),
    SseqCommand('PortamentoControll', 1),
    SseqCommand('ModDepth', 1),
    SseqCommand('ModSpeed', 1),
    SseqCommand('ModType', 1),
    SseqCommand('ModRange', 1),
    SseqCommand('PortamentoOnOff', 1),
    SseqCommand('PortamentoTime', 1),
    SseqCommand('Attack', 1),
    SseqCommand('Decay', 1),
    SseqCommand('Sustain', 1),
    SseqCommand('Release', 1),
    SseqCommand('LoopStart', 1),
    SseqCommand('Expression', 1),
    SseqCommand('Print', 1),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand('ModDelay', 2),
    SseqCommand('Tempo', 2),
    SseqCommand(),
    SseqCommand('PitchSweep', 2),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand(),
    SseqCommand('LoopEnd'),
    SseqCommand('Return\n'),
    SseqCommand('TracksUsed', 2),
    SseqCommand('TrackEnd\n'),
]


class SseqCommandId(enum.Enum):
    """Enum class mapping SSEQ commands."""
    Delay = 0x80
    Instrument = 0x81
    Pointer = 0x93
    Jump = 0x94
    Call = 0x95
    Pan = 0xC0
    Volume = 0xC1
    MasterVolume = 0xC2
    Transpose = 0xC3
    PitchBlend = 0xC4
    PitchBlendRange = 0xC5
    Priority = 0xC6
    Poly = 0xC7
    Tie = 0xC8
    PortamentoControll = 0xC9
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
    TracksUsed = 0xFE
    TrackEnd = 0xFF

    @property
    def info(self):
        """Gets the SseqCommand corresponding to the enum value."""
        cmd = sseq_commands[self.value - 0x80]
        if not cmd.name:
            cmd = SseqCommand(f'Unknown_0x{self.value:02X}')
        return cmd
