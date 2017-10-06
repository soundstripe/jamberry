#!/usr/bin/env python

# This command line utility gives you a quick and easy TAR.csv file.
# By default it saves the file into the current directory, but
# you can specify the output directory as an optional argument.

from pathlib import Path
from datetime import datetime
import argparse
import jamberry


def save_tar(destination='.'):
    """Fetch and save your current Team Activity Report CSV file into output_directory."""
    destination = Path(destination)
    ws = jamberry.JamberryWorkstation()  # username and password will be read from jamberry.ini
    csv_data = ws.fetch_team_activity_csv()  # defaults to current month, entire downline
    file_name = datetime.now().strftime('%Y-%m-%d %H.%M TAR.csv')
    file_path = destination / file_name
    file_path.write_bytes(csv_data)
    return file_name


if __name__ == '__main__':
    output_directory = '.'

    parser = argparse.ArgumentParser(description='Fetch your current TAR from your workstation.')
    parser.add_argument('--output_directory', default='.', help='Specify the output directory')
    parser.parse_args()

    print(save_tar(destination=output_directory))
