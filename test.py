from server import Server

s = Server()

s.start()
import time
time.sleep(10)
s.save()
s.join()
