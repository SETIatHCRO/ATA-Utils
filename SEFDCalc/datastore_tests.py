#!/usr/bin/python

import argparse
import datetime
import sys

from os import environ

from google.cloud import datastore

PROJECT_ID = "ata-nsg-assessment1"

"""
Check for the env variable GOOGLE_APPLICATION_CREDENTIALS which is the fulle
path to your credentials JSON file. In that file the project ID is defined.
"""
def checkForCredentials():
    if environ.get("GOOGLE_APPLICATION_CREDENTIALS") is None:
        print("The environment variable GOOGLE_APPLICATION_CREDENTIALS is not defined.")
        print("See: https://cloud.google.com/docs/authentication/getting-started")
        print("You must also have the datastore libraries installed:")
        print("  https://cloud.google.com/datastore/docs/reference/libraries")
        print("Also see: https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/datastore/cloud-client")
        raise SystemExit

def createClient():
    return datastore.Client(PROJECT_ID);

def newSession(client, antlist, sourcelist):
    print("Antlist: %s, sourcelist: %s"  % (antlist, sourcelist));
    antArray = antlist.split(",")
    for ant in antArray:
        print ant

def init():
    checkForCredentials()
    createClient()

def printHelp():
    print("Syntax: %s <args>" % sys.argv[0])
    print("\n")
    sys.exit(0)

if __name__ == '__main__':

    #if(len(sys.argv) == 1):
    #    printHelp()
    def new_session(client, args):
        newSession(client, args.antlist, args.sourcelist);


    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    new_parser = subparsers.add_parser('newsession', help=new_session.__doc__)
    new_parser.set_defaults(func=new_session)
    new_parser.add_argument('antlist', help='comma separated antenna list')
    new_parser.add_argument('sourcelist', help='comma separated source list')

    args = parser.parse_args()

    client = createClient()
    args.func(client, args)

    init()


print "HELLO"
