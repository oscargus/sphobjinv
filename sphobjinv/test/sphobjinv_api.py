# ------------------------------------------------------------------------------
# Name:        sphobjinv_api
# Purpose:     Module for sphobjinv API tests
#
# Author:      Brian Skinn
#                bskinn@alum.mit.edu
#
# Created:     18 Dec 2017
# Copyright:   (c) Brian Skinn 2016-2018
# License:     The MIT License; see "LICENSE.txt" for full license terms.
#
#            https://www.github.com/bskinn/sphobjinv
#
# ------------------------------------------------------------------------------

"""Module for sphobjinv API tests."""

import unittest as ut

from .sphobjinv_base import B_LINES_0, S_LINES_0
from .sphobjinv_base import DEC_EXT, CMP_EXT
from .sphobjinv_base import INIT_FNAME_BASE, MOD_FNAME_BASE
from .sphobjinv_base import RES_FNAME_BASE, INVALID_FNAME
from .sphobjinv_base import REMOTE_URL, P_INV, TESTALL
from .sphobjinv_base import SuperSphobjinv
from .sphobjinv_base import copy_dec, copy_cmp, scr_path, res_path
from .sphobjinv_base import decomp_cmp_test, file_exists_test
from .sphobjinv_base import sphinx_load_test


class TestSphobjinvAPIExpectGood(SuperSphobjinv, ut.TestCase):
    """Testing code accuracy under good params & expected behavior."""

    def test_API_SourceTypes_IterationCheck(self):
        """Confirm that SourceTypes iterates in the expected order."""
        import itertools as itt

        import sphobjinv as soi

        items = [soi.SourceTypes.Manual,
                 soi.SourceTypes.BytesPlaintext,
                 soi.SourceTypes.BytesZlib,
                 soi.SourceTypes.FnamePlaintext,
                 soi.SourceTypes.FnameZlib,
                 soi.SourceTypes.DictJSON,
                 soi.SourceTypes.URL,
                 ]

        for it, en in itt.zip_longest(items, soi.SourceTypes, fillvalue=None):
            with self.subTest(en.value if en else it.value):
                self.assertEqual(it, en)

    def test_API_CompressSucceeds(self):
        """Check that a compress attempt via API throws no errors."""
        import sphobjinv as soi

        # Populate scratch with the decompressed ref file
        copy_dec()

        # Store dest filename for reuse
        dest_fname = scr_path(MOD_FNAME_BASE + CMP_EXT)

        # See if it makes it all the way through the process without error
        with self.subTest('error_in_process'):
            try:
                b_dec = soi.readbytes(scr_path(INIT_FNAME_BASE + DEC_EXT))
                b_cmp = soi.compress(b_dec)
                soi.writebytes(dest_fname, b_cmp)
            except Exception:
                self.fail(msg='objects.txt compression failed.')

        # Simple assertion that compressed file now exists
        file_exists_test(self, dest_fname)

        # Seeing if sphinx actually likes the file
        sphinx_load_test(self, dest_fname)

    def test_API_DecompressSucceeds(self):
        """Check that a decomp attempt via API throws no errors."""
        import sphobjinv as soi

        # Populate scratch with compressed ref file
        copy_cmp()

        # Store target filename for reuse
        dest_fname = scr_path(MOD_FNAME_BASE + DEC_EXT)

        # See if the compress operation completes without error
        with self.subTest('error_in_process'):
            try:
                b_cmp = soi.readbytes(scr_path(INIT_FNAME_BASE + CMP_EXT))
                b_dec = soi.decompress(b_cmp)
                soi.writebytes(dest_fname, b_dec)
            except Exception:
                self.fail(msg='objects.inv decompression failed.')

        # Simple assertion of the existence of the decompressed file
        file_exists_test(self, dest_fname)

        # Testing compare w/original file
        decomp_cmp_test(self, dest_fname)

    def test_API_RegexDataCheck(self):
        """Confirm the regex for loading data lines is working properly."""
        import sphobjinv as soi

        # Populate scratch with the decompressed file
        copy_dec()

        # Read the file
        b_str = soi.fileops.readbytes(scr_path(INIT_FNAME_BASE + DEC_EXT))

        # Have to convert any DOS newlines REMOVE THIS
        b_str = b_str.replace(b'\r\n', b'\n')

        # A separate check shows 56 entries in the reference hive."""
        with self.subTest('entries_count'):
            self.assertEqual(56, len(soi.re.pb_data.findall(b_str)))

        # The first entry in the file is:
        #  attr.Attribute py:class 1 api.html#$ -
        # The third entry from the end is:
        #  slots std:label -1 examples.html#$ Slots
        elements = [0, -3]
        testdata = {soi.DataFields.Name: [b'attr.Attribute', b'slots'],
                    soi.DataFields.Domain: [b'py', b'std'],
                    soi.DataFields.Role: [b'class', b'label'],
                    soi.DataFields.Priority: [b'1', b'-1'],
                    soi.DataFields.URI: [b'api.html#$', b'examples.html#$'],
                    soi.DataFields.DispName: [b'-', b'Slots']}

        # Materialize the list of data line matches
        mchs = list(soi.re.pb_data.finditer(b_str))

        # Test each of the id-ed data lines
        for i, e in enumerate(elements):
            for df in soi.DataFields:
                with self.subTest('{0}_{1}'.format(df.value, e)):
                    self.assertEqual(mchs[e].group(df.value),
                                     testdata[df][i])

    def test_API_DataObjBytes_InitCheck(self):
        """Confirm the DataObjBytes type functions correctly."""
        import sphobjinv as soi

        # Pull .txt file and match first data line
        b_dec = soi.readbytes(res_path(RES_FNAME_BASE + DEC_EXT))
        mch = soi.pb_data.search(b_dec)
        b_mchdict = {_: mch.group(_) for _ in mch.groupdict()}
        s_mchdict = {_: b_mchdict[_].decode(encoding='utf-8')
                     for _ in b_mchdict}

        # Confirm DataObjBytes instantiates w/bytes
        with self.subTest('inst_bytes'):
            try:
                b_dob = soi.DataObjBytes(**b_mchdict)
            except Exception:
                self.fail('bytes instantiation failed')

        # Confirm DataObjBytes instantiates w/str
        with self.subTest('inst_str'):
            try:
                s_dob = soi.DataObjBytes(**s_mchdict)
            except Exception:
                self.fail('str instantiation failed')

        # Confirm members match
        for _ in b_mchdict:
            with self.subTest('match_' + _):
                self.assertEqual(getattr(b_dob, _),
                                 getattr(s_dob, _))

        # Confirm str-equivalents match
        for _ in b_mchdict:
            with self.subTest('str_equiv_' + _):
                self.assertEqual(getattr(b_dob, _),
                                 getattr(b_dob.as_str, _)
                                 .encode(encoding='utf-8'))

    def test_API_DataObjStr_InitCheck(self):
        """Confirm the DataObjStr type functions correctly."""
        import sphobjinv as soi

        # Pull .txt file and match first data line
        b_dec = soi.readbytes(res_path(RES_FNAME_BASE + DEC_EXT))
        mch = soi.pb_data.search(b_dec)
        b_mchdict = {_: mch.group(_) for _ in mch.groupdict()}
        s_mchdict = {_: b_mchdict[_].decode(encoding='utf-8')
                     for _ in b_mchdict}

        # Confirm DataObjStr instantiates w/bytes
        with self.subTest('inst_bytes'):
            try:
                b_dos = soi.DataObjStr(**b_mchdict)
            except Exception:
                self.fail('bytes instantiation failed')

        # Confirm DataObjStr instantiates w/str
        with self.subTest('inst_str'):
            try:
                s_dos = soi.DataObjStr(**s_mchdict)
            except Exception:
                self.fail('str instantiation failed')

        # Confirm members match
        for _ in s_mchdict:
            with self.subTest('match_' + _):
                self.assertEqual(getattr(b_dos, _),
                                 getattr(s_dos, _))

        # Confirm bytes-equivalents match
        for _ in s_mchdict:
            with self.subTest('str_equiv_' + _):
                self.assertEqual(getattr(s_dos, _),
                                 getattr(s_dos.as_bytes, _)
                                 .decode(encoding='utf-8'))

    def test_API_DataObjBytes_FlatDictFxn(self):
        """Confirm that flat dict generating function works."""
        import sphobjinv as soi

        # Pull .txt file and match first data line
        b_dec = soi.readbytes(res_path(RES_FNAME_BASE + DEC_EXT))
        mch = soi.pb_data.search(b_dec)

        # Extract the match information, stuff into a DataObjBytes
        # instance, and extract the flat_dict
        b_mchdict = {_: mch.group(_) for _ in mch.groupdict()}
        b_jsondict = soi.DataObjBytes(**b_mchdict).json_dict()

        # Check matchingness
        for _ in b_mchdict:
            with self.subTest(_):
                self.assertEqual(b_mchdict[_], b_jsondict[_])

    def test_API_DataObjStr_FlatDictFxn(self):
        """Confirm that flat dict generating function works."""
        import sphobjinv as soi

        # Pull .txt file and match first data line
        b_dec = soi.readbytes(res_path(RES_FNAME_BASE + DEC_EXT))
        mch = soi.pb_data.search(b_dec)

        # Extract the match information, stuff into a DataObjStr
        # instance, and extract the flat_dict
        b_mchdict = {_: mch.group(_) for _ in mch.groupdict()}
        s_jsondict = soi.DataObjStr(**b_mchdict).json_dict()

        # Check matchingness
        for _ in b_mchdict:
            with self.subTest(_):
                self.assertEqual(b_mchdict[_].decode(encoding='utf-8'),
                                 s_jsondict[_])

    # These methods testing data_line also implicitly test flat_dict
    def test_API_DataObjBytes_DataLineFxn(self):
        """Confirm that data line formatting function works."""
        from itertools import product

        import sphobjinv as soi

        # Generate and check data line as bytes, both expanded
        # and contracted, with both expanded/contracted flag
        for _, __ in product(B_LINES_0, repeat=2):  # True/False product
            dob = soi.DataObjBytes(**soi.pb_data.search(B_LINES_0[_])
                                   .groupdict())
            b_dl = dob.data_line(expand=__)
            with self.subTest(str(_) + '_expand_' + str(__)):
                self.assertEqual(b_dl, B_LINES_0[_ or __])

            b_dl = dob.data_line(contract=__)
            with self.subTest(str(_) + '_contract_' + str(__)):
                self.assertEqual(b_dl, B_LINES_0[_ and not __])

    def test_API_DataObjStr_DataLineFxn(self):
        """Confirm that data line formatting function works."""
        from itertools import product

        import sphobjinv as soi

        # Generate and check data line as str, both expanded
        # and contracted, with both expanded/contracted flag
        for _, __ in product(S_LINES_0, repeat=2):  # True/False product
            dos = soi.DataObjStr(**soi.p_data.search(S_LINES_0[_])
                                 .groupdict())
            s_dl = dos.data_line(expand=__)
            with self.subTest(str(_) + '_expand_' + str(__)):
                self.assertEqual(s_dl, S_LINES_0[_ or __])

    def test_API_DataObjStr_EvolveName(self):
        """Confirm evolving a new |str| instance works properly."""
        from sphobjinv import Inventory as Inv

        inv = Inv(res_path(RES_FNAME_BASE + CMP_EXT))
        obj = inv.objects[5]

        newname = 'foo'
        obj2 = obj.evolve(name=newname)

        for k in obj.json_dict():
            with self.subTest(k):
                if k == 'name':
                    self.assertEqual(obj2.name, newname)
                else:
                    self.assertEqual(getattr(obj, k), getattr(obj2, k))

    def test_API_DataObjBytes_EvolveName(self):
        """Confirm evolving a new |bytes| instance works properly."""
        from sphobjinv import Inventory as Inv

        inv = Inv(res_path(RES_FNAME_BASE + CMP_EXT))
        obj = inv.objects[5].as_bytes

        newname = b'foo'
        obj2 = obj.evolve(name=newname)

        for k in obj.json_dict():
            with self.subTest(k):
                if k == 'name':
                    self.assertEqual(obj2.name, newname)
                else:
                    self.assertEqual(getattr(obj, k), getattr(obj2, k))


