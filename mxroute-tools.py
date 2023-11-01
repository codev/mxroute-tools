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
DNS_CMD = "CMD_API_DNS_CONTROL"
DKIM_SUB = 'x._domainkey'
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
        formatter_class=argparse.RawTextHelpFormatter,
        description='Tools for MXRoute.com email dashboard via DirectAdmin API.')
    parser.add_argument('command', choices=['list', 'dkim'], default='list', type=str, nargs='?',
                        help="""command to run:
list - list information about domains and email accounts
dkim - check DKIM settings on each domain""")
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

def command_list(domains):
    """List information about domains"""
    # Get the list of domains
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

def command_dkim(domains):
    """Check DKIM settings for domains"""
    print("* DKIM settings")

    for domain in domains:
        # Get the DKIM data for each domain
        dns_data = make_api_request(DNS_CMD, {'domain': domain })
        dkim_data = next((item for item in dns_data['records'] if item.get('name') == DKIM_SUB), None)
        if dkim_data:
            dkim_data = dkim_data['value']
            dkim_data = dkim_data[1:len(dkim_data)-1]

        # Now test if it matches by looking up the live value on DNS
        # pip3 install dnspython
        import dns.resolver
        dkim_in_dns = ''
        try:
            dns_lookup = dns.resolver.resolve(f"{DKIM_SUB}.{domain}", 'TXT')[0]
            for txt_string in dns_lookup.strings:
                dkim_in_dns = dkim_in_dns + txt_string.decode('utf-8')
        except:
            dkim_in_dns = 'NONE'

        if dkim_in_dns == dkim_data:
            print(f"** DNS CORRECT for {domain}")
        else:
            if dkim_in_dns and dkim_in_dns != 'NONE':
                print (f"** DNS SETUP for {domain}")
            else:
                print(f"** DNS FAILURE for {domain}")
            dkim_split = ['"' + dkim_data[i:i+110] + '"' for i in range(0, len(dkim_data), 250)]
            print(f"{DKIM_SUB} 3000 IN TXT " + " ".join(dkim_split))
            print("")


def main():
    """Main entry point"""
    get_config()

    domains = make_api_request(DOMAINS_CMD, {})
    if config['command'] == 'list':
        command_list(domains)
    elif config['command'] == 'dkim':
        command_dkim(domains)
    else:
        print(f"ERROR unknown command: {config['command']}")

if __name__ == '__main__':
    main()
