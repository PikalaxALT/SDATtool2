import bisect
import collections.abc
import dataclasses
import typing
import enum

from .named_struct import DataClass


class SNDInstType(enum.Enum):
    SND_INST_INVALID = 0
    SND_INST_PCM = 1
    SND_INST_PSG = 2
    SND_INST_NOISE = 3
    SND_INST_DIRECTPCM = 4
    SND_INST_NULL = 5
    SND_INST_DRUM_SET = 16
    SND_INST_KEY_SPLIT = 17


@dataclasses.dataclass
class SNDInstOffset(DataClass):
    raw: 'L'

    @property
    def type(self):
        return SNDInstType(self.raw & 0xFF)

    @type.setter
    def type(self, value: SNDInstType):
        self.raw = (self.raw & ~0xFF) | (value.value & 0xFF)

    @property
    def offset(self):
        return (self.raw >> 8) & 0xFFFFFF

    @offset.setter
    def offset(self, value: int):
        self.raw = (self.raw & ~0xFFFFFF00) | ((value & 0xFFFFFF) << 8)

    def to_dict(self):
        return {
            'type': self.type.name,
            'offset': self.offset
        }


@dataclasses.dataclass
class SNDInstParam(DataClass):
    wave_0: 'H'
    wave_1: 'H'
    original_key: 'B'
    attack: 'B'
    decay: 'B'
    sustain: 'B'
    release: 'B'
    pan: 'B'

    @property
    def wave(self):
        return [self.wave_0, self.wave_1]

    @wave.setter
    def wave(self, value: collections.abc.Iterable[int, int]):
        self.wave_0, self.wave_1 = value

    def to_dict(self):
        ret = dataclasses.asdict(self)
        del ret['wave_0'], ret['wave_1']
        ret['wave'] = self.wave
        return ret


@dataclasses.dataclass
class SNDInstData(DataClass):
    type: 'B'
    padding: 'B'
    wave_0: 'H'
    wave_1: 'H'
    original_key: 'B'
    attack: 'B'
    decay: 'B'
    sustain: 'B'
    release: 'B'
    pan: 'B'

    def __post_init__(self):
        self.type = SNDInstType(self.type)

    @property
    def wave(self):
        return [self.wave_0, self.wave_1]

    @wave.setter
    def wave(self, value: collections.abc.Iterable[int, int]):
        self.wave_0, self.wave_1 = value

    def to_dict(self):
        ret = dataclasses.asdict(self)
        ret['type'] = ret['type'].name
        del ret['wave_0'], ret['wave_1']
        ret['wave'] = self.wave
        return ret


@dataclasses.dataclass
class SNDDrumSet(DataClass):
    min: 'B'
    max: 'B'

    @classmethod
    def from_binary(cls, bindata: typing.ByteString, offset: int):
        self = cls.unpack_from(bindata, offset)
        self.instdata = list(SNDInstData.iter_unpack(
            bindata[offset + cls.size:offset + cls.size + SNDInstData.size * (self.max - self.min + 1)]))
        return self

    def __post_init__(self):
        self.instdata = []

    def __getitem__(self, item):
        assert self.min <= item <= self.max <= 255
        return self.instdata[item - self.min]

    def __setitem__(self, key, value):
        assert key <= 255
        if key < self.min:
            self.instdata = [None for _ in range(key, self.min)] + self.instdata
            self.min = key
        elif key > self.max:
            self.instdata = self.instdata + [None for _ in range(self.max, key + 1)]
            self.max = key
        self.instdata[key] = value

    def to_dict(self):
        return dataclasses.asdict(self) | {
            'instruments': [inst.to_dict() for inst in self.instdata]
        }


@dataclasses.dataclass
class SNDKeySplit(DataClass):
    key: '8s'

    def __post_init__(self):
        self.key = bytearray(self.key)
        self.instdata = []

    @classmethod
    def from_binary(cls, bindata: typing.ByteString, offset: int):
        self = cls.unpack_from(bindata, offset)
        num_inst = sum(1 for x in self.key if x)
        self.instdata = list(
            SNDInstData.iter_unpack(bindata[offset + cls.size:offset + cls.size + SNDInstData.size * num_inst]))
        return self

    def to_dict(self):
        return {
            'key': list(self.key.rstrip(b'\0')),
            'instruments': [inst.to_dict() for inst in self.instdata]
        }


@dataclasses.dataclass
class SNDBankData(DataClass):
    signature: '4s'
    byteOrder: 'H'
    version: 'H'
    fileSize: 'L'
    headerSize: 'H'
    dataBlocks: 'H'
    kind: 'L'
    size_: 'L'
    waveLink_dummy: '32s'

    inst_unpack_methods = {
        SNDInstType.SND_INST_INVALID: lambda x, y: None,
        SNDInstType.SND_INST_DRUM_SET: SNDDrumSet.from_binary,
        SNDInstType.SND_INST_KEY_SPLIT: SNDKeySplit.from_binary,
    }

    def __post_init__(self):
        super().__post_init__()
        self.instOffsets: list[SNDInstOffset] = []
        self.insts = []

    @staticmethod
    def get_instrument(file: typing.ByteString, offset: SNDInstOffset):
        return SNDBankData.inst_unpack_methods.get(offset.type, SNDInstParam.unpack_from)(file, offset.offset)

    @classmethod
    def from_binary(cls, file: typing.ByteString):
        self = cls.unpack_from(file)
        self.instOffsets = list(SNDInstOffset.unpack_array_from(file, cls.size))
        self.insts = [SNDBankData.get_instrument(file, offset) for offset in self.instOffsets]
        return self
