""" Runs QC Processing on the entire database  """

import sys
import logging
from eurobisqc.examples import mssql_pipeline
from eurobisqc.examples import mssql_multiprocess
from dbworks import mssql_db_functions

this = sys.modules[__name__]
this.logger = logging.getLogger(__name__)
this.logger.setLevel(logging.DEBUG)
this.logger.addHandler(logging.StreamHandler())

# query the dataset on entering and stores the datasets ...
this.sql_all_datasets = f"SELECT d.id, d.displayname FROM  dataproviders d inner join eurobis e " \
                        f"on d.id = e.dataprovider_id " \
                        f"GROUP BY d.id, d.displayname ORDER BY d.id "

this.dataset_ids = []
this.dataset_names = []

this.exit = False


def grab_datasets(sql_string):
    """ Queries the database to retrieve a list of all datasets with records
        in eurobis IMPORTANT, datasets are sorted """
    if mssql_db_functions.conn is None:
        this.conn = mssql_db_functions.open_db()

    if this.conn is not None:
        cursor = this.conn.cursor()
        cursor.execute(sql_string)
        # Should extract something meaningful from the dataset...
        for row in cursor:
            this.dataset_ids.append(row[0])
            this.dataset_names.append(row[1])
    else:
        this.logger.error("No DB connection!")
        exit(0)


def process_all_db(with_multi_process=True, with_logging=False):
    """ Processes the entire DB either using multiprocessing or not """
    grab_datasets(this.sql_all_datasets)

    if with_multi_process:
        mssql_multiprocess.do_db_multi_selection(this.dataset_ids, this.dataset_names)
    else:
        mssql_pipeline.process_dataset_list(0, this.dataset_ids, False, with_logging)