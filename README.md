# jamberry

This is an unlikely library to access your Jamberry consultant
workstation information in Python.

## Installation

First method -- quick/easy

    pip install git+git://github.com/soundstripe/jamberry.git

Second method -- useful if you want to contribute or extend this work

    git clone --depth=1 https://github.com/soundstripe/jamberry.git
    cd jamberry
    python setup.py develop

## Usage

Example: count the number of each consultant type in your downline

    from collections import Counter
    import jamberry

    ws = jamberry.JamberryWorkstation('username', 'password')
    consultant_types = Counter()
    for consultant, activity in ws.downline_consultants():
        consultant_types['consultant.consultant_type] += 1
    print(consultant_types)

Output:

    Counter({'Fast Start': 10, 'Hobbyist': 180, 'Professional Consultant': 96})
