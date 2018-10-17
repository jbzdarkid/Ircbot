# Known bug: "/me Kappa" will not send emote data (25:0-4), so I can't detect that "Kappa" is an emote. If "Kappa" is already known to be an emote, then this causes no problems.

# TODO: Split this file up somehow. Will be easier once I have more UI features
# TODO: Userlist
# TODO: Fix #jtv channel to sign in with your real username
# TODO: Extra whitespace on users with no badge -- should I just remove the auto-whitespace removal?
# TODO: Clickable links / Link title previews
#
#
# Exception in thread Thread-4:
# Traceback (most recent call last):
  # File "C:\Program Files (x86)\Python36-32\lib\threading.py", line 916, in _bootstrap_inner
    # self.run()
  # File "C:\Program Files (x86)\Python36-32\lib\threading.py", line 864, in run
    # self._target(*self._args, **self._kwargs)
  # File "Documents\GitHub\Ircbot\ircbot.py", line 118, in chat_listen
    # on_chat(line_data, m.group(2), m.group(3))
  # File "C:\Users\localhost\Documents\GitHub\Ircbot\ircbot_ui.py", line 85, in on_chat
    # chat_window.draw_image('emote_' + word, emotes[word])
  # File "C:\Users\localhost\Documents\GitHub\Ircbot\ircbot_chat_window.py", line 54, in draw_image
    # self.linewrap(image.width())
# AttributeError: 'NoneType' object has no attribute 'width'

from json import load
from random import randint
from re import compile, findall
from select import select
from socket import socket
from threading import Thread
from time import sleep
from urllib import request
from tkinter import *
from ircbot_chat_window import ChatWindow, emotes
from my_logger import log_tk_exception, log, log_exception
from datetime import datetime

my_username = 'jbzdarkid'
from my_token import my_token

#@badges=broadcaster/1,subscriber/0;color=#FFFF00;display-name=Jbzdarkid;emotes=;id=45de0c28-b080-4a63-8866-28db15703985;mod=0;room-id=18925492;subscriber=1;tmi-sent-ts=1530238644213;turbo=0;user-id=18925492;user-type= :jbzdarkid!jbzdarkid@jbzdarkid.tmi.twitch.tv PRIVMSG #jbzdarkid :test
CHAT_MSG = compile('^@(.*?):(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG #' + my_username + ' :(.*)\r\n$')

#:jtv!jtv@jtv.tmi.twitch.tv PRIVMSG jbzdarkid :PunchEmileAgainPlease is now hosting you.
JTV_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG ' + my_username + ' :(.*)\r\n$')

#:toad1750!toad1750@toad1750.tmi.twitch.tv JOIN #jbzdarkid
JOIN_MSG = compile(':(\w+)!\w+@\w+.tmi.twitch.tv JOIN #(\w+)\r\n')

#:shoutgamers!shoutgamers@shoutgamers.tmi.twitch.tv PART #jbzdarkid
PART_MSG = compile(':(\w+)!\w+@\w+.tmi.twitch.tv PART #(\w+)\r\n')

def load_ffz_global():
  while 1:
    try:
      raw = load(request.urlopen('https://api.frankerfacez.com/v1/set/global'))
      break
    except:
      sleep(5000)
  log('Loaded global FFZ emotes')
  set_id = str(raw['default_sets'][0])
  for emote in raw['sets'][set_id]['emoticons']:
    emotes[emote['name']] = 'https://cdn.frankerfacez.com/emoticon/%s/1' % emote['id']

def load_ffz_channel(username):
  while 1:
    try:
      raw = load(request.urlopen('https://api.frankerfacez.com/v1/room/' + username))
      break
    except:
      sleep(5000)
  log('Loaded FFZ emotes for ' + username)
  set_id = str(raw['room']['set'])
  for emote in raw['sets'][set_id]['emoticons']:
    emotes[emote['name']] = 'https://cdn.frankerfacez.com/emoticon/%s/1' % emote['id']

def load_bttv_global():
  while 1:
    try:
      raw = load(request.urlopen('https://api.betterttv.net/2/emotes'))
      break
    except:
      sleep(5000)
  log('Loaded global BTTV emotes')
  for emote in raw['emotes']:
    emotes[emote['code']] = 'https://cdn.betterttv.net/emote/%s/1x' % emote['id']

def load_bttv_channel(username):
  while 1:
    try:
      raw = load(request.urlopen('https://api.beetterttv.net/2/channels/' + username))
      break
    except:
      sleep(5000)
  log('Loaded BTTV emotes for ' + username)
  for emote in raw['emotes']:
    emotes[emote['code']] = 'https://cdn.betterttv.net/emote/%s/1x' % emote['id']

