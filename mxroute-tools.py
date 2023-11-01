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

import requests
import json
import getopt
import sys
import getpass

# Constants for the API
ENDPOINT_PREFIX = "https://"
ENDPOINT_SUFFIX = ".mxrouting.net:2222"
DOMAINS_CMD = "CMD_API_SHOW_DOMAINS"
HEADERS = {"Content-Type": "application/json"}

def show_usage():
    """Prints usage and exits"""

    print ("Usage: imapbackup [OPTIONS] -h HOST -u USERNAME [-p PASSWORD]")
    print (" -h HOST --host=HOST           Short host address, eg. if your server is maildemo.mxrouting.net use maildemo")
    print (" -u USER --user=USER           Username to log into server")
    print (" -p PASS --pass=PASS           Prompts for password or login key if not specified.")
    sys.exit(1)


def get_config():
    """Process command line options, returns a dictionary with config in it, will exit on error"""

    try:
        short_arguments = "h:u:p:"
        long_arguments = ["server=", "user=", "pass="]
        options, remaining_args = getopt.gnu_getopt(sys.argv[1:], short_arguments, long_arguments)
    except getopt.GetoptError:
        show_usage()

    config = {}
    errors = []

    # Process the command line, storing values in config and any errors
    if not len(options) and not len(remaining_args):
        show_usage()

    for option, value in options:
        if option in ("-h", "--host"):
            config['host'] = value
        elif option in ("-u", "--user"):
            config['user'] = value
        elif option in ("-p", "--pass"):
            config['pass'] = value
        else:
            errors.append("Unknown option: " + option)

    for arg in remaining_args:
        errors.append("Unknown argument: " + arg)

    # Check the options, showing errors and exiting if needed
    for error in errors:
        print ("ERROR: ", error)
    if len(errors):
        sys.exit(1)

    # Prompt for any missing arguments
    if 'pass' not in config:
        config['pass'] = getpass.getpass("Password or Login Key: ")

    return config


def make_api_request(cmd, config, params={}):
    """Make a call to the Direct Admin API, returns the json response"""
    url = f"{ENDPOINT_PREFIX}{config['host']}{ENDPOINT_SUFFIX}/{cmd}"
    default_params = {'json': 'yes'}
    request_params = {**default_params, **(params or {})}
    try:
        response = requests.get(url, auth=(config['user'], config['pass']), headers=HEADERS, params=request_params)
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



def main():
    """Main entry point"""
    config = get_config()

    # Get the list of domains
    domains = make_api_request(DOMAINS_CMD, config)
    print(f"# Domains ({len(domains)})")
    for domain in domains:
        print(domain)

if __name__ == '__main__':
    main()