class TestSphobjinvAPIInventoryExpectGood(SuperSphobjinv, ut.TestCase):
    """Testing Inventory code accuracy w/good params & expected behavior."""

    def test_API_Inventory_DefaultNoneInstantiation(self):
        """Confirm 'manual' instantiation with None."""
        import sphobjinv as soi

        inv = soi.Inventory()

        with self.subTest('project'):
            self.assertEqual(inv.project, None)

        with self.subTest('version'):
            self.assertEqual(inv.version, None)

        with self.subTest('count'):
            self.assertEqual(inv.count, 0)

        with self.subTest('source_type'):
            self.assertEqual(inv.source_type, soi.SourceTypes.Manual)

    def check_attrs_inventory(self, inv, st, subtest_id):
        """Encapsulate high-level consistency tests for Inventory objects."""
        with self.subTest('{0}_{1}_project'.format(subtest_id, st.value)):
            self.assertEqual(inv.project, 'attrs')

        with self.subTest('{0}_{1}_version'.format(subtest_id, st.value)):
            self.assertEqual(inv.version, '17.2')

        with self.subTest('{0}_{1}_count'.format(subtest_id, st.value)):
            self.assertEqual(inv.count, 56)

        with self.subTest('{0}_{1}_source_type'.format(subtest_id, st.value)):
            self.assertEqual(inv.source_type, st)

    def test_API_Inventory_TestMostImports(self):
        """Check all high-level modes for Inventory instantiation."""
        from sphobjinv import readbytes, Inventory as Inv, SourceTypes as ST
        from sphobjinv.data import _utf8_decode

        sources = {ST.BytesPlaintext:
                   readbytes(res_path(RES_FNAME_BASE + DEC_EXT)),
                   ST.BytesZlib:
                   readbytes(res_path(RES_FNAME_BASE + CMP_EXT)),
                   ST.FnamePlaintext:
                   res_path(RES_FNAME_BASE + DEC_EXT),
                   ST.FnameZlib:
                   res_path(RES_FNAME_BASE + CMP_EXT),
                   }

        for st in ST:
            if st in [ST.Manual, ST.DictJSON, ST.URL]:
                # Manual isn't tested
                # DictJSON is tested independently, to avoid crashing this
                #  test if something goes wrong in the generation & reimport.
                # URL is its own beast, tested in the separate Nonlocal
                #  class, below.
                continue

            self.check_attrs_inventory(Inv(sources[st]), st, 'general')

            if st == ST.BytesPlaintext:
                inv = Inv(plaintext=sources[st])
                self.check_attrs_inventory(inv, st, st.value)

                inv = Inv(plaintext=_utf8_decode(sources[st]))
                self.check_attrs_inventory(inv, st, st.value)

            if st == ST.BytesZlib:
                inv = Inv(zlib=sources[st])
                self.check_attrs_inventory(inv, st, st.value)

            if st == ST.FnamePlaintext:
                inv = Inv(fname_plain=sources[st])
                self.check_attrs_inventory(inv, st, st.value)

            if st == ST.FnameZlib:
                inv = Inv(fname_zlib=sources[st])
                self.check_attrs_inventory(inv, st, st.value)

    def test_API_Inventory_FlatDictJSONValidate(self):
        """Confirm that the flat_dict properties generated valid JSON."""
        import jsonschema

        import sphobjinv as soi

        inv = soi.Inventory(res_path(RES_FNAME_BASE + CMP_EXT))
        v = jsonschema.Draft4Validator(soi.json_schema)

        for prop in ['none', 'expand', 'contract']:
            kwarg = {} if prop == 'none' else {prop: True}
            with self.subTest(prop):
                try:
                    v.validate(inv.json_dict(**kwarg))
                except jsonschema.ValidationError:
                    self.fail("'{0}' JSON invalid".format(prop))

    def test_API_Inventory_FlatDictReimport(self):
        """Confirm re-import of a generated flat_dict."""
        from sphobjinv import Inventory, SourceTypes

        inv = Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        inv = Inventory(inv.json_dict())

        self.check_attrs_inventory(inv, SourceTypes.DictJSON, 'general')

    def test_API_Inventory_FlatDictReimportWithMetadata(self):
        """Confirm re-import of a generated flat_dict."""
        from sphobjinv import Inventory, SourceTypes

        inv = Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        d = inv.json_dict()

        d.update({'metadata': 'test string'})

        with self.subTest('instantiate_metadata_string'):
            try:
                inv = Inventory(d)
            except Exception:
                self.fail('Failed when instantiating with string metadata')

        self.check_attrs_inventory(inv, SourceTypes.DictJSON,
                                   'contents_metadata_string')

        d.update({'metadata': {'this': 'foo', 'that': 'bar'}})

        with self.subTest('instantiate_metadata_dict'):
            try:
                inv = Inventory(d)
            except Exception:
                self.fail('Failed when instantiating with dict metadata')

        self.check_attrs_inventory(inv, SourceTypes.DictJSON,
                                   'contents_metadata_dict')

        d.update({'metadata': 42})

        with self.subTest('instantiate_metadata_int'):
            try:
                inv = Inventory(d)
            except Exception:
                self.fail('Failed when instantiating with int metadata')

        self.check_attrs_inventory(inv, SourceTypes.DictJSON,
                                   'contents_metadata_int')

    def test_API_Inventory_TooSmallFlatDictImportButIgnore(self):
        """Confirm no error when flat dict passed w/too few objs w/ignore."""
        import sphobjinv as soi

        inv = soi.Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        d = inv.json_dict()
        d.pop('12')

        inv2 = soi.Inventory(d, count_error=False)

        # 55 b/c the loop continues past missing elements
        self.assertEqual(inv2.count, 55)

    def test_API_Inventory_DataFileGenAndReimport(self):
        """Confirm integrated data_file export/import behavior."""
        import os

        import sphobjinv as soi

        for fn in os.listdir(res_path()):
            # Drop unless testall
            if (not os.environ.get(TESTALL, False) and
                    fn != 'objects_attrs.inv'):
                continue

            if fn.startswith('objects_') and fn.endswith('.inv'):
                # Make Inventory
                mch = P_INV.match(fn)
                proj = mch.group(1)
                inv1 = soi.Inventory(res_path(fn))

                # Generate new zlib file and reimport
                data = inv1.data_file()
                cmp_data = soi.compress(data)
                soi.writebytes(scr_path(fn), cmp_data)
                inv2 = soi.Inventory(scr_path(fn))

                # Test the things
                with self.subTest(proj + '_project'):
                    self.assertEqual(inv1.project, inv2.project)
                with self.subTest(proj + '_version'):
                    self.assertEqual(inv1.version, inv2.version)
                with self.subTest(proj + '_count'):
                    self.assertEqual(inv1.count, inv2.count)

                # Only check objects if counts match
                if inv1.count == inv2.count:
                    for i, objs in enumerate(zip(inv1.objects,
                                                 inv2.objects)):
                        with self.subTest(proj + '_obj' + str(i)):
                            self.assertEqual(objs[0].name,
                                             objs[1].name)
                            self.assertEqual(objs[0].domain,
                                             objs[1].domain)
                            self.assertEqual(objs[0].role,
                                             objs[1].role)
                            self.assertEqual(objs[0].uri,
                                             objs[1].uri)
                            self.assertEqual(objs[0].priority,
                                             objs[1].priority)
                            self.assertEqual(objs[0].dispname,
                                             objs[1].dispname)

    def test_API_Inventory_DataFileGenAndSphinxLoad(self):
        """Confirm Sphinx likes generated inventory files."""
        import os

        import sphobjinv as soi

        for fn in os.listdir(res_path()):
            # Drop unless testall
            if (not os.environ.get(TESTALL, False) and
                    fn != 'objects_attrs.inv'):
                continue

            if fn.startswith('objects_') and fn.endswith('.inv'):
                # Make Inventory
                mch = P_INV.match(fn)
                proj = mch.group(1)
                inv1 = soi.Inventory(res_path(fn))

                # Generate new zlib file
                data = inv1.data_file()
                cmp_data = soi.compress(data)
                soi.writebytes(scr_path(fn), cmp_data)

                # Test the Sphinx load process
                with self.subTest(proj):
                    sphinx_load_test(self, scr_path(fn))

    def test_API_Inventory_NameSuggest(self):
        """Confirm object name suggestion is nominally working."""
        from numbers import Number

        import sphobjinv as soi

        rst = ':py:function:`attr.evolve`'
        idx = 6

        inv = soi.Inventory(res_path(RES_FNAME_BASE + CMP_EXT))

        # No test on the exact fuzzywuzzy match score in these since
        # it could change as fw continues development
        rec = inv.suggest('evolve')

        with self.subTest('plain'):
            self.assertEqual(rec[0], rst)

        rec = inv.suggest('evolve', with_index=True)

        with self.subTest('with_index'):
            self.assertEqual(rec[0][0], rst)
            self.assertEqual(rec[0][1], idx)

        rec = inv.suggest('evolve', with_score=True)

        with self.subTest('with_score'):
            self.assertEqual(rec[0][0], rst)
            self.assertIsInstance(rec[0][1], Number)

        rec = inv.suggest('evolve', with_index=True, with_score=True)

        with self.subTest('with_both'):
            self.assertEqual(rec[0][0], rst)
            self.assertIsInstance(rec[0][1], Number)
            self.assertEqual(rec[0][2], idx)

    def test_API_FuzzyWuzzy_WarningCheck(self):
        """Confirm only the Levenshtein warning is raised, if any are."""
        import warnings

        with warnings.catch_warnings(record=True) as wc:
            warnings.simplefilter("always")
            from fuzzywuzzy import process

            process.__doc__  # Stop flake8 unused import complaint

        # Try to import, and adjust tests accordingly
        try:
            import Levenshtein
            Levenshtein.__doc__  # Stop flake8 complaint
        except ImportError:
            lev_present = False
        else:
            lev_present = True

        if lev_present:
            with self.subTest('count_Lev_present'):  # pragma: no cover
                self.assertEqual(len(wc), 0)

        else:
            with self.subTest('count_Lev_absent'):
                self.assertEqual(len(wc), 1)

            with self.subTest('identity_Lev_absent'):
                # 'message' will be a Warning instance, thus 'args[0]'
                # to retrieve the warning message as str.
                self.assertIn('levenshtein', wc[0].message.args[0].lower())


