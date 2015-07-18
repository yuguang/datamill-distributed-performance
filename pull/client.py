__author__ = 'yuguang'
from ftplib import all_errors as FTP_ERRORS
import ftp, time, settings
from emerge import Emerge
import threading, sys, csv
from Queue import Queue

class Worker(threading.Thread):
    def __init__(self, timeout):
        self.updates = 0
        self.jobs = 0
        self.errors = 0
        self.timeout = timeout
        threading.Thread.__init__(self)

    def get_statistics(self):
        return {
            'updates': self.updates,
            'jobs': self.jobs,
            'errors': self.errors,
        }

    def run(self):
        m = ftp.Master()
        start = time.time()
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
            if (time.time() - start) > self.timeout:
                break

if __name__ == '__main__':
    num_workers = int(sys.argv[1])
    timeout = int(sys.argv[1]) * 60
    queue = Queue(num_workers)
    for i in range(num_workers):
        thread = Worker(timeout)
        thread.start()
        queue.put(thread, True)

    time.sleep(timeout)
    updates = 0
    jobs = 0
    errors = 0
    while not queue.empty():
        thread = queue.get(True)
        stats = thread.get_statistics()
        updates += stats['updates']
        jobs += stats['jobs']
        errors += stats['errors']
        thread.join(1)
    with open('results.csv', 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([updates, jobs, errors])
    sys.exit(0)