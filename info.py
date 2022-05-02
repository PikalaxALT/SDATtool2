import dataclasses
from named_struct import DataClass


@dataclasses.dataclass
class NNSSndArcSeqInfo(DataClass):
    fileId: 'L'
    bankNo: 'H'
    volume: 'B'
    channelPrio: 'B'
    playerPrio: 'B'
    playerNo: 'B'
    reserved: 'H'


@dataclasses.dataclass
class NNSSndArcSeqArcInfo(DataClass):
    fileId: 'L'


@dataclasses.dataclass
class NNSSndArcBankInfo(DataClass):
    fileId: 'L'
    waveArcNo_0: 'H'
    waveArcNo_1: 'H'
    waveArcNo_2: 'H'
    waveArcNo_3: 'H'


@dataclasses.dataclass
class NNSSndArcWaveArcInfo(DataClass):
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


@dataclasses.dataclass
class NNSSndArcStrmInfo(DataClass):
    fileId: 'L'
    volume: 'B'
    playerPrio: 'B'
    playerNo: 'B'
    flags: 'B'


@dataclasses.dataclass
class NNSSndArcPlayerInfo(DataClass):
    seqMax: 'B'
    padding: 'B'
    allocChBitFlag: 'H'
    heapSize: 'L'


@dataclasses.dataclass
class NNSSndArcStrmPlayerInfo(DataClass):
    numChannels: 'B'
    chNoList_0: 'B'
    chNoList_1: 'B'


@dataclasses.dataclass
class NNSSndArcGroupItem(DataClass):
    type: 'B'
    loadFlags: 'B'
    padding: 'H'
    index: 'L'


@dataclasses.dataclass
class NNSSndArcGroupInfo(DataClass):
    count: 'L'


@dataclasses.dataclass
class NNSSndArcSeqArcOffset(DataClass):
    symbol: 'L'
    table: 'L'


@dataclasses.dataclass
class NNSSndSymbolAndInfoOffsets(DataClass):
    kind: 'L'
    size: 'L'
    seqOffset: 'L'
    seqArcOffset: 'L'
    bankOffset: 'L'
    waveArcOffset: 'L'
    playerOffset: 'L'
    groupOffset: 'L'
    strmPlayerOffset: 'L'
    strmOffset: 'L'


@dataclasses.dataclass
class NNSSndArcHeader(DataClass):
    signature: '4s'
    byteOrder: 'H'
    version: 'H'
    fileSize: 'L'
    headerSize: 'H'
    dataBlocks: 'H'
    seqOffset: 'L'
    seqArcOffset: 'L'
    bankOffset: 'L'
    waveArcOffset: 'L'
    playerOffset: 'L'
    groupOffset: 'L'
    strmPlayerOffset: 'L'
    strmOffset: 'L'
