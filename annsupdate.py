#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE
import sys
import argparse
import ipaddress

parser = argparse.ArgumentParser()
parser.add_argument("--network", default="192.168.2.0/24")
parser.add_argument("--nameserver", default="192.168.2.68")
parser.add_argument("--domain", default="hisaruki.tk")
parser.add_argument("--ttl", default=1800, type=int)
parser.add_argument("--timeout", default=0.15, type=float)
args = parser.parse_args()

args.network = ipaddress.ip_network(args.network)

o, e = Popen(["arp", "-n"], stdout=PIPE).communicate()
arps = o.decode().splitlines()
arps = [x.split() for x in arps if x.find("Address") < 0]

text = 'server ' + args.nameserver + "\n"


for arp in arps:
    ip = arp[0]
    if not ipaddress.ip_address(ip) in args.network.hosts():
        continue
    proc = ["timeout", str(args.timeout), "nmblookup", "-A", ip]
    o, e = Popen(proc, stdout=PIPE).communicate()
    if not o:
        continue
    result = o.decode().splitlines()
    result = [x.split() for x in result if x]
    for line in filter(lambda x: x[1] == '<20>', result):
        hostname = line[0]
        fqdn = hostname + "." + args.domain
        text += "update delete " + fqdn + " A\n"
        text += "update add " + fqdn
        text += " " + str(args.ttl)
        text += " A " + ip + " \n"
text += "send\n"
text += "quit\n"

sys.stderr.write(text)
proc = Popen(["nsupdate"], stdin=PIPE)
proc.stdin.write(text.encode())
proc.communicate()
