from server import Server

s = Server(34197)

s.start()
import time
time.sleep(10)
s.save()
s.join()
