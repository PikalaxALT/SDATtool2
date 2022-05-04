import typing
import enum
import os
from .named_struct import NamedStruct, CStruct


class FileType(typing.NamedTuple):
    """Data class for SDAT member filetypes."""
    ext: str = ''
    header: bytes = b''


file_types = [
    FileType('.sseq', b'SSEQ'),
    FileType('.ssar', b'SSAR'),
    FileType('.sbnk', b'SBNK'),
    FileType('.swar', b'SWAR'),
    None,
    None,
    None,
    FileType('.strm', b'STRM'),
    None,
]


class CoreInfoType(enum.Enum):
    """Enum for the core SDAT member types"""
    SEQ = 0
    SEQARC = 1
    BANK = 2
    WAVARC = 3
    PLAYER = 4
    GROUP = 5
    PLAYER2 = 6
    STRM = 7

    @property
    def file_type(self):
        """Returns the FileType corresponding to the enum value."""
        return file_types[self.value]


class SdatIO:
    """Wrapper class for the SDAT buffer"""

    def __init__(self, infile: typing.BinaryIO = None):
        """Creates an SdatIO object from an optional input file.
        If no file is provided, creates an empty SdatIO buffer."""
        self.data = bytearray() if infile is None else bytearray(infile.read())
        self.cursor = 0

    def write(self, x: int, *, size=1, pos: int = None):
        """Writes a value of arbitrary length to the buffer.
        If pos is None, appends the data and advances the cursor."""
        val = x.to_bytes(size, 'little')
        if pos is None:
            self.data += val
            self.cursor = len(self.data)
        else:
            self.data[pos:pos + size] = val

    def append_long(self, x: int):
        """Writes a 32-bit value to the end of the buffer, and advances the cursor."""
        self.write(x, size=4)

    def append_short(self, x: int):
        """Writes a 16-bit value to the end of the buffer, and advances the cursor."""
        self.write(x, size=2)

    def append_byte(self, x: int):
        """Writes an 8-bit value to the end of the buffer, and advances the cursor."""
        self.write(x, size=1)

    def write_long(self, loc: int, x: int):
        """Writes a 32-bit value to the buffer at the specified position."""
        self.write(x, size=4, pos=loc)

    def write_short(self, loc: int, x: int):
        """Writes a 16-bit value to the buffer at the specified position."""
        self.write(x, size=2, pos=loc)

    def write_byte(self, loc: int, x: int):
        """Writes an 8-bit value to the buffer at the specified position."""
        self.write(x, size=1, pos=loc)

    def read(self, size=1, pos: int = None):
        """Reads a value of arbitrary length from the buffer.
        If pos is None, reads from the end of the buffer and advances the cursor.
        Otherwise, reads data at pos."""
        if pos is None:
            pos = self.cursor
            self.cursor += size
        return int.from_bytes(self.data[pos:pos + size], 'little')

    def read_long(self, pos: int = None):
        """Reads a 32-bit value from the buffer.
        If pos is None, reads from the end of the buffer and advances the cursor.
        Otherwise, reads data at pos."""
        return self.read(size=4, pos=pos)

    def read_short(self, pos: int = None):
        """Reads a 16-bit value from the buffer.
        If pos is None, reads from the end of the buffer and advances the cursor.
        Otherwise, reads data at pos."""
        return self.read(size=2, pos=pos)

    def read_byte(self, pos: int = None):
        """Reads an 8-bit value from the buffer.
        If pos is None, reads from the end of the buffer and advances the cursor.
        Otherwise, reads data at pos."""
        return self.read(size=1, pos=pos)

    def get_string(self, base, offset=0):
        """Reads a string from the buffer at the given offset.
        If offset is 0 or not supplied, returns an empty string.
        This handles the case where a symbol is anonymous."""
        if 0 in (base, offset):
            return ''
        pos = base + offset
        end = self.data.find(b'\0', pos)
        ret = self.data[pos:end].decode('ascii')
        if offset is None:
            self.cursor = end + 1
        return ret

    def align(self, alignment=4, *, out=False):
        """Update the internal cursor to align to a byte boundary.

        alignment must be a power of 2.
        If out is True, also pads the buffer."""
        mask = alignment - 1
        assert alignment & mask == 0
        new = (self.cursor + mask) & ~mask
        if new > self.cursor:
            if out:
                self.data += bytes(new - self.cursor)
            self.cursor = new

    def seek(self, pos: int, whence=os.SEEK_SET):
        """Update the internal cursor position. Behavior matches that of BinaryIO.seek.

        When whence == os.SEEK_SET: cursor is set to pos
        When whence == os.SEEK_CUR: pos is added to the cursor
        When whence == os.SEEK_END: cursor is set to pos less than the buffer length

        After the above logic, cursor is clamped to the buffer range."""
        if whence == os.SEEK_SET:
            new = pos
        elif whence == os.SEEK_CUR:
            new = self.cursor + pos
        elif whence == os.SEEK_END:
            new = len(self.data) - pos
        else:
            raise ValueError('unrecognized argument for "whence"')
        self.cursor = min(max(new, 0), len(self.data))

    def read_struct(self, struct: NamedStruct, base: int = None, offset: int = None) -> CStruct:
        """Reads a C struct from the SDAT at an offset.
        If offset is None (the default), the cursor is advanced."""
        if 0 in (base, offset):
            return None
        if base is not None and offset is not None:
            offset += base
        ret = struct.unpack_from(self.data, offset if offset is not None else self.cursor)
        if offset is None:
            self.cursor += struct.size
        return ret

    def read_array(self, struct: NamedStruct, base: int = None, offset: int = None) -> list[CStruct]:
        """Reads an array of C structs from the SDAT at an offset.
        If offset is None (the default), the cursor is advanced."""
        if 0 in (base, offset):
            return []
        if base is not None and offset is not None:
            offset += base
        ret = list(struct.unpack_array_from(self.data, offset if offset is not None else self.cursor))
        if offset is None:
            self.cursor += 4 + len(ret) * struct.size
        return ret

    def write_struct(self, obj: CStruct, offset: int = None):
        """Writes a single dataclass as a C object.
        If offset is None (the default), the object is appended to the buffer
        and the cursor is advanced."""
        if offset is None:
            self.data += obj.pack()
            self.cursor = len(self.data)
        else:
            obj.pack_into(self.data, offset)

    def write_array(self, objs: list[CStruct], offset: int = None):
        """Writes a list of dataclass as a C length-encoded array.
        If offset is None (the default), the object is appended to the buffer
        and the cursor is advanced."""
        assert offset != 0
        if not objs:
            self.write_long(offset, 0)
        else:
            cls: NamedStruct = objs[0].__class__
            if offset is None:
                self.data += cls.pack_array(objs)
                self.cursor = len(self.data)
            else:
                cls.pack_array_into(self.data, offset, objs)
