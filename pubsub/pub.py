__author__ = 'yuguang'

from common import *
import sys
import settings, time

if __name__ == '__main__':

    while True:
        q = PubSub()
        q.publish({'update':1, 'job': 1})
        time.sleep(settings.CONTROLLER_LOOP_SLEEP_TIME)