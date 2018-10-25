from camelstraw import HttpGetJob, Slave


if __name__ == '__main__':
    slave = Slave()
    jobs = (
        HttpGetJob('http://localhost'),
        HttpGetJob('http://127.0.0.1'),
        HttpGetJob('http://localhost'),
        HttpGetJob('http://127.0.0.1'),
    )
    slave.dispatch(*jobs)
    slave.start()
