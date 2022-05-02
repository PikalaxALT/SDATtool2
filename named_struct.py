import struct
import dataclasses
import typing
import collections.abc
from utils import classproperty


CStruct = typing.TypeVar('CStruct')
NamedStruct = type[CStruct]


class DataClass:
    """A base class for merging the functionality of struct with dataclasses.

    Do not attempt to instantiate this class. Instead, subclass it and define
    the fields annotated with their C types.
    See https://docs.python.org/3/library/struct.html#format-characters for
    valid annotations.
    Note that the resulting dataclass will not be strongly typed.

    Example:

    @dataclasses.dataclass
    class MyDataClass(DataClass):
        __byteorder__ = 'native'  # default: 'little'
        name: '16s'  # bytes len=16
        balance: 'L' # int
        age: 'B'     # int
    """
    __byteorder__ = 'little'
    _struct: struct.Struct

    def __init__(self, *args, **kwargs):
        if self.__class__ is DataClass:
            raise NotImplementedError
        super().__init__(*args, **kwargs)

    def __post_init__(self):
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        fmtstr = {
            'little': '<',
            'big': '>',
        }.get(cls.__byteorder__, 'little')
        for name, spec in cls.__annotations__.items():
            if not name.startswith('_'):
                fmtstr += spec
                cls.__annotations__[name] = typing.Any
        cls._struct = struct.Struct(fmtstr)

    @classmethod
    def unpack_word(cls, buffer: typing.ByteString):
        return int.from_bytes(buffer[:4], cls.__byteorder__)

    @classmethod
    def pack_word(cls, value: int):
        return value.to_bytes(4, cls.__byteorder__)

    @classmethod
    def unpack(cls, buffer: typing.ByteString) -> CStruct:
        """Like struct.Struct().unpack, but returns an instance of the
        data class instead of a tuple."""
        return cls(*cls._struct.unpack(buffer))

    @classmethod
    def unpack_from(cls, buffer: typing.ByteString, offset=0) -> CStruct:
        """Like struct.Struct().unpack_from, but returns an instance of the
        data class instead of a tuple."""
        return cls(*cls._struct.unpack_from(buffer, offset=offset))

    @classmethod
    def iter_unpack(cls, buffer: typing.ByteString) -> collections.abc.Iterator[CStruct]:
        """Like struct.Struct().iter_unpack, but returns an instance of the
        data class instead of a tuple."""
        for tup in cls._struct.iter_unpack(buffer):
            yield cls(*tup)

    @classmethod
    def unpack_array(cls, buffer: typing.ByteString):
        """Returns an iterator of data class instances from a length-encoded
        array. The length value is expected to be a 32-bit word."""
        count = cls.unpack_word(buffer)
        length = count * cls.size
        return cls.iter_unpack(buffer[4:4 + length])
    
    @classmethod
    def unpack_array_from(cls, buffer: typing.ByteString, offset=0):
        """Returns an iterator of data class instances from a length-encoded
        array. The length value is expected to be a 32-bit word."""
        count = cls.unpack_word(buffer[offset:offset + 4])
        length = count * cls.size
        return cls.iter_unpack(buffer[offset + 4:offset + 4 + length])

    def pack(self):
        """Like struct.Struct().pack, but uses the instance of the
        data class instead of a tuple."""
        return self._struct.pack(*dataclasses.astuple(self))

    def pack_into(self, buffer: typing.ByteString, offset: int):
        """Like struct.Struct().pack_into, but uses the instance of the
        data class instead of a tuple."""
        self._struct.pack_into(buffer, offset, *dataclasses.astuple(self))
    
    @classmethod
    def pack_array(cls, array: 'list[CStruct]'):
        """Packs a length-encoded array of DataClass into bytes"""
        ret = cls.pack_word(len(array))
        for obj in array:
            ret += obj.pack()
        return ret
    
    @classmethod
    def pack_array_into(cls, buffer: typing.ByteString, offset: int, array: 'list[CStruct]'):
        """Packs a length-encoded array of DataClass into an existing buffer"""
        buffer[offset:offset + 4] = cls.pack_word(len(array))
        for i, obj in enumerate(array):
            obj.pack_into(buffer, offset + 4 + cls.size * i)

    @classproperty
    def size(cls):
        """Gets the size of the underlying struct."""
        return cls._struct.size
