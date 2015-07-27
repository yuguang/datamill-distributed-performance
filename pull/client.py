__author__ = 'yuguang'
from ftplib import all_errors as FTP_ERRORS
import ftp, time, settings
from emerge import Emerge
import threading, sys, csv
from Queue import Queue

class Worker(threading.Thread):
    def __init__(self, num_workers):
        self.updates = 0
        self.jobs = 0
        self.errors = 0
        self.num_workers = num_workers
        threading.Thread.__init__(self)

    def get_statistics(self):
        return {
            'updates': self.updates,
            'jobs': self.jobs,
            'errors': self.errors,
        }

    def run(self):
        m = ftp.Master()
        headers = [self.num_workers, settings.CONTROLLER_LOOP_SLEEP_TIME, settings.FTP_CONNECT_TIMEOUT_SECS, settings.LAYMAN_TIMEOUT_SECS]
        while True:
            try:
                if Emerge.worker_needs_update():
                    print "Got update notification"
                    self.updates += 1
                    with open('results.csv', 'a') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(headers + [1, 0, 0])
                if m.pick_job():
                    print "Got job"
                    self.jobs += 1
                    with open('results.csv', 'a') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(headers + [0, 1, 0])
                time.sleep(settings.CONTROLLER_LOOP_SLEEP_TIME)
            except Exception:
                print "An Error occured"
                self.errors += 1
                with open('results.csv', 'a') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers + [0, 0, 1])

if __name__ == '__main__':
    num_workers = int(sys.argv[1])
    queue = Queue(num_workers)
    for i in range(num_workers):
        thread = Worker(num_workers)
        thread.start()
        queue.put(thread, True)