
import logging
import time


operf = logging.FileHandler(filename='operation.log', mode='a', encoding='utf-8')
operf.setLevel(logging.INFO)
fmt = logging.Formatter(fmt="%(levelname)s:%(name)s:%(module)s:%(message)s")
operf.setFormatter(fmt)

slogf = logging.FileHandler(filename='server.log', mode='a', encoding='utf-8')
slogf.setLevel(logging.INFO)
fmt1 = logging.Formatter(fmt="%(levelname)s:%(name)s:%(module)s:%(message)s")
slogf.setFormatter(fmt1)


oper = logging.Logger(name='operation', level=logging.INFO)
oper.addHandler(operf)

slog = logging.Logger(name='server', level=logging.INFO)
slog.addHandler(slogf)

class log:
    def bot(msg):
        global oper
        print(
            f'{time.asctime( time.localtime(time.time()) )}:[Telegram]: {msg}')
        oper.info(
            f'{time.asctime( time.localtime(time.time()) )}:[Telegram]: {msg} \n')

    def server(msg):
        global slog
        print(
            f'{time.asctime( time.localtime(time.time()) )}:[ Server ]: {msg}')
        slog.info(
            f'{time.asctime( time.localtime(time.time()) )}:[ Server ]: {msg}')

    def error(msg):
        global oper
        oper.error(
            f'{time.asctime( time.localtime(time.time()) )}:[ System ]: {msg}'
        )