userlist = set()
def on_join(user):
  if user not in userlist:
    print('JOIN: ' + user)
    userlist.add(user)
def on_part(user):
  print('PART: ' + user)

def send(irc, message):
  irc.send(message.encode('utf-8') + b'\r\n')

def chat_listen():
  global chat_window
  while ui_running: # Wait on messages from IRC
    try:
      # Wait for new data so that control-C works
      ready = select([irc], [], [], 1) # 1 second timeout
      if ready[0]:
        data = irc.recv(4096).decode('utf-8')
        log(data)
        if data == 'PING :tmi.twitch.tv\r\n':
          send(irc, 'PONG :tmi.twitch.tv')
          continue
        elif JTV_MSG.match(data):
          m = JTV_MSG.match(data)
          chat_window.on_chat({}, '', m.group(2))
        elif CHAT_MSG.match(data):
          m = CHAT_MSG.match(data)
          line_data = {}
          for kvp in m.group(1).split(';'):
            line_data[kvp.split('=')[0]] = kvp.split('=')[1]
          chat_window.on_chat(line_data, m.group(2), m.group(3))
        elif JOIN_MSG.search(data):
          for m in JOIN_MSG.finditer(data):
            if m.group(2) == my_username:
              on_join(m.group(1))
        elif PART_MSG.search(data):
          for m in PART_MSG.finditer(data):
            if m.group(2) == my_username:
              on_join(m.group(1))
        else:
          log('Unable to parse message!\n')
    except:
      log_exception()
      sleep(1000)


def debug():
  global chat_window
  chat_window.on_chat({'tmi-sent-ts':'1531588971'}, 'Ircbot', 'DEBUG')

def error():
  global chat_window
  chat_window.on_chat('asdfasdf')

def test():
  send_message('test')

# TODO: test send_whisper
def send_whisper(username, message):
  send(irc, 'PRIVMSG #jtv :/w ' + username + ' ' + message)

def send_message(message):
  send(irc, 'PRIVMSG #' + my_username + ' :' + message)
  global chat_window
  chat_window.on_chat({'tmi-sent-ts':'1531588971'}, my_username, message)

def start_ui():
  global reminders
  global chat_window
  # Create the UI
  root = Tk()
  root.title('Ircbot')
  root.geometry('1000x1000+0+0')
  root.report_callback_exception = log_tk_exception
  # root.iconbitmap('favicon.ico')
  reminders = Frame(root, width=250)
  reminders.pack(side='left')

  """
  Label(root, text='Send message:').pack(side='bottom')
  chat_message = StringVar()
  Entry(root, textvariable=chat_message).pack(side='bottom')
  def parse_entry(chat_message):
    self.send_message(chat_message.get())

  root.bind('<Return>', lambda: parse_entry(chat_message))
  """

  Button(root, text='Debug', fg='red', command=debug).pack(side='left')
  Button(root, text='Error', fg='red', command=error).pack(side='left')
  Button(root, text='Test', fg='red', command=test).pack(side='left')
  chat_window = ChatWindow(root, reminders, bg='black')
  chat_window.pack(side='left', expand=True, fill='both')
  chat_window.draw_text('Chat bot started on ' + datetime.now().strftime('%m/%d/%Y'))
  chat_window.draw_newline()

  root.mainloop()

if __name__ == '__main__':
  # Connect to twitch
  irc = socket()
  irc.connect(('irc.chat.twitch.tv', 6667))
  send(irc, 'PASS ' + my_token)
  send(irc, 'NICK ' + my_username)
#  send(irc, 'NICK justinfan%05d' % randint(0, 99999))

  send(irc, 'CAP REQ :twitch.tv/membership')
  send(irc, 'CAP REQ :twitch.tv/tags')
  send(irc, 'CAP REQ :twitch.tv/commands')
  send(irc, 'JOIN #' + my_username)
  send(irc, 'JOIN #jtv')

  irc.setblocking(0)

  threads = []
  threads.append(Thread(target=load_ffz_global, name='FFZ_Global'))
  threads.append(Thread(target=load_ffz_channel, name='FFZ_Channel', args=(my_username,)))
  threads.append(Thread(target=load_bttv_global, name='BTTV_Global'))
  # threads.append(Thread(target=load_bttv_channel, name='BTTV_Channel', args=(my_username,)))

  ui_running = True
  thread = Thread(target=chat_listen, name='Chat_Listen')
  thread.daemon = True
  threads.append(thread)

  for thread in threads:
    thread.start()

  start_ui()
  # Return from start_ui means it was closed, so shut down
  ui_running = False
  for thread in threads:
    thread.join()
