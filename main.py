import os
import shutil
from pathlib import Path
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

CONFIG_INPUT = 'Hot Folder Input'
CONFIG_OUTPUT = 'Hot Folder Output'

DEFAULT_LOCATION = config.get('Hot Folders Location', 'Location')

def adding_to_file_name(options):
    hot_folder_location = f'{DEFAULT_LOCATION}/{options}'
    hp_hot_folder_location = 'C:/DylanH/VSC_Projects/Change_Name_Hotfoler/HpHotFolder'
    name_suffix = config.get(CONFIG_INPUT, options)
    for file in os.listdir(hot_folder_location):
        p = Path(file)
        new_file_name = "{0}{2}{1}".format(p.stem, p.suffix, name_suffix)
        shutil.move(f'{hot_folder_location}/{file}', f'{hp_hot_folder_location}/{new_file_name}')
        


if __name__ == "__main__":
    while True:
        for options in config.options(CONFIG_INPUT):
            print(options)
            adding_to_file_name(options)
            break