#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Jan-Philip Gehrcke, http://gehrcke.de
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
import time
import logging
from subprocess import Popen, PIPE
from logging.handlers import RotatingFileHandler

"""
Invoke shutdown if none of a list of specified hosts is reachable over the
network during a certain time period (a couple of minutes, usually).
Reachability is tested via ICMP requests (pings) in regular intervals (a couple
of seconds, usually).

On FreeBSD as well as Linux the exit code of the ping program can be used for
determining if a host is alive. Quote from FreeBSD's ping manual:

    EXIT STATUS
         The ping utility exits with one of the following values:
         0       At least one response was heard from the specified host.
        [...]

Here, `ping -o -t 5 host` is used. By default, ping sends a request once per
second. `-t 5` makes sure that ping exits (latest) after 5 seconds. In other
words, if the host does not immediately respond to the first request although
it is online, a few more requests are sent. Any response arriving within 5
seconds after `ping` invocation is sufficient to detect the target host as
being alive. `-o` makes `ping` exit upon the first reply. Assuming that the
hosts to poll generally respond to ICMP requests, this configuration should be
pretty safe and insensitive to minor network hiccups.
"""

# List of hosts to check for being reachable. If name resolution is properly
# set up in the LAN, this can be hostnames, otherwise IP addresses.
HOSTS_TO_CHECK = [
    "hostname1",
    "hostname2",
    "192.168.1.5"
    ]

# Path to the log file of this script. The log file is automatically created,
# regularly rotated (when having a size of about 500 kB) and appended to among
# script invocations.
#logfile_path = "/mnt/disks/sshadmin_home/conditionalshutdown/logfile.log"
logfile_path = "logfile.log"


# Condition for shutdown is that all test hosts have constantly not been
# reachable within a couple of minutes (a case where we don't want the NAS to
# shut down is e.g. when all test hosts are simultaneously restarting, i.e.
# not reachable only once and for a short time). `REQUIRED_OFFLINE_SECONDS`
# defines the time interval that all hosts need to be offline before shutdown
# is invoked. Something like 5 minutes is recommended, i.e. 300 s.
REQUIRED_OFFLINE_SECONDS = 300

# `POLLING_INTERVAL_SECONDS` specifies how frequently the list of hosts should
# be checked during the time interval specified above. Checking every thirty
# seconds within five minutes would be a reasonable choice.
POLLING_INTERVAL_SECONDS = 30


# Make sure that hosts are tested multiple times within
# `REQUIRED_OFFLINE_SECONDS`.
assert REQUIRED_OFFLINE_SECONDS > 2*POLLING_INTERVAL_SECONDS


def main():
    exit_if_any_host_up()
    log.info("No host is reachable. Poll again, every %s s.",
        POLLING_INTERVAL_SECONDS)
    deadline = time.time() + REQUIRED_OFFLINE_SECONDS
    deadline_str = time.strftime("%H:%M:%S", time.localtime(deadline))
    while time.time() < deadline:
        log.info('Invoke shutdown if no host comes up until %s.', deadline_str)
        time.sleep(POLLING_INTERVAL_SECONDS)
        exit_if_any_host_up()
    log.info("'shutdown -p now' returncode: %s" %
        run_subprocess(['/sbin/shutdown', '-p', 'now']))


def exit_if_any_host_up():
    log.info("Pinging hosts, exit program if one is up.")
    for host in HOSTS_TO_CHECK:
        if host_responding(host):
            log.info("Exit program.")
            sys.exit(0)


def host_responding(host):
    log.info("Pinging host '%s'...", host)
    rc = run_subprocess(['ping', '-o', '-t', '5',  host])
    if not rc:
        log.info("Ping returned with code 0, host is up.")
        return True
    log.info("Ping returned with code %s, host is down.", rc)
    return False


def run_subprocess(cmdlist):
    log.debug("Calling Popen(%s).", cmdlist)
    try:
        sp = Popen(cmdlist, stdout=PIPE, stderr=PIPE)
        out, err = sp.communicate()
    except OSError as e:
        log.error("OSError while executing subprocess. Error message:\n%s" % e)
        sys.exit(1)
    if out:
        log.debug("Subprocess stdout:\n%s", out)
    if err:
        log.debug("Subprocess stderr:\n%s", err)
    return sp.returncode


if __name__ == "__main__":
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    fh = RotatingFileHandler(
        logfile_path,
        mode='a',
        maxBytes=500*1024,
        backupCount=30,
        encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    log.addHandler(ch)
    log.addHandler(fh)
    main()
