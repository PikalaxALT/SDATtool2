import argparse
import json
import typing
import os

from . import info
from .version import __version__
from .sdat_io import SdatIO
from .utils import Timer


f"""SDATtool2 convert between an SDAT file and its components.

For help, run python -m {os.path.dirname(__file__)} -h

Requires Python 3.9 or later
"""


class Namespace(argparse.Namespace):
    """A typed namespace containing the user-supplied args."""
    SDATfile: str
    folder: str = None
    mode: bool
    optimize: bool
    optimizeSize: bool
    optimizeRAM: bool
    noSymbBlock: bool

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SDAT: typing.Optional[SdatIO] = None

    def main_unpack(self):
        """The main logic for unpacking an SDAT into a directory tree"""
        print('Unpacking...')

        # Ensure the output directory exists
        os.makedirs(self.folder, exist_ok=True)

        # Read the SDAT file as a wrapped buffer
        with open(self.SDATfile, 'rb') as fp:
            self.SDAT = SdatIO(fp)

        # Read the header
        header = self.SDAT.read_struct(info.NNSSndArcHeader)

        # Read the symbol block
        if header.symbolDataOffset != 0:
            symb_header = self.SDAT.read_struct(info.NNSSndSymbolAndInfoOffsets, offset=header.symbolDataOffset)
            symbols = info.SymbolData.from_offsets(symb_header, header.symbolDataOffset, self.SDAT)
        else:
            symbols = None

        # Read the file block
        fat_header = self.SDAT.read_struct(info.NNSSndArcFat, offset=header.fatOffset)
        fat_entries = self.SDAT.read_array(info.NNSSndArcFileInfo, offset=header.fatOffset + fat_header.size)
        files = [x.read_file(header.fileImageOffset, self.SDAT) for x in fat_entries]

        # Read the info block
        info_header = self.SDAT.read_struct(info.NNSSndSymbolAndInfoOffsets, offset=header.infoOffset)
        infos = info.InfoData.from_offsets(info_header, header.infoOffset, self.SDAT)
        if symbols is not None:
            infos.set_symbols(symbols)

        # Dump the info block
        info_dict = infos.to_dict()
        with open(os.path.join(self.folder, 'Info.json'), 'w') as outf:
            json.dump(info_dict, outf, indent=4)

        # Dump the files
        infos.dump_files(files, self.folder)
        with open(os.path.join(self.folder, 'Files.json'), 'w') as outf:
            json.dump(infos.filenames, outf, indent=4)

    def main_build(self):
        """The main logic for building an SDAT from a directory tree"""
        print('Building...')
        raise NotImplementedError('SDAT building not yet implemented')

        # Create an empty SDAT buffer
        self.SDAT = SdatIO()
        ...

    def main(self):
        """The main logic of the program"""

        # Default io dir is the stem of the SDAT filename
        if self.folder is None:
            self.folder, _ = os.path.splitext(self.SDATfile)

        # Sanity checking
        assert self.folder != self.SDATfile, 'Input and output cannot match'

        # Branch the logic based on mode of operation
        method = self.main_build if self.mode else self.main_unpack
        with Timer(print=True) as t:
            method()


def sync_bool(dest2: str, *, const=True):
    """Returns an Action which synchronizes a Boolean option
    to a secondary Boolean option.
    Use the const kwarg to make this behave
    like store_true (const=True, default) or store_false (const=False)."""
    class SyncBool(argparse.Action):
        def __init__(self, option_strings, dest,  **kwargs):
            super().__init__(option_strings, dest, default=not const, const=const, **kwargs)

        def __call__(self, parser, namespace, value, option_string=None):
            super()(parser, namespace, value, option_string=option_string)
            setattr(namespace, dest2, self.const)

    return SyncBool


def assert_extension(ext: str):
    """Returns an Action which treats the argument as a filename,
    verifies its extension, but does not open the file."""
    class AssertExtension(argparse.Action):
        def __call__(self, parser, namespace, value, option_string=None):
            if not value.casefold().endswith(ext.casefold()):
                raise argparse.ArgumentError(self, f'{value} does not have required extension {ext}')
            super()(parser, namespace, value, option_string=option_string)


def main():
    parser = argparse.ArgumentParser(description=f"SDAT-Tool {__version__}: Unpack/Pack NDS SDAT Files")
    parser.add_argument("SDATfile", action=assert_extension('.sdat'))
    parser.add_argument("folder", nargs="?")
    mode_grp = parser.add_mutually_exclusive_group(required=True)
    mode_grp.add_argument("-u", "--unpack", dest="mode", action="store_false")
    mode_grp.add_argument("-b", "--build", dest="mode", action="store_true")
    parser.add_argument("-o", "--optimize", dest="optimize", action="store_true",
                        help="Remove unused and duplicate files")
    opt_grp = parser.add_mutually_exclusive_group()
    opt_grp.add_argument("-os", "--optimize_size", dest="optimizeSize", action=sync_bool('optimize'),
                         help="Build Optimized for filesize")
    opt_grp.add_argument("-or", "--optimize_ram", dest="optimizeRAM", action=sync_bool('optimize'),
                         help="Build Optimized for RAM")
    parser.add_argument("-ns", "--noSymbBlock", dest="noSymbBlock", action="store_true",
                        help="Build without a SymbBlock")
    args = parser.parse_args(namespace=Namespace())
    args.main()


if __name__ == '__main__':
    main()
