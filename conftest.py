r"""*Root conftest for* ``sphobjinv``.

``sphobjinv`` is a toolkit for manipulation and inspection of
Sphinx |objects.inv| files.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    20 Mar 2019

**Copyright**
    \(c) Brian Skinn 2016-2019

**Source Repository**
    http://www.github.com/bskinn/sphobjinv

**Documentation**
    http://sphobjinv.readthedocs.io

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

"""


import os.path as osp
import re
import shutil
import sys
from enum import Enum
from filecmp import cmp
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--testall",
        action="store_true",
        help="Test *all* inventories stored in testing resource folder",
    )


@pytest.fixture(scope="session")
def res_path():
    return Path(".") / "tests" / "resource"


@pytest.fixture(scope="session")
def misc_info(res_path):
    class Info:
        class FNames(Enum):
            RES_FNAME_BASE = "objects_attrs"
            INIT_FNAME_BASE = "objects"
            MOD_FNAME_BASE = "objects_mod"

        class Extensions(Enum):
            CMP_EXT = ".inv"
            DEC_EXT = ".txt"
            JSON_EXT = ".json"

        invalid_filename = "*?*?.txt" if sys.platform == "win32" else "/"

        # Sample object lines lines from an inventory, as bytes
        # False --> contracted abbreviations
        # True  --> expanded abbreviations
        byte_lines = {
            False: b"attr.Attribute py:class 1 api.html#$ -",
            True: b"attr.Attribute py:class 1 api.html#attr.Attribute attr.Attribute",
        }

        # For the URL mode of Inventory instantiation
        remote_url = (
            "https://github.com/bskinn/sphobjinv/raw/dev/sphobjinv/"
            "test/resource/objects_{0}.inv"
        )

        # Regex pattern for objects_xyz.inv files
        p_inv = re.compile(r"objects_([^.]+)\.inv", re.I)

    # Standard location for decompressed object in resource folder,
    # for comparison to a freshly generated decompressed file
    Info.res_decomp_path = res_path / (
        Info.FNames.RES_FNAME_BASE.value + Info.Extensions.DEC_EXT.value
    )

    # String version of the sample object lines
    Info.str_lines = {
        _: Info.byte_lines[_].decode("utf-8") for _ in Info.byte_lines
    }

    return Info


@pytest.fixture()
def scratch_dir(tmp_path, res_path, misc_info):
    for ext in [_.value for _ in misc_info.Extensions]:
        shutil.copy(
            str(res_path / "objects_attrs{}".format(ext)), str(tmp_path)
        )

    yield tmp_path


@pytest.fixture(scope="session")
def sphinx_load_test():
    """Return function to perform 'live' Sphinx inventory load test."""

    from sphinx.util.inventory import InventoryFile as IFile

    def func(path):
        # Easier to have the file open the whole time
        with path.open("rb") as f:

            # Attempt the load operation
            try:
                IFile.load(f, "", osp.join)
            except Exception as e:
                pytest.fail(e)

    return func


@pytest.fixture()  # Must be function scope since uses monkeypatch
def run_cmdline_test(monkeypatch):
    """Return function to perform command line exit code test."""
    from sphobjinv.cmdline import main

    def func(arglist, *, expect=0):  # , suffix=None):

        # Assemble execution arguments
        runargs = ["sphobjinv"]
        runargs.extend(arglist)

        # Mock sys.argv, run main, and restore sys.argv
        with monkeypatch.context() as m:
            m.setattr(sys, "argv", runargs)

            try:
                main()
            except SystemExit as e:
                retcode = e.args[0]
                ok = True
            else:
                ok = False

        # Do all pytesty stuff outside monkeypatch context
        assert ok, "SystemExit not raised on termination."

        # Test that execution completed w/indicated exit code
        assert retcode == expect

    return func


@pytest.fixture(scope="session")
def decomp_cmp_test(misc_info):
    """Return function to confirm indicated decompressed file is identical to resource."""

    def func(path):
        assert cmp(str(misc_info.res_decomp_path), str(path), shallow=False)

    return func
