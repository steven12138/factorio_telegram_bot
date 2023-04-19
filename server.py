import threading
import os
import subprocess
from logger import log
from textwrap import dedent
import select


class Server(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.dir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'server')
        self.port = port
        self.saving = False
        self.proc = None
        self.output = ""

    def save(self):
        if self.saving:
            return -1
        self.saving = True
        self.proc.stdin.write("/save\n".encode('utf-8'))
        self.proc.stdin.flush()
        while True:
            if self.output.__contains__("Saving finished"):
                self.saving = False
                return 0

    def stop(self):
        if self.proc == None:
            return -1
        self.proc.send_signal(subprocess.signal.SIGINT)
        while True:
            if self.output.__contains__("Goodbye"):
                self.proc = None
                return 0

    def awake(self):
        if self.proc is not None:
            return -1
        self.start()
        while True:
            if self.proc is not None:
                break
        while True:
            if self.output.__contains__("Hosting") or self.output.__contains__("Matching server connection resumed"):
                return 0

    def run(self):
        self.proc = subprocess.Popen(
            [
                os.path.join(self.dir, 'bin/x64/factorio'),
                '--start-server', os.path.join(self.dir, 'saves/sss.zip'),
                '--server-settings', os.path.join(self.dir,
                                                  'config/server-settings.json'),
                '--port', str(self.port)
            ],
            cwd=self.dir,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        while True:
            output = self.proc.stdout.readline()
            if self.proc is None or (not output and self.proc.poll() is not None):
                break
            if output:
                self.output = dedent(output.decode('utf-8').split('\n')[0])
                log.server(self.output)
