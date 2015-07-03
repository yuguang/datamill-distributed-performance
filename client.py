__author__ = 'yuguang'
from ftplib import all_errors as FTP_ERRORS

import ftp
m=ftp.Master()
jobs = 0
errors = 0
while True:
    try:
        if m.pick_job():
            print "Got job"
            jobs += 1
    except FTP_ERRORS:
        print "An FTP error occured"
        errors += 1