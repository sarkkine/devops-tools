#!/usr/bin/env python

import json
import requests
import base64
import sys, getopt
from os.path import expanduser


def main(argv):
    usage = "registry-ls -r <registry_hostname:port> -u <username> -p <password>"
    registry_host = None
    username = password = None
    try:
        opts, args = getopt.getopt(argv, "hr:u:p:", ["help", "registry=", "username=", "password="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print usage
            sys.exit()
        elif opt in ("-r", "--registry"):
            registry_host = arg
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
    if (username and not password) or (password and not username):
        print "ERROR Both username and password are required"
        print usage
        sys.exit(2)
    if not registry_host:
        print "ERROR Registry host is required"
        print usage
        sys.exit(2)

    reg = Registry(registry_host, get_auth(registry_host, username, password))
    repos = reg.get_repos()
    max_width = len(max(repos)) + len(registry_host) + 3
    widths = [max_width, 20]
    print_row(["REPOSITORY","TAG"], widths)

    for repo in repos:
        for tag in reg.get_tags(repo):
            print_row(["%s/%s" % (registry_host, repo), tag], widths)

def print_row(row, widths):
    print (" ".join( format(cdata, "%ds" % width) for width, cdata in zip(widths, row)))

def get_auth(registry_host, username, password):
    if username:
        return base64.b64encode("%s:%s" % (username, password))

    try:
        conf_filename = expanduser('~/.docker/config.json')
        with open(conf_filename) as conf_file:
            conf = json.load(conf_file)
            return conf['auths'][registry_host]['auth']
    except:
        print "ERROR Could not find auth entry in %s for %s" % (conf_filename, registry_host)
        sys.exit(2)

class Registry:
    def __init__(self, host, auth, ssl=True):
        self.host = host
        self.auth = auth
        if ssl:
            self.proto="https://"
        else:
            self.proto="http://"

    def get_repos(self):
        req = self.registry_req("_catalog")
        if req != None:
            pjson = json.loads(req.text)
            repo_array = pjson['repositories']
        else:
            return None
        return repo_array

    def get_tags(self, repo):
        req = self.registry_req("%s/tags/list" % repo)
        if req != None:
            pjson = json.loads(req.text)
            repo_array = pjson['tags']
        else:
            return None
        return repo_array

    def registry_req(self, operation):
        headers = {"Authorization": "Basic %s" % self.auth}
        req = requests.get("%s%s/v2/%s" % (self.proto, self.host, operation), headers=headers)
        req.raise_for_status()
        return req

if __name__ == "__main__":
    main(sys.argv[1:])
