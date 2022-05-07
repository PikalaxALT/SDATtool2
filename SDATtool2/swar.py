import dataclasses
import os.path
import typing

from .named_struct import DataClass


@dataclasses.dataclass
class SWAVHeader(DataClass):
    signature: '4s'
    byteOrder: 'H'
    version: 'H'
    fileSize: 'L'
    headerSize: 'H'
    dataBlocks: 'H'
    kind: 'L'
    size_: 'L'


@dataclasses.dataclass
class SNDWaveData(DataClass):
    format: 'B'
    loopflag: 'B'
    rate: 'H'
    timer: 'H'
    loopstart: 'H'
    looplen: 'L'

    def __post_init__(self):
        self.samples = b''

    @classmethod
    def from_binary(cls, file: typing.ByteString, begin: int, end: int):
        self = cls.unpack_from(file, begin)
        self.samples = file[begin + cls.size:end]
        return self

    def to_swav(self, filename: str):
        """Dump SWAV file"""
        header = SWAVHeader(
            b'SWAV',
            0xFEFF,
            0x0100,
            SWAVHeader.size + self.size + len(self.samples),
            0x10,
            1,
            int.from_bytes(b'DATA', 'little'),
            self.size + len(self.samples) + 8
        )
        with open(filename, 'wb') as ofp:
            ofp.write(header.pack() + self.pack() + self.samples)


@dataclasses.dataclass
class SNDWaveOffset(DataClass):
    offset: 'L'


@dataclasses.dataclass
class SNDWaveArc(DataClass):
    signature: '4s'
    byteOrder: 'H'
    version: 'H'
    fileSize: 'L'
    headerSize: 'H'
    dataBlocks: 'H'
    kind: 'L'
    size_: 'L'
    dummy: '32s'

    def __post_init__(self):
        self.waveOffsets: list[SNDWaveOffset] = []
        self.waves: list[SNDWaveData] = []

    @classmethod
    def from_binary(cls, file: typing.ByteString):
        self = cls.unpack_from(file)
        self.waveOffsets = list(SNDWaveOffset.unpack_array_from(file, cls.size))
        self.waves = [
            SNDWaveData.from_binary(
                file,
                x.offset,
                self.waveOffsets[i].offset if i < len(self.waveOffsets) else len(file)
            ) for i, x in enumerate(self.waveOffsets, 1)
        ]
        return self

    def to_wavs(self, filename_fmt: str):
        dirname = os.path.dirname(filename_fmt)
        os.makedirs(dirname, exist_ok=True)
        for i, swav in enumerate(self.waves):
            swav.to_swav(filename_fmt.format(i))
