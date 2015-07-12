__author__ = 'yuguang'
from ftplib import all_errors as FTP_ERRORS
import ftp, time, settings
from emerge import Emerge
import multiprocessing
import threading, sys

class Worker(threading.Thread):
    def __init__(self):
        self.updates = 0
        self.jobs = 0
        self.errors = 0
        threading.Thread.__init__(self)

    def get_statistics(self):
        return {
            'updates': self.updates,
            'jobs': self.jobs,
            'errors': self.errors,
        }

    def run(self):
        m=ftp.Master()
        while True:
            try:
                if Emerge.worker_needs_update():
                    print "Got update notification"
                    self.updates += 1
                if m.pick_job():
                    print "Got job"
                    self.jobs += 1
                else:
                    time.sleep(settings.CONTROLLER_LOOP_SLEEP_TIME)
            except Exception:
                print "An Error occured"
                self.errors += 1

if __name__ == '__main__':
    num_workers = int(sys.argv[1])
    for i in range(num_workers):
        t = threading.Thread(target=Worker)
        t.start()

    time.sleep(60)
    updates = 0
    jobs = 0
    errors = 0
    main_thread = threading.currentThread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        stats = t.get_statistics()
        updates += stats['updates']
        jobs += stats['jobs']
        errors += stats['errors']
        t.stop()
        t.join()