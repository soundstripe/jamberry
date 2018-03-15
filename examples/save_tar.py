#!/usr/bin/env python

# This command line utility gives you a quick and easy TAR.csv file.
# By default it saves the file into the current directory, but
# you can specify the output directory as an optional argument.
#
# Username and password will be read from jamberry.ini.
#
# After the file is saved, it is launched in the system's default csv
# viewer.

import os
import argparse
from pathlib import Path
from datetime import datetime
import jamberry


def save_tar(destination='.'):
    """
    Fetch and save your current Team Activity Report CSV file into output_directory.
    defaults to current year/month, entire downline
    """
    destination = Path(destination)
    ws = jamberry.JamberryWorkstation()
    csv_data = ws.fetch_team_activity_csv()
    file_name = datetime.now().strftime('%Y-%m-%d %H.%M TAR.csv')
    file_path = destination / file_name
    file_path.write_bytes(csv_data)
    return file_path


if __name__ == '__main__':
    output_directory = '.'

    parser = argparse.ArgumentParser(description='Fetch your current TAR from your workstation.')
    parser.add_argument('--output_directory', default='.', help='Specify the output directory')
    parser.add_argument('--no-open', help='Specify this to simply save the file and exit')
    parser.parse_args()

    path = save_tar(destination=output_directory)
    os.startfile(path)
