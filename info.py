import struct
import dataclasses
import typing


class NamedStruct(struct.Struct):
    """A variant of struct that doubles as a dataclass."""
    def __init__(self, cls_name, _format, fields, **kwargs):
        super().__init__(_format)
        self._cls = dataclasses.make_dataclass(cls_name, fields, **kwargs)  # no slots for py39 compat

    def _make(self, values: tuple):
        return self._cls(*values)

    def __call__(self, *args):
        return self._cls(*args)

    def unpack(self, buffer: typing.ByteString):
        return self._make(super().unpack(buffer))

    def unpack_from(self, buffer: typing.ByteString, offset=0):
        return self._make(super().unpack_from(buffer, offset=offset))

    def iter_unpack(self, buffer: typing.ByteString):
        for tup in super().iter_unpack(buffer):
            yield self._make(tup)

    def pack(self, obj):
        return super().pack(*dataclasses.astuple(obj))

    def pack_into(self, buffer: typing.ByteString, offset: int, obj):
        super().pack_into(buffer, offset, *dataclasses.astuple(obj))

    @property
    def cls(self):
        return self._cls


NNSSndArcSeqInfo = NamedStruct(
    'NNSSndArcSeqInfo', '<LHBBBBH', [
        ('fileId', int),
        ('bankNo', int),
        ('volume', int),
        ('channelPrio', int),
        ('playerPrio', int),
        ('playerNo', int),
        ('reserved', int),
    ]
)

NNSSndArcSeqArcInfo = NamedStruct(
    'NNSSndArcSeqArcInfo', '<L', [
        ('fileId', int),
    ]
)

NNSSndArcBankInfo = NamedStruct(
    'NNSSndArcBankInfo', '<L4H', [
        ('fileId', int),
        ('waveArcNo_0', int),
        ('waveArcNo_1', int),
        ('waveArcNo_2', int),
        ('waveArcNo_3', int),
    ]
)


class WaveArcInfo:
    raw: int

    @property
    def fileId(self):
        return self.raw & 0xFFFFFF

    @fileId.setter
    def fileId(self, value):
        self.raw = (self.raw & ~0xFFFFFF) | (value & 0xFFFFFF)

    @property
    def flags(self):
        return (self.raw >> 24) & 0xFF

    @flags.setter
    def flags(self, value):
        self.raw = (self.raw & ~0xFF000000) | ((value & 0xFF) << 24)


NNSSndArcWaveArcInfo = NamedStruct(
    'NNSSndArcWaveArcInfo', '<L', [
        ('raw', int),
    ],
    bases=(WaveArcInfo,)
)

NNSSndArcStrmInfo = NamedStruct(
    'NNSSndArcStrmInfo', '<LBBBB', [
        ('fileId', int),
        ('volume', int),
        ('playerPrio', int),
        ('playerNo', int),
        ('flags', int),
    ]
)

NNSSndArcPlayerInfo = NamedStruct(
    'NNSSndArcPlayerInfo', '<BBHL', [
        ('seqMax', int),
        ('padding', int),
        ('allocChBitFlag', int),
        ('heapSize', int),
    ]
)

NNSSndArcStrmPlayerInfo = NamedStruct(
    'NNSSndArcStrmPlayerInfo', '<B2B', [
        ('numChannels', int),
        ('chNoList_0', int),
        ('chNoList_1', int),
    ]
)

NNSSndArcGroupItem = NamedStruct(
    'NNSSndArcGroupItem', '<BB2xL', [
        ('type', int),
        ('loadFlag', int),
        ('index', int),
    ]
)

NNSSndArcGroupInfo = NamedStruct(
    'NNSSndArcGroupInfo', '<L', [
        ('count', int),
    ]
)
