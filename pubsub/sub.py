__author__ = 'yuguang'

from common import *
import sys

if __name__ == '__main__':
    channel = sys.argv[1]

    q = PubSub(channel)


    def handler(data):
        print "Data received: %r" % data

    print 'Listening to {channel}'.format(**locals())


    q.subscribe(handler)