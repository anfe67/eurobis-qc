import sys

from dbworks import sqlite_db_functions
from eurobisqc.util import qc_flags

this = sys.modules[__name__]

# Return values for when the quality check fails
qc_mask_1 = qc_flags.QCFlag.REQUIRED_FIELDS_PRESENT.bitmask
qc_mask_10 = qc_flags.QCFlag.OBIS_DATAFORMAT_OK.bitmask

this.lookups_loaded = False

this.required_fields = {}

this.recommended_fields = {}  # Decide whether to do something with these

this.values_basis_of_record = {}

this.vocab = {}  # When lowercase only has to be used for presence verification

# When Using lowercase for field names
this.fields_to_compare = {}


# Improved QC for sex
def initialize_lookups():
    """ Only needed at the first call to initialize the lookup tables """

    if this.lookups_loaded:
        return

    # row factory - BEWARE - do not use con.row_factory as !
    # db_functions.conn.row_factory = lambda cursor, row: row[0] # important, this has side effects
    # Fill the lookups:

    # COUNT IDs and words
    c = sqlite_db_functions.conn.cursor()
    data = c.execute('SELECT Value FROM requiredFields').fetchall()
    this.required_fields = {val[0] for val in data}

    c = sqlite_db_functions.conn.cursor()
    data = c.execute('SELECT Value FROM recommendedFields').fetchall()
    this.recommended_fields = {val[0] for val in data}

    # SAMPLE SIZE IDs and words
    c = sqlite_db_functions.conn.cursor()
    data = c.execute('SELECT Value FROM basisOfRecordValues').fetchall()
    this.values_basis_of_record = {val[0] for val in data}

    this.vocab = {value.lower() for value in this.values_basis_of_record}
    this.fields_to_compare = {value.lower() for value in this.required_fields}

    this.lookups_loaded = True


def check_record_required(record, option=False):
    """ Check for presence of required fields, as per reference. This corresponds to QC1.
        Optionally look at a set of recommended fields
        :param record: The record to QC
        :param option: Recommended fields are verified or not
    """

    qc_mask = 0

    # It shall be done only once on the first entry
    if not this.lookups_loaded:
        initialize_lookups()

    # Field names are checked in lowercase (case insensitive)
    present_fields = set(record.keys())  # set(record.keys())

    # May be it can be done differently (faster)
    present_required_fields = present_fields.intersection(this.required_fields)

    if len(present_required_fields) == len(this.required_fields):
        # Looking at the checks from obis-qc, verify that fields are present but also that they are not None
        count = 0
        for required_field in this.required_fields:
            count += 1
            if record[required_field] is None:
                break  # No need to proceed

        if count == len(this.required_fields):
            qc_mask |= qc_mask_1
    # else:
    #     qc_mask |= qc_mask_1
    # An option to be pedantic and require presence of the optional fields
    if option:
        present_optional_fields = present_fields.intersection(this.recommended_fields)
        if len(present_optional_fields) == len(this.recommended_fields):
            count = 0
            for optional_field in this.recommended_fields:
                count += 1
                if record[optional_field] is None:
                    break  # No need to proceed

            if count == len(this.recommended_fields):
                qc_mask |= qc_mask_1

    return qc_mask


def check_record_obis_format(record):
    """ To be called for source type records
        :param record:
    """
    qc_mask = 0

    # QC 10
    if "basisOfRecord" in record and record["basisOfRecord"] is not None:
        if record["basisOfRecord"].lower() in this.vocab:
            qc_mask |= qc_mask_10
    # else:
    #     qc_mask |= qc_mask_10

    return qc_mask


def check_obis(records):
    """ To be called for a batch of records (list)
        :param records:
        it shall return the results of QC 10
    """

    return [check_record_obis_format(record) for record in records]


def check_required(records):
    """ To be called for a batch of records (list)
        :param records:
        it shall return the results of QC 1
        """

    return [check_record_required(record) for record in records]


def check(records):
    """ To be called for a batch of records (list)
        :param records:
        it shall return the results of QC 1 combined with QC 10 (saves some looping)
        """

    return [check_record_required(record) | check_record_obis_format(record) for record in records]


def check_aggregate(records):
    """ Event record depend on their occurrence records to verify that all the required fields are present
        this is the full set of event + occurrences of which the non-none fields, part of the required fields set
        shall be checked upon.
        :param records
        :returns a QC value for the REQUIRED_FIELDS mask calculated across all the records in the list """

    qc_required_fields = {value: 0 for value in this.required_fields}

    qc_calc = 1
    for record in records:
        qc_calc = 1
        present_fields = set(record.keys())  # set(record.keys())

        # May be it can be done differently (faster)
        present_required_fields = present_fields.intersection(this.required_fields)
        for required_field in present_required_fields:
            if record[required_field] is not None:
                qc_required_fields[required_field] = 1

        for value in qc_required_fields.values():
            qc_calc &= value
            if not value:
                break

        if qc_calc:
            break

    return qc_calc
