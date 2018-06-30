# Known bug: "/me Kappa" will not send emote data (25:0-4), so I can't detect that "Kappa" is an emote. If "Kappa" is already known to be an emote, then this causes no problems.

from PIL import Image as PIL_Image
from PIL import ImageTk
from config import chat_token, my_username
from datetime import datetime
from io import BytesIO
from re import compile, findall
from select import select
from socket import socket
from threading import Thread
from tkinter import *
from urllib import request
from json import load

#@badges=broadcaster/1,subscriber/0;color=#FFFF00;display-name=Jbzdarkid;emotes=;id=45de0c28-b080-4a63-8866-28db15703985;mod=0;room-id=18925492;subscriber=1;tmi-sent-ts=1530238644213;turbo=0;user-id=18925492;user-type= :jbzdarkid!jbzdarkid@jbzdarkid.tmi.twitch.tv PRIVMSG #jbzdarkid :test
CHAT_MSG = compile('^@(.*?):(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG #' + my_username + ' :(.*)\r\n$')

#:jtv!jtv@jtv.tmi.twitch.tv PRIVMSG jbzdarkid :PunchEmileAgainPlease is now hosting you.
JTV_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG ' + my_username + ' :(.*)\r\n$')

#:toad1750!toad1750@toad1750.tmi.twitch.tv JOIN #jbzdarkid
JOIN_MSG = compile(':(\w+)!\w+@\w+.tmi.twitch.tv JOIN #(\w+)\r\n')

#:shoutgamers!shoutgamers@shoutgamers.tmi.twitch.tv PART #jbzdarkid
PART_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PART #(\w+)\r\n$')

DEFAULT_TEXT = 'white'

emotes = {}

def draw_text(text, color):
  global chat_pos
  canvas.create_text(chat_pos, anchor='w', font='courier', text=text, fill=color)
  chat_pos = (chat_pos[0] + len(text)*10, chat_pos[1])

loaded_images = {}
def draw_image(name, url):
  global loaded_images
  if name not in loaded_images:
    img_bytes = BytesIO(request.urlopen(url).read())
    loaded_images[name] = ImageTk.PhotoImage(PIL_Image.open(img_bytes))
    print('Loaded image [%s] from url [%s]' % (name, url))
  image = loaded_images[name]
  global chat_pos
  canvas.create_image(chat_pos, image=image, anchor='w')
  chat_pos = (chat_pos[0] + image.width(), chat_pos[1])

def draw_newline():
  global chat_pos
  chat_pos = (0, chat_pos[1] + 28)
  canvas.config(scrollregion=(0, 0, 0, chat_pos[1]))
  canvas.yview_moveto(1.0)

def load_ffz_global():
  global emotes
  print('Loding global FFZ emotes...')
  raw = load(request.urlopen('https://api.frankerfacez.com/v1/set/global'))
  set_id = str(raw['default_sets'][0])
  for emote in raw['sets'][set_id]['emoticons']:
    emotes[emote['name']] = 'https:' + emote['urls']['1'] # ['2'] and ['4'] are larger.

def load_ffz_channel(username):
  global emotes
  print('Loding FFZ emotes for ' + username + '...')
  raw = load(request.urlopen('https://api.frankerfacez.com/v1/room/' + username))
  set_id = str(raw['room']['set'])
  for emote in raw['sets'][set_id]['emoticons']:
    emotes[emote['name']] = 'https:' + emote['urls']['1'] # ['2'] and ['4'] are larger.

def load_bttv_global():
  global emotes
  print('Loding global BTTV emotes...')
  raw = load(request.urlopen('https://api.betterttv.net/2/emotes'))
  for emote in raw['emotes']:
    emotes[emote['code']] = 'https://cdn.betterttv.net/emote/' + emote['id'] + '/1x'

def load_bttv_channel(username):
  global emotes
  print('Loding BTTV emotes for ' + username + '...')
  raw = load(request.urlopen('https://api.beetterttv.net/2/channels/' + username))
  for emote in raw['emotes']:
    emotes[emote['code']] = 'https://cdn.betterttv.net/emote/' + emote['id'] + '/1x'

