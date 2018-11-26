# test duration (seconds)
TEST_DURATION = 60

# ip value of master machine
MASTER = '10.172.143.48'
# websocket port port of master service
MASTER_PORT = 9001
# ip values list of slave machines
SLAVES = [
    '10.172.143.48'
]

# interval between each worker checks the queue (seconds)
WORKER_CHECK_INTERVAL = 1
# default timeout for each worker (seconds)
WORKER_TIMEOUT = -1
