import utils.dropbox_utils
from utils.dropbox_utils import backup_table, clear_dropbox_folder, connect_to_dropbox

import argparse
from dotenv import load_dotenv
from utils.database_utils import add_postgres_arguments


def backup_tables_to_dropbox(port=None, database=None):
    #clear existing files and upload new
    
    clear_dropbox_folder('/real_estate_data')

    backup_table("realtor__sold", 
                    'raw',
                    'realtor_sold',
                    'real_estate_data',
                    port=port,
                    database=database)
    
    backup_table("realtor__for_rent",
                 "raw",
                 'realtor_for_rent',
                 'real_estate_data',
                 port=port,
                 database=database)
    
if __name__ == "__main__":
    parser = add_postgres_arguments(argparse.ArgumentParser())
    args = parser.parse_args()
    load_dotenv()
    #clear_dropbox_folder('/real_estate_data')
    backup_tables_to_dropbox(port=args.port, database=args.database)
