import typing
import enum
import os
from named_struct import NamedStruct, DataClass


class FileType(typing.NamedTuple):
    """Data class for SDAT member filetypes."""
    ext: str = ''
    header: bytes = b''


file_types = [
    FileType('.sseq', b'SSEQ'),
    FileType('.ssar', b'SSAR'),
    FileType('.sbnk', b'SBNK'),
    FileType('.swar', b'SWAR'),
    FileType(),
    FileType(),
    FileType(),
    FileType('.strm', b'STRM'),
    FileType(),
]


class InfoType(enum.Enum):
    """Enum for SDAT member types"""
    SEQ = 0
    SEQARC = 1
    BANK = 2
    WAVARC = 3
    PLAYER = 4
    GROUP = 5
    PLAYER2 = 6
    STRM = 7
    FILE = 8

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
        self.names: list[list[str]] = [[] for _ in InfoType]
        self.filename_id: list[int] = []
        self.file_types: list[InfoType] = []

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

    def read_item_name(self, listitem: InfoType):
        """Reads the name of the item referenced in data, and advances the cursor.
        If the name is not loaded, generates one.

        listitem declares what type of symbol you want."""
        index = self.read_short(self.cursor)
        try:
            ret = self.names[listitem.value][index]
        except IndexError:
            ret = '' if index == 0xFFFF and listitem is InfoType.WAVARC else f'{listitem.name}_{index}'
        self.cursor += 1 if listitem is InfoType.PLAYER else 2
        return ret

    def read_filename(self):
        """Reads a file ID and fetches the host FS filename"""
        index = self.read_short()
        try:
            real_index = self.filename_id.index(index)
        except ValueError:
            real_index = len(self.filename_id)
        return self.names[InfoType.FILE.value][real_index] + self.file_types[real_index].file_type.ext

    def get_string(self):
        """Reads a string from the buffer and advances the cursor to the byte past the null terminator.
        Returns the string that was read."""
        end = self.data.find(b'\0', self.cursor)
        ret = self.data[self.cursor:end].decode('ascii')
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

    def read_struct(self, struct: NamedStruct, offset: int = None):
        """Reads a C struct from the SDAT at an offset.
        If offset is None (the default), the cursor is advanced."""
        ret = struct.unpack_from(self.data, offset if offset is not None else self.cursor)
        if offset is None:
            self.cursor += struct.size
        return ret

    def read_array(self, struct: NamedStruct, offset: int = None):
        """Reads an array of C structs from the SDAT at an offset.
        If offset is None (the default), the cursor is advanced."""
        ret = list(struct.unpack_array_from(self.data, offset if offset is not None else self.cursor))
        if offset is None:
            self.cursor += 4 + len(ret) * struct.size
        return ret

    def write_struct(self, struct: NamedStruct, obj: DataClass, offset: int = None):
        if offset is None:
            self.data += struct.pack(obj)
