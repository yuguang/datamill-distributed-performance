__author__ = 'yuguang'
from ftplib import all_errors as FTP_ERRORS
import ftp, time, settings
from emerge import Emerge

m=ftp.Master()
jobs = 0
errors = 0
while True:
    if Emerge.worker_needs_update():
        print "Got update notification"

    try:
        if m.pick_job():
            print "Got job"
            jobs += 1
        else:
            time.sleep(settings.CONTROLLER_LOOP_SLEEP_TIME)
    except FTP_ERRORS:
        print "An FTP error occured"
        errors += 1

