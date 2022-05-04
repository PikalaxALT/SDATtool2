import collections.abc
import dataclasses
import os
import typing

from .named_struct import DataClass, NamedStruct
from .sdat_io import SdatIO, CoreInfoType


@dataclasses.dataclass
class NNSSndArcSeqInfo(DataClass):
    _kind = CoreInfoType.SEQ
    fileId: 'L'
    bankNo: 'H'
    volume: 'B'
    channelPrio: 'B'
    playerPrio: 'B'
    playerNo: 'B'
    reserved: 'H'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''
        self.filename = ''


@dataclasses.dataclass
class NNSSndArcSeqArcInfo(DataClass):
    _kind = CoreInfoType.SEQARC
    fileId: 'L'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''
        self.filename = ''
        self.arc_names: list[str] = []


@dataclasses.dataclass
class NNSSndArcBankInfo(DataClass):
    _kind = CoreInfoType.BANK
    fileId: 'L'
    waveArcNo_0: 'H'
    waveArcNo_1: 'H'
    waveArcNo_2: 'H'
    waveArcNo_3: 'H'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''
        self.filename = ''


@dataclasses.dataclass
class NNSSndArcWaveArcInfo(DataClass):
    _kind = CoreInfoType.WAVARC
    raw: 'L'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''
        self.filename = ''

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
    _kind = CoreInfoType.STRM
    fileId: 'L'
    volume: 'B'
    playerPrio: 'B'
    playerNo: 'B'
    flags: 'B'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''
        self.filename = ''


@dataclasses.dataclass
class NNSSndArcPlayerInfo(DataClass):
    _kind = CoreInfoType.PLAYER
    seqMax: 'B'
    padding: 'B'
    allocChBitFlag: 'H'
    heapSize: 'L'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''


@dataclasses.dataclass
class NNSSndArcStrmPlayerInfo(DataClass):
    _kind = CoreInfoType.PLAYER2
    numChannels: 'B'
    chNoList_0: 'B'
    chNoList_1: 'B'

    def __post_init__(self):
        super().__post_init__()
        self.name = ''


@dataclasses.dataclass
class NNSSndArcGroupItem(DataClass):
    type: 'B'
    loadFlags: 'B'
    padding: 'H'
    index: 'L'


