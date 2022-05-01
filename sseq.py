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
    SseqCommand('Variable_B0', 3),
    SseqCommand('Variable_B1', 3),
    SseqCommand('Variable_B2', 3),
    SseqCommand('Variable_B3', 3),
    SseqCommand('Variable_B4', 3),
    SseqCommand('Variable_B5', 3),
    SseqCommand('Variable_B6', 3),
    SseqCommand('Variable_B7', 3),
    SseqCommand('Variable_B8', 3),
    SseqCommand('Variable_B9', 3),
    SseqCommand('Variable_BA', 3),
    SseqCommand('Variable_BB', 3),
    SseqCommand('Variable_BC', 3),
    SseqCommand('Variable_BD', 3),
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
    Variable_B0 = 0xB0
    Variable_B1 = 0xB1
    Variable_B2 = 0xB2
    Variable_B3 = 0xB3
    Variable_B4 = 0xB4
    Variable_B5 = 0xB5
    Variable_B6 = 0xB6
    Variable_B7 = 0xB7
    Variable_B8 = 0xB8
    Variable_B9 = 0xB9
    Variable_BA = 0xBA
    Variable_BB = 0xBB
    Variable_BC = 0xBC
    Variable_BD = 0xBD
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
