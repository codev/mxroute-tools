#!/usr/bin/env python3

"""
MXRoute domain and email listing tool.

 This file is part of mxroute-tools
 Copyright (C) 2023 Marc Sutton

 mxroute-tools is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__version__ = "1.0"
__author__ = "Marc Sutton (https://codev.uk)"
__copyright__ = "Copyright 2023 Marc Sutton"
__license__ = "GPL"
__maintainer__ = "Marc Sutton"
__email__ = "marc@codev.uk"

import json
import getpass
import argparse
import requests

# Constants for the API
ENDPOINT_PREFIX = "https://"
ENDPOINT_SUFFIX = ".mxrouting.net:2222"
DOMAINS_CMD = "CMD_API_SHOW_DOMAINS"
POP_CMD = "CMD_API_POP"
FORWARDERS_CMD = "CMD_API_EMAIL_FORWARDERS"
HEADERS = {"Content-Type": "application/json"}

# Globals
config = {}

def get_config():
    """
    Process command line options.

    Returns a dictionary with config in it as well as placing it into a global called config.
    Exits on error after displaying messages.
    """

    global config
    parser = argparse.ArgumentParser(
        prog="mxroute-tools",
        description='Tools for MXRoute.com email dashboard via DirectAdmin API.')
    parser.add_argument('-s', '--host',
                        required=True,
                        help="Short server address, eg. for maildemo.mxrouting.net use maildemo")
    parser.add_argument('-u', '--user',
                        required=True,
                        help="Username to log into server")
    parser.add_argument('-p', '--pass',
                        help="Login key or password, will prompt if not present",
                        default='')
    config = vars(parser.parse_args())

    # Prompt for any missing arguments
    if not config['pass']:
        config['pass'] = getpass.getpass("Password or Login Key: ")

    return config

def make_api_request(cmd, params):
    """
    Make a call to the Direct Admin API taking the command and parameters.

    Returns the response.
    """
    url = f"{ENDPOINT_PREFIX}{config['host']}{ENDPOINT_SUFFIX}/{cmd}"
    default_params = {'json': 'yes'}
    request_params = {**default_params, **(params or {})}
    try:
        response = requests.get(url, auth=(config['user'], config['pass']),
                                headers=HEADERS, params=request_params, timeout=10)
        response.raise_for_status()  # Will raise an error for bad status codes
        return response.json()
    except json.decoder.JSONDecodeError as e:
        # If JSON decoding fails then print the error and the original response text
        print(f"ERROR: JSONDecodeError: {e}")
        print("Response content:", response.text)
        raise
    except requests.RequestException as e:
        # Handle other request related errors
        print(f"ERROR: RequestException: {e}")
        raise

def get_email_data_per_domain(cmd, domains, action='list'):
    """Make a request per domains, returns a dictionary mapping domains to results"""
    result = {}
    for domain in domains:
        response = make_api_request(cmd, {'domain': domain, 'action': action})
        result[domain] = response
    return result


def main():
    """Main entry point"""
    get_config()

    # Get the list of domains
    domains = make_api_request(DOMAINS_CMD, {})
    print(f"# Domains ({len(domains)})")
    for domain in domains:
        print(domain)
    print()

    # Get the list of mailboxes
    email_boxes = get_email_data_per_domain(POP_CMD, domains)
    box_count = sum(len(box) for box in email_boxes.values())
    print(f"# Email Accounts ({box_count})")
    for domain, boxes in email_boxes.items():
        for box in boxes:
            print(f"{box}@{domain}")
    print()

    # Get the list of forwarders
    forwarders = get_email_data_per_domain(FORWARDERS_CMD, domains)
    forwarder_count = sum(len(fwd) for fwd in forwarders.values())
    print(f"# Forwarders ({forwarder_count})")
    for domain, fwds in forwarders.items():
        for fwd_from, fwd_to in fwds.items():
            to = ",".join(fwd_to)
            print(f"{fwd_from}@{domain} --> {to}")
    print()

if __name__ == '__main__':
    main()
