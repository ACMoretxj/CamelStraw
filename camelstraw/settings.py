# default start method
START_MODE = 'command'
# interval between each worker checks the queue (seconds)
WORKER_CHECK_INTERVAL = 1
# default timeout for each worker
WORKER_TIMEOUT = -1
# test duration (seconds)
TEST_DURATION = 60

MASTER = '10.172.143.48'
MASTER_PORT = 9001
SLAVES = [
    '10.172.143.48'
]
