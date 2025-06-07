import sys
import threading
from server import Server


def main(port=34197):
    server = Server(port)
    server.start()
    print("Factorio server starting. Type commands and press Enter to send. Ctrl+C to quit.")
    try:
        while server.proc is None:
            pass
        while True:
            cmd = input('> ')
            if cmd.strip().lower() in {'exit', 'quit'}:
                break
            server.send_command(cmd)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        server.join()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 34197
    main(port)