class TestSphobjinvAPIInvGoodNonlocal(SuperSphobjinv, ut.TestCase):
    """Testing Inventory URL download import method.

    The test in this class is SLOW. For routine testing work, invoke tests.py
    with '--local', rather than '--all', to avoid running it.

    """

    def test_API_Inventory_ManyURLImports(self):
        """Confirm a plethora of .inv files downloads properly via url arg."""
        import os

        from sphobjinv import Inventory as Inv

        for fn in os.listdir(res_path()):
            # Drop unless testall
            if (not os.environ.get(TESTALL, False) and
                    fn != 'objects_attrs.inv'):
                continue

            mch = P_INV.match(fn)
            if mch is not None:
                name = mch.group(1)
                inv1 = Inv(res_path(fn))
                inv2 = Inv(url=REMOTE_URL.format(name))
                with self.subTest(name + '_project'):
                    self.assertEqual(inv1.project, inv2.project)
                with self.subTest(name + '_version'):
                    self.assertEqual(inv1.version, inv2.version)
                with self.subTest(name + '_count'):
                    self.assertEqual(inv1.count, inv2.count)

                # Only check objects if counts match
                if inv1.count == inv2.count:
                    for i, objs in enumerate(zip(inv1.objects,
                                                 inv2.objects)):
                        with self.subTest(name + '_obj' + str(i)):
                            self.assertEqual(objs[0].name,
                                             objs[1].name)
                            self.assertEqual(objs[0].domain,
                                             objs[1].domain)
                            self.assertEqual(objs[0].role,
                                             objs[1].role)
                            self.assertEqual(objs[0].uri,
                                             objs[1].uri)
                            self.assertEqual(objs[0].priority,
                                             objs[1].priority)
                            self.assertEqual(objs[0].dispname,
                                             objs[1].dispname)

    @ut.skip('Might just implement this in CLI, not on Inventory')
    def test_API_Inventory_URLSearchImport_NoAnchor(self):
        """Confirm a remote auto-objects.inv search w/o anchor works.

        Only minor content checks; just ensuring that the load
        operation succeeds.

        """
        from sphobjinv import Inventory as Inv

        URL = 'https://docs.python.org/3.5/library/functions.html'

        try:
            Inv(url=URL)
        except Exception:
            self.fail(msg="Webpage URL search w/o anchor failed.")

    @ut.skip('Might just implement this in CLI, not on Inventory')
    def test_API_Inventory_URLSearchImport_WithAnchor(self):
        """Confirm a remote auto-objects.inv search WITH anchor works.

        Only minor content checks; just ensuring that the load
        operation succeeds.

        """
        from sphobjinv import Inventory as Inv

        URL = ('https://docs.python.org/3.5/library/'
               'functions.html#built-in-funcs')

        try:
            Inv(url=URL)
        except Exception:
            self.fail(msg="Webpage URL search with anchor failed.")


