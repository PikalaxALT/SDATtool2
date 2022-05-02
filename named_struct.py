import struct
import dataclasses
import typing
from utils import classproperty


@dataclasses.dataclass(init=False)
class DataClass:
    """A base class for"""
    __byteorder__ = 'little'
    _struct: struct.Struct

    def __init__(self, *args, **kwargs):
        if self.__class__ is DataClass:
            raise NotImplementedError
        super().__init__(*args, **kwargs)

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
        return cls(*cls._struct.unpack(buffer))

    @classmethod
    def unpack_from(cls, buffer: typing.ByteString, offset=0):
        return cls(*cls._struct.unpack_from(buffer, offset=offset))

    @classmethod
    def iter_unpack(cls, buffer: typing.ByteString):
        for tup in cls._struct.iter_unpack(buffer):
            yield cls(*tup)

    def pack(self):
        return self._struct.pack(*dataclasses.astuple(self))

    def pack_into(self, buffer: typing.ByteString, offset: int):
        self._struct.pack_into(buffer, offset, *dataclasses.astuple(self))

    @classproperty
    def size(cls):
        return cls._struct.size


NamedTuple = type[DataClass]
