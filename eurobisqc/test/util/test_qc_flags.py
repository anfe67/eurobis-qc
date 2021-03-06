import sys
import logging

from unittest import TestCase
from eurobisqc.qc_flags import QCFlag

this = sys.modules[__name__]
this.logger = logging.getLogger(__name__)

this.logger.setLevel(logging.DEBUG)
this.logger.addHandler(logging.StreamHandler())


class TestQCFlag(TestCase):

    def test_encode(self):
        for qc_flag in QCFlag:
            try:
                this.logger.info(qc_flag.encode(qc_flag.qc_number))
            except ValueError:
                self.fail()

    def test_decode_message(self):
        i = 0
        for qc_flag in QCFlag:
            try:
                this.logger.info(qc_flag.decode_message(i))
                i += 1
            except TypeError:
                self.fail()

    def test_decode_name(self):
        i = 0
        for qc_flag in QCFlag:
            try:
                this.logger.info(qc_flag.decode_name(i))
                i += 1
            except TypeError:
                self.fail()

    def test_decode_mask(self):
        test_mask = 1048575
        try:
            flags = QCFlag.decode_mask(test_mask)
            this.logger.info(flags)
        except (ValueError, TypeError):
            self.fail()

        self.assertTrue(flags[0] != 'INVALID')
        self.assertTrue(flags[-1] == 'DEPTH_FOR_SPECIES_OK')

    def test_encode_qc(self):
        record1 = {'id': 1, 'QC': 2}  # Record with QC
        record2 = {'id': 2}  # No QC
        record3 = "Just a fake"  # This is not a record

        error_bitmask = 1 << 3
        result = QCFlag.encode_qc(record1, error_bitmask)
        self.assertTrue(result['QC'] == 2 | error_bitmask)
        result = QCFlag.encode_qc(record2, error_bitmask)
        self.assertTrue(result['QC'] == error_bitmask)
        result = QCFlag.encode_qc(record3, error_bitmask)
        self.assertTrue(result is None)