class TestSphobjinvAPIExpectFail(SuperSphobjinv, ut.TestCase):
    """Testing that code raises expected errors when invoked improperly."""

    def test_API_NoInputFile(self):
        """Confirm that appropriate exceptions are raised w/no input file."""
        import sphobjinv as soi

        with self.subTest('decomp_input_file'):
            with self.assertRaises(FileNotFoundError):
                soi.readbytes(INIT_FNAME_BASE + DEC_EXT)

        with self.subTest('comp_input_file'):
            with self.assertRaises(FileNotFoundError):
                soi.readbytes(INIT_FNAME_BASE + CMP_EXT)

    def test_API_WriteFileBadOutputFile(self):
        """Confirm OSError raised on bad filename (example of read error)."""
        import sphobjinv as soi

        b_str = b'This is a binary string!'

        with self.assertRaises(OSError):
            soi.writebytes(INVALID_FNAME, b_str)

    def test_API_ErrorDecompressingPlaintext(self):
        """Confirm error raised on attempt to decompress plaintext."""
        from zlib import error as ZlibError

        import sphobjinv as soi

        # OS-dependent. VersionError on Windows b/c bytes import of the
        # text-file objects_attrs.txt has the first line ending with b'2\r\n',
        # whereas *nix will pass the version check but choke in the zlib
        # decompression process
        self.assertRaises((ZlibError, soi.VersionError),
                          soi.Inventory,
                          fname_zlib=res_path(RES_FNAME_BASE + DEC_EXT))

    def test_API_BadDataObjInitTypes(self):
        """Confirm error raised when init-ed w/wrong types."""
        import sphobjinv as soi

        with self.subTest('bytes'):
            with self.assertRaises(TypeError):
                soi.DataObjBytes(*range(6))

        with self.subTest('str'):
            with self.assertRaises(TypeError):
                soi.DataObjStr(*range(6))

    @ut.skip('Changed to mutable to avoid Inventory revision pain.')
    def test_API_ChangingImmutableDataObj(self):
        """Confirm DataObj's are immutable."""
        from attr.exceptions import FrozenInstanceError as FIError

        from sphobjinv import Inventory as Inv

        inv = Inv(res_path(RES_FNAME_BASE + CMP_EXT))

        with self.subTest('str'):
            with self.assertRaises(FIError):
                inv.objects[0].name = 'newname'
        with self.subTest('bytes'):
            with self.assertRaises(FIError):
                inv.objects[0].as_bytes.name = b'newname'

    def test_API_DataLine_BothArgsTrue(self):
        """Confirm error raised when both expand and contract are True."""
        import sphobjinv as soi

        dos = soi.DataObjStr(**soi.p_data.search(S_LINES_0[True])
                             .groupdict())
        with self.assertRaises(ValueError):
            dos.data_line(expand=True, contract=True)

    def test_API_Inventory_InvalidSource(self):
        """Confirm error raised when invalid source provided."""
        import sphobjinv as soi

        with self.assertRaises(TypeError):
            soi.Inventory('abcdefg')

    def test_API_Inventory_NoItemsFlatDict(self):
        """Confirm TypeError with no-items dict passed to json_dict."""
        import sphobjinv as soi

        d = {soi.HeaderFields.Project.value: 'proj',
             soi.HeaderFields.Version.value: 'v3.3',
             soi.HeaderFields.Count.value: 5}

        self.assertRaises(TypeError, soi.Inventory._import_json_dict, d)

    def test_API_Inventory_TooSmallDictImport(self):
        """Confirm error raised when JSON dict passed w/too few objects."""
        import sphobjinv as soi

        inv = soi.Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        d = inv.json_dict()
        d.pop('12')

        self.assertRaises(ValueError, soi.Inventory, d)

    def test_API_Inventory_BadObjDictImport(self):
        """Confirm error raised when JSON dict passed w/an invalid object."""
        from jsonschema.exceptions import ValidationError
        import sphobjinv as soi

        inv = soi.Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        d = inv.json_dict()
        d.update({'112': 'foobarbazquux'})

        self.assertRaises(ValidationError, soi.Inventory, dict_json=d)

    def test_API_Inventory_TooBigJSONDictImport(self):
        """Confirm error raised when JSON dict passed w/too many objects."""
        import sphobjinv as soi

        inv = soi.Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        d = inv.json_dict()
        d.update({'57': d['23']})

        self.assertRaises(ValueError, soi.Inventory, dict_json=d)

    def test_API_Inventory_BadRootObjectJSONDictImport(self):
        """Confirm error raised when spurious extra root object present."""
        import sphobjinv as soi
        from jsonschema.exceptions import ValidationError

        inv = soi.Inventory(res_path(RES_FNAME_BASE + DEC_EXT))
        d = inv.json_dict()
        d.update({'bad_foo': 'angry_bar'})

        self.assertRaises(ValidationError, soi.Inventory, dict_json=d)

    def test_API_Inventory_TooManyInitSrcArgs(self):
        """Confirm error if >1 sources passed."""
        from sphobjinv import Inventory

        self.assertRaises(RuntimeError, Inventory,
                          source='foo', plaintext='bar')

    def test_API_Inventory_NoObjectInventories(self):
        """Confirm no-objects inventories don't import."""
        import sphobjinv as soi

        inv = soi.Inventory()

        with self.subTest('plain'):
            self.assertRaises(TypeError, soi.Inventory, inv.data_file())

        with self.subTest('zlib'):
            # Actually testing that importing an empty inventory
            # blows up, not importing one
            self.assertRaises((TypeError, ValueError),
                              soi.Inventory,
                              soi.compress(inv.data_file()))

        d = {'project': 'test', 'version': '0.0', 'count': 0}
        with self.subTest('json'):
            self.assertRaises(ValueError, soi.Inventory, d)


def suite_api_expect_good():
    """Create and return the test suite for API expect-good cases."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestSphobjinvAPIExpectGood),
                tl.loadTestsFromTestCase(TestSphobjinvAPIInventoryExpectGood)])

    return s


def suite_api_expect_good_nonlocal():
    """Create and return the test suite for nonlocal API expect-good cases."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestSphobjinvAPIInvGoodNonlocal)])

    return s


def suite_api_expect_fail():
    """Create and return the test suite for API expect-fail cases."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestSphobjinvAPIExpectFail)])

    return s


if __name__ == '__main__':
    print("Module not executable.")
