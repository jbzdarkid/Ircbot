from time import time
from datetime import datetime
from os import path, mkdir
from traceback import format_exc, format_exception, print_exc

root = path.dirname(path.abspath(__file__)) + '/logs/'
try:
  mkdir(root)
except FileExistsError:
  pass

filename = root + datetime.fromtimestamp(time()).strftime('%Y_%m_%d_%H_%M_%S.log')

def log(line):
  with open(filename, 'ab') as logfile:
    try:
      clean_line = line.strip() + '\n'
      logfile.write(line.encode('utf-8'))
    except:
      print_exc()

def log_tk_exception(*args):
  exc_text = ''.join(format_exception(*args))
  print(exc_text)
  log(exc_text)

def log_exception():
  print_exc()
  log(format_exc())
