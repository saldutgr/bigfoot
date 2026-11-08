import utils.dropbox_utils
from utils.dropbox_utils import backup_table, clear_dropbox_folder, connect_to_dropbox

from dotenv import load_dotenv

def backup_tables_to_dropbox():
    #clear existing files and upload new
    
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
    clear_dropbox_folder('/real_estate_data')
    backup_tables_to_dropbox()