def on_chat(line_data, username, message):
  global emotes
  
  # https://stackoverflow.com/a/40223212
  def to_emoji(char):
    assert ord(char) > 0xFFFF
    encoded = char.encode('utf-16-le')
    return (
      chr(int.from_bytes(encoded[:2], 'little')) + 
      chr(int.from_bytes(encoded[2:], 'little')))
    
  message = ''.join([c if ord(c) <= 0xFFFF else to_emoji(c) for c in message])

  # Parse twitch emote names
  if 'emotes' in line_data and line_data['emotes'] != '':
    for emote in line_data['emotes'].split('/'):
      id, emote = emote.split(':')
      start, end = emote.split('-')
      name = message[int(start):int(end)+1]
      # Twitch images. /2.0 and /3.0 are larger images.
      if name not in emotes:
        emotes[name] = 'https://static-cdn.jtvnw.net/emoticons/v1/' + id + '/1.0'
        print(emotes.keys())

  # TODO: line_data['bits'] (int) ???

  draw_text(datetime.now().strftime('%I:%M:%S') + ' ', DEFAULT_TEXT) # Draw the timestamp

  if 'badges' in line_data and line_data['badges'] != '':
    for badge in line_data['badges'].split(','):
      name, _ = badge.split('/')
      if name == 'subscriber':
        # TODO: This guid comes from somewhere...
        url = 'https://static-cdn.jtvnw.net/badges/v1/5d9f2208-5dd8-11e7-8513-2ff4adfae661/1'
      else:
        url = 'https://static-cdn.jtvnw.net/chat-badges/' + name + '.png'
      draw_image('badge_' + name, url)

  if 'display-name' not in line_data or line_data['display-name'] == '':
    line_data['display-name'] = username
  if 'color' not in line_data or line_data['color'] == '':
    line_data['color'] = DEFAULT_TEXT

  draw_text(line_data['display-name'], line_data['color'])

  if message.startswith('\x01ACTION '):
    message = message[8:-1] # Trailing \x01 as well
    # Keep username color
  else:
    line_data['color'] = DEFAULT_TEXT
    draw_text(':', line_data['color'])
  
  previous_word_was_text = False
  for word in message.split(' '):
    if word in emotes:
      draw_image('emote_' + word, emotes[word])
      previous_word_was_text = False
    else:
      if previous_word_was_text:
        draw_text(' ', line_data['color'])
      draw_text(word, line_data['color'])
      previous_word_was_text = True
  draw_newline()

# TODO: Userlist?
def on_join(user):
  print('JOIN: ' + user)
def on_part(user):
  print('PART: ' + user)

def send(irc, message):
  irc.send(message.encode('utf-8') + b'\r\n')

def chat_listen():
  global irc
  global ui_running
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

def ping(*args):
  send_message('pong')

def debug():
  on_chat({}, 'Ircbot', 'DEBUG')

def kappa():
  on_chat({'emotes':''}, 'Ircbot', 'abc Kappa ;) 123')

if __name__ == '__main__':
  # Connect to twitch
  irc = socket()
  print('<202>')
  irc.connect(('irc.chat.twitch.tv', 6667))
  print('<204>')
  send(irc, 'PASS oauth:' + chat_token)
  send(irc, 'NICK ' + my_username)
  irc.recv(4096) # You are in a maze of twisty passages
  print('<208>')

  send(irc, 'CAP REQ :twitch.tv/membership')
  irc.recv(1024) # CAP * ACK :twitch.tv/membership
  send(irc, 'CAP REQ :twitch.tv/tags')
  irc.recv(1024) # CAP * ACK :twitch.tv/tags

  send(irc, 'JOIN #' + my_username)
  irc.recv(1024) # /JOIN
  irc.recv(1024) # End of /NAMES list
  send(irc, 'JOIN #jtv')
  irc.recv(1024) # /JOIN
  irc.recv(1024) # End of /NAMES list
  print('<220>')

  irc.setblocking(0)

  load_ffz_global()
  load_ffz_channel(my_username)
  load_bttv_global()
  # load_bttv_channel(my_username)
  
  # Create the UI
  root = Tk()
  root.title('Ircbot')
  root.geometry('500x500')
  frame = Frame(root)
  frame.pack(expand=True, fill='both')
  canvas = Canvas(frame, bg='black')
  canvas.pack(side='left', expand=True, fill='both')
  # TODO: On mac, this should be just "event.delta"
  root.bind_all('<MouseWheel>', lambda event: canvas.yview_scroll(event.delta//-120, 'units'))
  scrollbar = Scrollbar(frame, orient='vertical', command=canvas.yview)
  scrollbar.pack(side='right', fill='y')
  canvas.config(yscrollcommand=scrollbar.set)
  Button(root, text='Ping', fg='red', command=ping).pack(side='bottom')
  Button(root, text='Debug', fg='red', command=debug).pack(side='bottom')
  Button(root, text='Kappa', fg='red', command=kappa).pack(side='bottom')

  chat_pos = (2, 9) # Half-line height
  draw_text('Chat bot started on ' + datetime.now().strftime('%m/%d/%Y'), DEFAULT_TEXT)
  draw_newline()

  ui_running = True
  thread = Thread(target=chat_listen)
  thread.daemon = True
  thread.start()
  root.mainloop()
  ui_running = False
  thread.join()

# TODO: These don't work.

# def send_whisper(username, message):
#   send(irc, 'PRIVMSG #jtv :/w ' + username + ' ' + message)

# def send_message(message):
#   send(irc, 'PRIVMSG #jtv ' + my_username + ' :' + message)
