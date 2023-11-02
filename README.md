# mxroute-tools

Command line tools for mxroute.com mail hosting

## Overview

A python script for interacting with the Direct Admin API on [MXRoute.com](https://mxroute.com) mail hosting and getting lists of domains, mailboxes and forwarders.

## Features

* List domains managed by account
* List mailboxes
* List forwarders
* Check DKIM settings on domains
* Update or create forwarders

## Usage

To update a list of forwarders, use this command line:

./mxroute_tools.py -s server -u username -p neveragainfallforeveragain fwd < list-of-forwarders.txt

list-of-forwarders.txt should look like this (the same format as the DirectAdmin raw data):

first@test.com --> catch@test.com,throw@test.com
second@test.com --> catch@test.com

## Requirements

Requires python 3.8 and above.

## Contact

https://codev.uk/  
marc@codev.uk
