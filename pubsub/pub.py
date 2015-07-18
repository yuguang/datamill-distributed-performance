__author__ = 'yuguang'

from common import *
import sys

if __name__ == '__main__':
    channel = sys.argv[1]

    while True:
        message = raw_input('Enter a message: ')

        if message.lower() == 'exit':
            break

        q = PubSub(channel)
        q.publish({'a':1})
