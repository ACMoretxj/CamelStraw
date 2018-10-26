import multiprocessing
import time

from camelstraw import HttpGetJob, Slave


def callback(status_code, content):
    # print(multiprocessing.current_process().name, status_code, len(content))
    pass


if __name__ == '__main__':
    slave = Slave()
    jobs = (
        HttpGetJob('http://127.0.0.1', callback=callback),
        HttpGetJob('http://127.0.0.1', callback=callback),
        HttpGetJob('http://localhost', callback=callback),
        HttpGetJob('http://127.0.0.1', callback=callback),
    )
    slave.dispatch(*jobs)
    slave.start()
    time.sleep(7)
    slave.stop()
