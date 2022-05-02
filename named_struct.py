import struct
import dataclasses
import typing
from utils import classproperty


@dataclasses.dataclass
class DataClass:
    __byteorder__ = 'little'
    _struct: struct.Struct

    def __init__(self, *args, **kwargs):
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        fmtstr = {
            'little': '<',
            'big': '>',
            'native': '='
        }.get(cls.__byteorder__, 'little')
        for name, spec in cls.__annotations__.items():
            if not name.startswith('_'):
                fmtstr += spec
                cls.__annotations__[name] = typing.Any
        cls._struct = struct.Struct(fmtstr)

    @classmethod
    def unpack(cls, buffer: typing.ByteString):
        if not dataclasses.is_dataclass(cls):
            return NotImplemented
        return cls(*cls._struct.unpack(buffer))

    @classmethod
    def unpack_from(cls, buffer: typing.ByteString, offset=0):
        if not dataclasses.is_dataclass(cls):
            return NotImplemented
        return cls(*cls._struct.unpack_from(buffer, offset=offset))

    @classmethod
    def iter_unpack(cls, buffer: typing.ByteString):
        if not dataclasses.is_dataclass(cls):
            return NotImplemented
        for tup in cls._struct.iter_unpack(buffer):
            yield cls(*tup)

    def pack(self):
        return self._struct.pack(*dataclasses.astuple(self))

    def pack_into(self, buffer: typing.ByteString, offset: int):
        self._struct.pack_into(buffer, offset, *dataclasses.astuple(self))

    @classproperty
    def size(cls):
        if not dataclasses.is_dataclass(cls):
            return NotImplemented
        return cls._struct.size


NamedTuple = type[DataClass]
