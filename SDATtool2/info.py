import collections.abc
import dataclasses
import itertools
import os
import typing
import warnings
import json

from .named_struct import DataClass, NamedStruct
from .sdat_io import SdatIO, CoreInfoType
from .sseq import SseqToTxtConverter
from .sbnk import SNDBankData


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
        self.bank = None
        self.player = None

    def to_dict(self):
        ret = dataclasses.asdict(self)
        if self.bank is not None:
            ret['bank'] = self.bank.name
        if self.player is not None:
            ret['player'] = self.player.name
        return ret


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
        self.waveArc = []

    @property
    def waveArcNo(self):
        return [x for x in [
            self.waveArcNo_0,
            self.waveArcNo_1,
            self.waveArcNo_2,
            self.waveArcNo_3
        ] if x != 65535]

    @waveArcNo.setter
    def waveArcNo(self, value: collections.abc.Collection[int]):
        if len(value) > 4:
            warnings.warn('Setting waveArcNo with %d elements, but the capacity is 4' % len(value))
        for i, x in itertools.zip_longest(range(4), value[:4], fillvalue=0xFFFF):
            setattr(self, f'waveArcNo_{i}', x)

    def to_dict(self):
        return {
            'fileId': self.fileId,
            'waveArcNo': self.waveArcNo,
            'waveArc': [waveArc.name for waveArc in self.waveArc]
        }


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

    def to_dict(self):
        return {'fileId': self.fileId, 'flags': self.flags}

    def to_tuple(self):
        return (self.fileId, self.flags)


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
    _kind = CoreInfoType.GROUP

    type: 'B'
    loadFlags: 'B'
    padding: 'H'
    index: 'L'

    def __post_init__(self):
        self.seq = None

    def to_dict(self):
        ret = dataclasses.asdict(self)
        if self.seq is not None:
            ret['seq'] = self.seq.name
        return ret


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

    def read_file(self, sdat: SdatIO) -> typing.ByteString:
        return sdat[self.offset:self.offset + self.size_]


@dataclasses.dataclass
class NNSSndArcFat(DataClass):
    kind: 'L'
    size_: 'L'  # avoid namespace conflict with base class property "size"


@dataclasses.dataclass
class NNSSndArcFile(DataClass):
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
    dummy: '16s'


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
class NativeFileInfo:
    name: str = ''
    kind: CoreInfoType = 8
    contents: bytes = b''

    def write_binary(self, outdir: str):
        with open(os.path.join(outdir, self.name), 'wb') as ofp:
            ofp.write(self.contents)

    def dump_sseq_to_txt(self, txtfile: str):
        seq_parser = SseqToTxtConverter(self.contents)
        seqname = os.path.basename(self.name.replace(CoreInfoType.SEQ.file_type.bin_ext, ''))
        with open(txtfile, 'w') as ofp:
            for line in seq_parser.parse():
                line = line.format(seqname=seqname)
                print(line, file=ofp)

    def dump_sbnk_to_json(self, txtfile: str):
        sbnk = SNDBankData.from_binary(self.contents)
        sbnk_dict = {
            'instruments': [
                ({
                    'type': offset.type.name
                } | (inst.to_dict() if inst is not None else {}))
                for offset, inst in zip(sbnk.instOffsets, sbnk.insts)
            ]
        }
        with open(txtfile, 'w') as ofp:
            json.dump(sbnk_dict, ofp, indent=4)

    def dump_text(self, outdir):
        if not isinstance(self.kind, CoreInfoType):
            return
        txtfile = os.path.join(outdir, self.name.replace(self.kind.file_type.bin_ext, self.kind.file_type.txt_ext))
        if self.kind is CoreInfoType.SEQ:
            self.dump_sseq_to_txt(txtfile)
        elif self.kind is CoreInfoType.BANK:
            self.dump_sbnk_to_json(txtfile)


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
        self.file_descriptions: list[NativeFileInfo] = []

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

    def set_name(self, info, symb, info_idx):
        if info._kind is CoreInfoType.SEQARC:
            info.name, info.arc_names = symb
        else:
            info.name = symb
        if not info.name:
            info.name = f'{info._kind.name}_{info_idx:03d}'

    def add_file(self, info, contents):
        if info.fileId >= len(self.file_descriptions):
            self.file_descriptions += [NativeFileInfo() for _ in range(info.fileId - len(self.file_descriptions) + 1)]
        desc = self.file_descriptions[info.fileId]
        if not desc.name:
            desc.name = info._kind.make_file_name(info.name)
            desc.kind = info._kind
            desc.contents = contents
        info.filename = desc.name

    def set_symbols(self, symbols: SymbolData, files: list[typing.ByteString]):
        """Unify the INFO objects with the SYMB objects"""
        for infolist, symbollist in zip(self, symbols):
            for i, (info, symb) in enumerate(zip(infolist, symbollist)):
                if hasattr(info, 'name'):
                    self.set_name(info, symb, i)
                if hasattr(info, 'fileId'):
                    self.add_file(info, files[info.fileId])
                if isinstance(info, NNSSndArcSeqInfo):
                    info.bank = self.bank[info.bankNo]
                    info.player = self.player[info.playerNo]
                elif isinstance(info, NNSSndArcBankInfo):
                    info.waveArc = [self.waveArc[x] for x in info.waveArcNo]
                elif isinstance(info, NNSSndArcGroupInfo):
                    for i, x in enumerate(info):
                        x.name = f'{info.name}_{i:03d}'
                        x.seq = self.seq[x.index]

    @staticmethod
    def make_name(info, index, idx2=None):
        return getattr(info, 'name', f'{info._kind.name}_{index:03d}' + ('' if idx2 is None else f'_{idx2:03d}'))

    @staticmethod
    def single_to_dict(info, index, idx2=None):
        if not dataclasses.is_dataclass(info):
            return {}
        ret = info.to_dict() if hasattr(info, 'to_dict') else dataclasses.asdict(info)
        ret['name'] = InfoData.make_name(info, index, idx2)
        if hasattr(info, 'arc_names'):
            ret['arc_names'] = info.arc_names
        if hasattr(info, 'filename'):
            ret['filename'] = info.filename.replace('\\', '/')  # use Unix pathsep for JSON
        return ret

    def to_dict(self):
        result = {}
        for kind, infolist in zip(CoreInfoType, self):
            result[kind.name] = {}
            for i, info in enumerate(infolist):
                if info is None:
                    continue
                if isinstance(info, collections.abc.Iterable):
                    name = InfoData.make_name(info, i) if hasattr(info, '_kind') else ''
                    result[kind.name][i] = {
                        'name': name,
                        'list': [InfoData.single_to_dict(x, i, j) for j, x in enumerate(info)],
                    }
                else:
                    result[kind.name][i] = InfoData.single_to_dict(info, i)
        return result

    def dump_files(self, outdir):
        for kind, infolist in zip(CoreInfoType, self):
            if kind.file_type is not None and infolist:
                os.makedirs(os.path.join(outdir, 'Files', kind.name), exist_ok=True)
        for i, filedesc in enumerate(self.file_descriptions):
            if not filedesc.name:
                os.makedirs(os.path.join(outdir, 'Files', 'Unknown'), exist_ok=True)
                filedesc.name = os.path.join('Files', 'Unknown', f'UNK_{i:05d}.bin')
            filedesc.write_binary(outdir)
            filedesc.dump_text(outdir)
