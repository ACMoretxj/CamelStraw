import asyncio
import time
from multiprocessing import Process

from camelstraw import Worker, Job, HttpGetJob


if __name__ == '__main__':
    jobs = [
        HttpGetJob('http://localhost'),
        HttpGetJob('http://127.0.0.1'),
        HttpGetJob('http://camel-straw.com'),
        # HttpGetJob('http://baidu.com')
    ]
    worker = Worker()
    print('worker = Worker()')
    [worker.dispatch(job) for job in jobs]
    print('worker.dispatch(job)')
    worker.start()
    print('worker.start()')
