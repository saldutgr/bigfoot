from utils.database_utils import backup_table

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
    
if __name__ == "__main__":
    load_dotenv()
    backup_tables_to_dropbox()
