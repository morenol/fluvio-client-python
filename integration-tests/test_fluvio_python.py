from fluvio import (Fluvio, FluviorError, Offset)
import unittest
import uuid


def create_topic(topic):
    import subprocess
    subprocess.run("fluvio topic create %s" % topic, shell=True)


def delete_topic(topic):
    import subprocess
    subprocess.run("fluvio topic delete %s" % topic, shell=True)


class TestFluvioMethods(unittest.TestCase):
    def setUp(self):
        self.topic = str(uuid.uuid4())
        create_topic(self.topic)

    def tearDown(self):
        delete_topic(self.topic)

    def test_connect(self):
        # A very simple test
        Fluvio.connect()

    def test_produce(self):
        fluvio = Fluvio.connect()

        producer = fluvio.topic_producer(self.topic)
        for i in range(10):
            producer.send_string("FOOBAR %s " % i)

    def test_consume_with_iterator(self):
        fluvio = Fluvio.connect()
        producer = fluvio.topic_producer(self.topic)
        for i in range(10):
            producer.send_string("record-%s" % i)

        consumer = fluvio.partition_consumer(self.topic, 0)
        count = 0
        for i in consumer.stream(Offset.beginning()):
            print("THIS IS IN AN ITERATOR! %s" % i.value())
            self.assertEqual(
                bytearray(i.value()).decode(), 'record-%s' % count
            )
            self.assertEqual(i.value_string(), 'record-%s' % count)
            count += 1
            if count >= 10:
                break

    def test_key_value(self):
        fluvio = Fluvio.connect()
        producer = fluvio.topic_producer(self.topic)
        for i in range(10):
            producer.send("foo".encode(), ("record-%s" % i).encode())

        consumer = fluvio.partition_consumer(self.topic, 0)
        count = 0
        for i in consumer.stream(Offset.beginning()):
            print(
                "THIS IS IN AN ITERATOR! key - %s, value - %s" % (
                    i.key(),
                    i.value()
                )
            )
            self.assertEqual(
                bytearray(i.value()).decode(), 'record-%s' % count
            )
            self.assertEqual(i.value_string(), 'record-%s' % count)
            self.assertEqual(i.key_string(), 'foo')
            self.assertEqual(i.key(), list('foo'.encode()))

            count += 1
            if count >= 10:
                break

    def test_batch_produce(self):
        fluvio = Fluvio.connect()
        producer = fluvio.topic_producer(self.topic)

        records = []
        for i in range(10):
            record = (("%s" % i).encode(), ("record-%s" % i).encode())
            records.append(record)

        producer.send_all(records)

        consumer = fluvio.partition_consumer(self.topic, 0)
        count = 0
        for i in consumer.stream(Offset.beginning()):
            self.assertEqual(
                bytearray(i.value()).decode(), 'record-%s' % count
            )
            self.assertEqual(i.value_string(), 'record-%s' % count)
            self.assertEqual(i.key_string(), ('%s' % count))
            self.assertEqual(i.key(), list(('%s' % count).encode()))

            count += 1
            if count >= 10:
                break


class TestFluvioErrors(unittest.TestCase):
    def setUp(self):
        self.topic = str(uuid.uuid4())

    def test_produce_on_uncreated_topic(self):
        fluvio = Fluvio.connect()

        error = None
        try:
            fluvio.topic_producer(self.topic)
        except FluviorError as e:
            error = e
            print('ERROR: %s' % e)

        self.assertTrue(error is not None)
        self.assertEqual(
            error.args,
            (
                'Topic not found: %s' % self.topic,  # noqa: E501
            )
        )
