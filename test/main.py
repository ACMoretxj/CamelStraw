import time

from camelstraw import HttpGetJob, Slave


def callback(status_code, content):
    print(status_code, content)


if __name__ == '__main__':
    slave = Slave()
    jobs = (
        HttpGetJob('http://localhost', callback=callback),
        HttpGetJob('http://127.0.0.1', callback=callback),
        HttpGetJob('http://localhost', callback=callback),
        HttpGetJob('http://127.0.0.1', callback=callback),
    )
    slave.dispatch(*jobs)
    slave.start()
    time.sleep(15)
    slave.stop()
