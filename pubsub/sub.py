__author__ = 'yuguang'

from common import *
import settings
import threading, sys, csv
from Queue import Queue

class Worker(threading.Thread):
    def __init__(self, timeout):
        self.updates = 0
        self.jobs = 0
        self.errors = 0
        self.timeout = timeout
        threading.Thread.__init__(self)

    def run(self):
        q = PubSub()

        headers = [self.num_workers, settings.CONTROLLER_LOOP_SLEEP_TIME]
        def handler(data):
            with open('results.csv', 'a') as csvfile:
                writer = csv.writer(csvfile)
                if data['update']:
                    writer.writerow(headers + [1, 0, 0])
                if data['job']:
                    writer.writerow(headers + [0, 1, 0])

        print 'Listening to {channel}'.format(**locals())
        q.subscribe(handler)

if __name__ == '__main__':
    num_workers = int(sys.argv[1])
    queue = Queue(num_workers)
    for i in range(num_workers):
        thread = Worker(num_workers)
        thread.start()
        queue.put(thread, True)