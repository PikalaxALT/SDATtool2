import argparse
import typing

from version import __version__
from sdat_io import SdatIO


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
        with open(self.SDATfile, 'rb') as fp:
            self.SDAT = SdatIO(fp)

    def main_build(self):
        """The main logic for building an SDAT from a directory tree"""
        self.SDAT = SdatIO()

    def main(self):
        """The main logic of the program"""
        if self.mode:
            self.main_build()
        else:
            self.main_unpack()


def sync_bool(dest2, *, const=True):
    """Returns an Action which synchronizes a Boolean option
    to a secondary Boolean option.
    Use the const kwarg to make this behave
    like store_true (const=True, default) or store_false (const=False)."""
    class SyncBool(argparse.Action):
        def __init__(self, option_strings, dest,  **kwargs):
            super().__init__(option_strings, dest, default=not const, const=const, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            super()(parser, namespace, values, option_string=option_string)
            setattr(namespace, dest2, self.const)

    return SyncBool


def main():
    parser = argparse.ArgumentParser(description=f"SDAT-Tool {__version__}: Unpack/Pack NDS SDAT Files")
    parser.add_argument("SDATfile")
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
