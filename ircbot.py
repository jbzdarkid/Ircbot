# Known bug: "/me Kappa" will not send emote data (25:0-4), so I can't detect that "Kappa" is an emote. If "Kappa" is already known to be an emote, then this causes no problems.

from ircbot_ui import on_chat, start_ui, emotes
from json import load
from re import compile, findall
from select import select
from socket import socket
from threading import Thread
from urllib import request
from random import randint
from time import sleep

my_username = 'jbzdarkid'

#@badges=broadcaster/1,subscriber/0;color=#FFFF00;display-name=Jbzdarkid;emotes=;id=45de0c28-b080-4a63-8866-28db15703985;mod=0;room-id=18925492;subscriber=1;tmi-sent-ts=1530238644213;turbo=0;user-id=18925492;user-type= :jbzdarkid!jbzdarkid@jbzdarkid.tmi.twitch.tv PRIVMSG #jbzdarkid :test
CHAT_MSG = compile('^@(.*?):(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG #' + my_username + ' :(.*)\r\n$')

#:jtv!jtv@jtv.tmi.twitch.tv PRIVMSG jbzdarkid :PunchEmileAgainPlease is now hosting you.
JTV_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG ' + my_username + ' :(.*)\r\n$')

#:toad1750!toad1750@toad1750.tmi.twitch.tv JOIN #jbzdarkid
JOIN_MSG = compile(':(\w+)!\w+@\w+.tmi.twitch.tv JOIN #(\w+)\r\n')

#:shoutgamers!shoutgamers@shoutgamers.tmi.twitch.tv PART #jbzdarkid
PART_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PART #(\w+)\r\n$')

def load_ffz_global():
  while 1:
    try:
      raw = load(request.urlopen('https://api.frankerfacez.com/v1/set/global'))
      break
    except:
      sleep(5000)
  print('Loaded global FFZ emotes')
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
  print('Loaded FFZ emotes for ' + username)
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
  print('Loaded global BTTV emotes')
  for emote in raw['emotes']:
    emotes[emote['code']] = 'https://cdn.betterttv.net/emote/%s/1x' % emote['id']

def load_bttv_channel(username):
  while 1:
    try:
      raw = load(request.urlopen('https://api.beetterttv.net/2/channels/' + username))
      break
    except:
      sleep(5000)
  print('Loaded BTTV emotes for ' + username)
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
  while ui_running: # Wait on messages from IRC
    # Wait for new data so that control-C works
    ready = select([irc], [], [], 1) # 1 second timeout
    if ready[0]:
      data = irc.recv(4096).decode('utf-8')
      if data == 'PING :tmi.twitch.tv\r\n':
        send(irc, 'PONG :tmi.twitch.tv')
        continue
      elif JTV_MSG.match(data):
        m = JTV_MSG.match(data)
        on_chat({}, '', m.group(2))
      elif CHAT_MSG.match(data):
        m = CHAT_MSG.match(data)
        line_data = {}
        for kvp in m.group(1).split(';'):
          line_data[kvp.split('=')[0]] = kvp.split('=')[1]
        print(line_data)
        on_chat(line_data, m.group(2), m.group(3))
      elif JOIN_MSG.search(data):
        for m in JOIN_MSG.finditer(data):
          if m.group(2) == my_username:
            on_join(m.group(1))
      elif PART_MSG.match(data):
        m = PART_MSG.match(data)
        if m.group(2) == my_username:
          on_part(m.group(1))
      else:
        print('Unable to parse message: """' + data + '"""')

if __name__ == '__main__':
  # Connect to twitch
  irc = socket()
  print('<97>')
  irc.connect(('irc.chat.twitch.tv', 6667))
  print('<99>')
  # send(irc, 'PASS asdf')
  # send(irc, 'NICK ' + my_username)
  send(irc, 'NICK justinfan%05d' % randint(0, 99999))
  irc.recv(4096) # You are in a maze of twisty passages
  print('<103>')

  send(irc, 'CAP REQ :twitch.tv/membership')
  irc.recv(1024) # CAP * ACK :twitch.tv/membership
  print('<107>')
  send(irc, 'CAP REQ :twitch.tv/tags')
  irc.recv(1024) # CAP * ACK :twitch.tv/tags
  print('<110>')
  send(irc, 'CAP REQ :twitch.tv/commands')
  irc.recv(1024) # CAP * ACK :twitch.tv/commands
  print('<116>')

  send(irc, 'JOIN #' + my_username)
  irc.recv(1024) # /JOIN
  irc.recv(1024) # End of /NAMES list
  print('<118>')
  send(irc, 'JOIN #jtv')
  irc.recv(1024) # /JOIN
  irc.recv(1024) # End of /NAMES list
  print('<122>')

  irc.setblocking(0)

  threads = []
  threads.append(Thread(target=load_ffz_global))
  threads.append(Thread(target=load_ffz_channel, args=(my_username,)))
  threads.append(Thread(target=load_bttv_global))
  # threads.append(Thread(target=load_bttv_channel, args=(my_username,)))

  ui_running = True
  thread = Thread(target=chat_listen)
  thread.daemon = True
  threads.append(thread)

  for thread in threads:
    thread.start()
  start_ui()
  ui_running = False
  for thread in threads:
    thread.join()

# TODO: These don't work.

# def send_whisper(username, message):
#   send(irc, 'PRIVMSG #jtv :/w ' + username + ' ' + message)

# def send_message(message):
#   send(irc, 'PRIVMSG #jtv ' + my_username + ' :' + message)
