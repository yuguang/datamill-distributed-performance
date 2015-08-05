from common import *
import settings, time

if __name__ == '__main__':

    while True:
        q = PubSub()
        print 'Publishing updates and jobs to {} channel'.format(q.channel)
        q.publish({'update':1, 'job': 1})
        time.sleep(settings.CONTROLLER_LOOP_SLEEP_TIME)