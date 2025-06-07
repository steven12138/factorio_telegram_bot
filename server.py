import threading
import os
import subprocess
from logger import log
from textwrap import dedent


class Server(threading.Thread):
    """Thread wrapper around a Factorio server process."""

    def __init__(self, port: int):
        super().__init__()
        self.dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'server')
        self.port = port
        self.saving = False
        self.proc: subprocess.Popen | None = None
        self.output = ""
        self.output_lines: list[str] = []

    def send_command(self, cmd: str) -> int:
        """Send a raw command to the Factorio server."""
        if self.proc is None:
            return -1
        self.proc.stdin.write((cmd + "\n").encode('utf-8'))
        self.proc.stdin.flush()
        return 0

    def save(self):
        if self.saving:
            return -1
        self.saving = True
        self.send_command('/save')
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
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )
        for line in self.proc.stdout:
            if line:
                self.output = dedent(line.strip())
                self.output_lines.append(self.output)
                log.server(self.output)
        self.proc = None