class NNSSndArcGroupInfo(list):
    _kind = CoreInfoType.GROUP

    def __init__(self, *args, name='', **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name


@dataclasses.dataclass
class NNSSndArcSeqArcOffset(DataClass):
    symbol: 'L'
    table: 'L'

    @classmethod
    def read_seqarc_strings(cls, base: int, offset: int, sdat: SdatIO):
        if 0 in (base, offset):
            return []

        def inner():
            for x in sdat.read_array(cls, base, offset):
                symbol = sdat.get_string(offset, x.symbol)
                table = NNSSndArcOffsetTable.read_strings(offset, x.table, sdat)
                yield [symbol, table]
        return list(inner())


@dataclasses.dataclass
class NNSSndSymbolAndInfoOffsets(DataClass):
    kind: 'L'
    size_: 'L'  # avoid namespace conflict with base class property "size"
    seqOffset: 'L'
    seqArcOffset: 'L'
    bankOffset: 'L'
    waveArcOffset: 'L'
    playerOffset: 'L'
    groupOffset: 'L'
    strmPlayerOffset: 'L'
    strmOffset: 'L'

    def __iter__(self) -> collections.abc.Iterator[tuple[str, typing.Any]]:
        ret = iter(dataclasses.asdict(self).items())
        # Consume the first two fields
        next(ret)
        next(ret)
        return ret


@dataclasses.dataclass
class NNSSndArcFileInfo(DataClass):
    offset: 'L'
    size_: 'L'
    mem: 'L'
    reserved: 'L'

    def read_file(self, base: int, sdat: SdatIO) -> typing.ByteString:
        if base == 0:
            return b''
        return sdat.data[base + self.offset:base + self.offset + self.size_]


@dataclasses.dataclass
class NNSSndArcFat(DataClass):
    kind: 'L'
    size_: 'L'  # avoid namespace conflict with base class property "size"


@dataclasses.dataclass
class NNSSndArcHeader(DataClass):
    signature: '4s'
    byteOrder: 'H'
    version: 'H'
    fileSize: 'L'
    headerSize: 'H'
    dataBlocks: 'H'
    symbolDataOffset: 'L'
    symbolDataSize: 'L'
    infoOffset: 'L'
    infoSize: 'L'
    fatOffset: 'L'
    fatSize: 'L'
    fileImageOffset: 'L'
    fileImageSize: 'L'


@dataclasses.dataclass
class NNSSndArcOffsetTable(DataClass):
    offset: 'L'

    @classmethod
    def read_all(cls, sbcls: NamedStruct, base: int, offset: int, sdat: SdatIO):
        if 0 in (base, offset):
            return []
        return [sdat.read_struct(sbcls, base, x.offset) for x in sdat.read_array(cls, base, offset)]

    @classmethod
    def read_arrays(cls, sbcls: NamedStruct, base: int, offset: int, sdat: SdatIO, list_factory=list):
        if 0 in (base, offset):
            return []
        return [list_factory(sdat.read_array(sbcls, base, x.offset)) for x in sdat.read_array(cls, base, offset)]

    @classmethod
    def read_strings(cls, base: int, offset: int, sdat: SdatIO):
        if 0 in (base, offset):
            return []
        return [sdat.get_string(base, x.offset) for x in sdat.read_array(cls, base, offset)]


# Non-C-types
@dataclasses.dataclass
class SymbolData:
    seq: list[str] = dataclasses.field(default_factory=list)
    seqArc: list[list[str, list[str]]] = dataclasses.field(default_factory=list)
    bank: list[str] = dataclasses.field(default_factory=list)
    waveArc: list[str] = dataclasses.field(default_factory=list)
    player: list[str] = dataclasses.field(default_factory=list)
    group: list[str] = dataclasses.field(default_factory=list)
    strmPlayer: list[str] = dataclasses.field(default_factory=list)
    strm: list[str] = dataclasses.field(default_factory=list)

    def __iter__(self):
        """Shallow cast to iterator"""
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    @classmethod
    def from_offsets(cls, header: NNSSndSymbolAndInfoOffsets, offset: int, sdat: SdatIO):
        return cls(
            NNSSndArcOffsetTable.read_strings(offset, header.seqOffset, sdat),
            NNSSndArcSeqArcOffset.read_seqarc_strings(offset, header.seqArcOffset, sdat),
            NNSSndArcOffsetTable.read_strings(offset, header.bankOffset, sdat),
            NNSSndArcOffsetTable.read_strings(offset, header.waveArcOffset, sdat),
            NNSSndArcOffsetTable.read_strings(offset, header.playerOffset, sdat),
            NNSSndArcOffsetTable.read_strings(offset, header.groupOffset, sdat),
            NNSSndArcOffsetTable.read_strings(offset, header.strmPlayerOffset, sdat),
            NNSSndArcOffsetTable.read_strings(offset, header.strmOffset, sdat),
        )


# Non-C-types
@dataclasses.dataclass
class InfoData:
    seq: list[NNSSndArcSeqInfo] = dataclasses.field(default_factory=list)
    seqArc: list[NNSSndArcSeqArcInfo] = dataclasses.field(default_factory=list)
    bank: list[NNSSndArcBankInfo] = dataclasses.field(default_factory=list)
    waveArc: list[NNSSndArcWaveArcInfo] = dataclasses.field(default_factory=list)
    player: list[NNSSndArcPlayerInfo] = dataclasses.field(default_factory=list)
    group: list[list[NNSSndArcGroupItem]] = dataclasses.field(default_factory=list)
    strmPlayer: list[NNSSndArcStrmPlayerInfo] = dataclasses.field(default_factory=list)
    strm: list[NNSSndArcStrmInfo] = dataclasses.field(default_factory=list)

    def __iter__(self):
        """Shallow cast to iterator"""
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def __post_init__(self):
        self.filenames = []

    @classmethod
    def from_offsets(cls, header: NNSSndSymbolAndInfoOffsets, offset: int, sdat: SdatIO):
        return cls(
            NNSSndArcOffsetTable.read_all(NNSSndArcSeqInfo, offset, header.seqOffset, sdat),
            NNSSndArcOffsetTable.read_all(NNSSndArcSeqArcInfo, offset, header.seqArcOffset, sdat),
            NNSSndArcOffsetTable.read_all(NNSSndArcBankInfo, offset, header.bankOffset, sdat),
            NNSSndArcOffsetTable.read_all(NNSSndArcWaveArcInfo, offset, header.waveArcOffset, sdat),
            NNSSndArcOffsetTable.read_all(NNSSndArcPlayerInfo, offset, header.playerOffset, sdat),
            NNSSndArcOffsetTable.read_arrays(NNSSndArcGroupItem, offset, header.groupOffset, sdat, list_factory=NNSSndArcGroupInfo),
            NNSSndArcOffsetTable.read_all(NNSSndArcStrmPlayerInfo, offset, header.strmPlayerOffset, sdat),
            NNSSndArcOffsetTable.read_all(NNSSndArcStrmInfo, offset, header.strmOffset, sdat),
        )

    def set_symbols(self, symbols: SymbolData):
        for infolist, symbollist in zip(self, symbols):
            for i, (info, symb) in enumerate(zip(infolist, symbollist)):
                if hasattr(info, 'name'):
                    if info._kind is CoreInfoType.SEQARC:
                        info.name, info.arc_names = symb
                    else:
                        info.name = symb
                    if not info.name:
                        info.name = f'{info._kind.name}_{i:03d}'
                if hasattr(info, 'fileId'):
                    assert info.fileId < 65536
                    if info.fileId >= len(self.filenames):
                        self.filenames += ['' for _ in range(info.fileId - len(self.filenames) + 1)]
                    self.filenames[info.fileId] = self.filenames[info.fileId] or os.path.join(
                        'Files',
                        info._kind.name,
                        info.name + info._kind.file_type.ext
                    )
                    info.filename = self.filenames[info.fileId]

    @staticmethod
    def single_to_dict(info, index, idx2=None):
        if not dataclasses.is_dataclass(info):
            return {}
        ret = dataclasses.asdict(info)
        ret['name'] = getattr(info, 'name', f'{info._kind.name}_{index:03d}' + '' if idx2 is None else f'_{idx2:03d}')
        if hasattr(info, 'arc_names'):
            ret['arc_names'] = info.arc_names
        if hasattr(info, 'filename'):
            ret['filename'] = info.filename
        return ret

    def to_dict(self):
        result: dict[str, list[dict]] = {}
        for kind, infolist in zip(CoreInfoType, self):
            result[kind.name] = []
            for i, info in enumerate(infolist):
                if isinstance(info, collections.abc.Iterable):
                    result[kind.name].append([InfoData.single_to_dict(x, i, j) for j, x in enumerate(info)])
                else:
                    result[kind.name].append(InfoData.single_to_dict(info, i))
        return result

    def dump_files(self, files, outdir):
        for kind in CoreInfoType:
            if kind.file_type is not None:
                os.makedirs(os.path.join(outdir, 'Files', kind.name), exist_ok=True)
        os.makedirs(os.path.join(outdir, 'Files', 'Unknown'), exist_ok=True)
        if len(self.filenames) < len(files):
            self.filenames.extend('' for _ in range(len(files) - len(self.filenames)))
        for i, (name, file) in enumerate(zip(self.filenames, files)):
            if not name:
                name = self.filenames[i] = os.path.join('Files', 'Unknown', f'UNK_{i:05d}.bin')
            with open(os.path.join(outdir, name), 'wb') as ofp:
                ofp.write(file)