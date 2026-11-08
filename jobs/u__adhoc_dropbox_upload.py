from utils.database_utils import backup_table, batch_backup
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-t', '--table_name', type=str, required=True, help='Name of the table to backup')
parser.add_argument('-s', '--schema_name', type=str, required=True, help='Name of the schema')
parser.add_argument('-f', '--dropbox_file', type=str, required=True, help='Name of the file to be created in Dropbox')
parser.add_argument('-df', '--dropbox_folder', type=str, required=True, help='Name of the folder in Dropbox where the file will be uploaded')
parser.add_argument('-w', '--where', type=str, required=False, help='Optional WHERE clause for the SQL query')
parser.add_argument('-z', '--zip', type=str, required=False, help='Optional flag to indicate if the file should be zipped')

args = parser.parse_args()

print(args)
if __name__ == '__main__':
    batch_backup(
        args.table_name, 
        args.schema_name, 
        args.dropbox_file, 
        args.dropbox_folder, 
        where=args.where,
        zip=args.zip)