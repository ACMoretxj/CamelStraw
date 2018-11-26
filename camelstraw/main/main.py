import argparse
from multiprocessing import cpu_count

from .launchers import CmdLauncher, WebLauncher
from ..settings import TEST_DURATION
from ..net import HttpMethod


def cmd_main():
    parser = argparse.ArgumentParser(description='CamelStraw command line tool.')
    # though the default value None here, the real default value will be set to cpu_count() in WorkerManager
    parser.add_argument('-w', '--worker', metavar='WorkerNumber', dest='worker_num', action='store', nargs='?',
                        default=None, type=int, help='worker number, every worker owns a standalone process, '
                                                     'default value is the number of your cpu.')
    parser.add_argument('-t', '--timeout', metavar='Timeout', dest='duration', action='store', nargs='?',
                        default=TEST_DURATION, type=int, help='test duration (seconds), default value is 60.')
    parser.add_argument('-m', '--method', metavar='Method', dest='method', action='store', nargs='?',
                        default=HttpMethod.GET.phrase, help='request method, should be one of \'HttpGet\' or '
                                                            '\'HttpPost]\', for more methods please refer to '
                                                            'the api document.')
    parser.add_argument('-p', '--path', metavar='Path', dest='urls', action='append', nargs='+',
                        help='request urls, you can offer more than one urls, whatever the method is, '
                             'you should always provide arguments in url (just like a HttpGet request), for example '
                             '\'http://example.com?arg1=value1&arg2=value2\', when you use HttpPost method, the '
                             'arguments will be parsed to json format and sent to \'http://example.com\' as a payload.')
    args = parser.parse_args()
    launcher = CmdLauncher(duration=args.duration, worker_num=args.worker_num, method=args.method, urls=args.urls)
    launcher.launch()


def web_main():
    parser = argparse.ArgumentParser(description='CamelStraw web interface tool.')
    parser.add_argument('-h', '--host', metavar='Host', dest='host', action='store', nargs='?',
                        default='127.0.0.1', type=str, help='the host serves the web interface, '
                                                            'default value is \'127.0.0.1\'.')
    parser.add_argument('-p', '--port', metavar='Port', dest='port', action='store', nargs='?',
                        default=4869, type=int, help='the port the web service listens to, default value is 4869.')
    args = parser.parse_args()
    launcher = WebLauncher(host=args.host, port=args.port)
    launcher.launch()
