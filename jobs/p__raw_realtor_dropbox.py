from utils.database_utils import backup_table
from db2pq import db_to_pq

from dotenv import load_dotenv
def backup_tables_to_dropbox():
    
    backup_table("realtor__sold", 
                    'raw',
                    'realtor_sold',
                    'real_estate_data')
    
    backup_table("realtor__for_rent",
                 "raw",
                 'realtor_for_rent',
                 'real_estate_data')
    pq_file = db_to_pq(
    table_name="here__traffic_flows",
    schema="raw",
    host="localhost",
    database="bigfoot"
    )

    print(pq_file)
    
    """
    backup_table("here__traffic_flows",
                 "raw",
                 "here_traffic",
                 "real_estate_data")
    """
    
if __name__ == "__main__":
    load_dotenv()
    backup_tables_to_dropbox()
