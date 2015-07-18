import json
from settings import config
import redis

class PubSub(object):
    """
    Very simple Pub/Sub pattern wrapper
    using simplified Redis Pub/Sub functionality.

    Usage (publisher)::

        import redis

        r = redis.Redis()

        q = PubSub(r, "channel")
        q.publish("test data")


    Usage (listener)::

        import redis

        r = redis.Redis()
        q = PubSub(r, "channel")

        def handler(data):
            print "Data received: %r" % data

        q.subscribe(handler)

    """
    def __init__(self, channel="default"):
        self.redis = redis.StrictRedis(**config)
        self.channel = channel

    def publish(self, data):
        self.redis.publish(self.channel, json.dumps(data))

    def subscribe(self, handler):
        redis = self.redis.pubsub()
        redis.subscribe(self.channel)

        for data_raw in redis.listen():
            if data_raw['type'] != "message":
                continue

            data = json.loads(data_raw["data"])
            handler(data)
