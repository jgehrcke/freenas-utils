#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Jan-Philip Gehrcke, http://gehrcke.de
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
import logging
from subprocess import call
from time import time, strftime, localtime
from logging.handlers import RotatingFileHandler

LOGFILE_PATH = "/mnt/two_3TB_disks/jpg_private/home/progg0rn/nas_scripts/syncdir_rsynctasks/synctasks.log"
RSYNC_LOGFILES_DIR = "/mnt/two_3TB_disks/jpg_private/home/progg0rn/nas_scripts/syncdir_rsynctasks/rsynclogs"


# TASKS is a list of 3-tuples. In a 3-tuple, the elements are, by order:
# - name
# - source directory (without trailing slash)
# - target directory (source dir is put into the target dir)
TASKS = [
    (
        "home",
        "/mnt/two_3TB_disks/jpg_private/home",
        "/mnt/usbbackup/synctargets/jpg_private"
    ),
    (
        "sshadmin_home",
        "/mnt/two_3TB_disks/sshadmin_home",
        "/mnt/usbbackup/synctargets"
    ),
    (
        "user_home",
        "/mnt/two_3TB_disks/user_home",
        "/mnt/usbbackup/synctargets"
    ),
    (
        "photos",
        "/mnt/two_3TB_disks/jpg_private/photos",
        "/mnt/usbbackup/synctargets/jpg_private"
    ),
    (
        "guterstuff",
        "/mnt/two_3TB_disks/jpg_private/guterstuff",
        "/mnt/usbbackup/synctargets/jpg_private"
    ),
    (
        "audio",
        "/mnt/two_3TB_disks/media/__AUDIO__",
        "/mnt/usbbackup/synctargets/media"
    ),
    ]


def main():
    log.info("Program launch.")
    t0 = time()
    tasks = [SyncDirTask(n,s,t) for n,s,t in TASKS]
    log.info("Running tasks.")
    for t in tasks:
        t.run()
    duration = time() - t0
    log.info("Task iteration done.")
    log.info("Program runtime (walltime): %s", seconds_to_hms(duration))
    log.info("Program termination.")


class SyncDirTask(object):
    def __init__(self, name, source_dir, target_dir):
        log.info("Setting up task '%s'.", name)
        self.name = name
        # Source dir must be given without trailing slash, rsync then
        # creates this dir in target dir.
        if not os.path.isdir(source_dir):
            log.error("Source is no directory: %s", source_dir)
            sys.exit(1)
        if not os.path.isdir(target_dir):
            log.error("Target is no directory: %s", target_dir)
            sys.exit(1)
        if source_dir.endswith("/"):
            log.error("Source has trailing slash: %s", source_dir)
            sys.exit(1)
        self._source_dir = source_dir
        self._target_dir = target_dir
        self._logfile_dir = RSYNC_LOGFILES_DIR
        assert os.path.isdir(self._logfile_dir)

    def run(self):
        log.info("Starting task '%s'.", self.name)
        self._run_rsync()
        log.info("Task %s finished.", self.name)

    def _run_rsync(self):
        logfname = "rsync_stdouterr_%s_%s.log" % (self.name, timestr())
        logpath = os.path.join(self._logfile_dir, logfname)
        rsync_cmd = [
            "/usr/local/bin/rsync",
            "--archive",
            "--verbose",
            "--hard-links",
            "--delete",
            "--fuzzy",
            "--stats",
            self._source_dir,
            self._target_dir,
            ]
        log.info("Opening file '%s' for capturing rsync's stdout/err.",
            logpath)
        with open(logpath, "w") as logfile:
            t0 = time()
            log.info("rsync cmd list:\n%s", rsync_cmd)
            log.info("Running rsync.")
            try:
                rcode = call(rsync_cmd, stdout=logfile, stderr=logfile)
                if rcode == 0:
                    log.info("rsync returncode is 0.")
                else:
                    log.error("rsync returncode not 0: %s", rcode)
            except OSError as e:
                log.error("OSError while executing rsync: %s", e)
                return
            duration = time() - t0
            log.info("rsync runtime (walltime): %s", seconds_to_hms(duration))
            self._duration = duration
            self._rsync_returncode = rcode
            logfile.write("\nwrapper info: rsync exitcode: %s\n" % rcode)
            logfile.write("wrapper info: rsync runtime (walltime): %s\n" %
                seconds_to_hms(duration))


def timestr():
    return strftime("%Y%m%d-%H%M%S", localtime())


def seconds_to_hms(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return "%s:%s:%.2f" % (hours, minutes, seconds)


if __name__ == "__main__":
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    fh = RotatingFileHandler(
        LOGFILE_PATH,
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
