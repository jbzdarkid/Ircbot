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

#@badges=broadcaster/1,subscriber/0;color=#FFFF00;display-name=Jbzdarkid;emotes=;id=45de0c28-b080-4a63-8866-28db15703985;mod=0;room-id=18925492;subscriber=1;tmi-sent-ts=1530238644213;turbo=0;user-id=18925492;user-type= :jbzdarkid!jbzdarkid@jbzdarkid.tmi.twitch.tv PRIVMSG #jbzdarkid :test
CHAT_MSG = compile('^@(.*?):(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG #' + my_username + ' :(.*)\r\n$')

#:jtv!jtv@jtv.tmi.twitch.tv PRIVMSG jbzdarkid :PunchEmileAgainPlease is now hosting you.
JTV_MSG = compile('^:(\w+)!\w+@\w+.tmi.twitch.tv PRIVMSG ' + my_username + ' :(.*)\r\n$')

def draw_text(text, color='black'):
  print(text)
  global chat_pos
  canvas.create_text(chat_pos, anchor=NW, font='courier', text=text, fill=color)
  chat_pos = (chat_pos[0] + len(text)*10, chat_pos[1])
  print(chat_pos)

def draw_image(image):
  print(image.width())
  global chat_pos
  canvas.create_image(chat_pos, image=image, anchor=W)
  chat_pos = (chat_pos[0] + image.width(), chat_pos[1])
  print(chat_pos)

def draw_newline():
  global chat_pos
  chat_pos = (0, chat_pos[1] + 28)
  x1, y1, x2, y2 = canvas.cget('scrollregion').split(' ')
  canvas.config(scrollregion=(int(x1), int(y1), int(x2), chat_pos[1]))
  # TODO: Scroll down
  # top, bottom = vbar.get()
  # vbar.set(top, 1.0)
  # text_label.see(END) # TODO: Doesn't respect if you are currently scrolling
  
loaded_images = {}
def load_image(id):
  global loaded_images
  # Twitch images. /2.0 and /3.0 are larger images.
  img_file = request.urlopen('https://static-cdn.jtvnw.net/emoticons/v1/' + id + '/1.0')
  pil_image = PIL_Image.open(BytesIO(img_file.read()))
  tk_image = ImageTk.PhotoImage(pil_image)
  loaded_images[id] = (pil_image, tk_image)
  
  
  # Can't access subscriber badges w/o OAUTH2 token. URL is https://api.twitch.tv/kraken/chat/jbzdarkid/badges?oauth_token=blah
  
  # https://static-cdn.jtvnw.net/chat-badges/[].png
  # globalmod, admin, broadcaster, mod, staff, turbo

  # https://api.frankerfacez.com/v1/set/global
  # https://api.frankerfacez.com/v1/room/jbzdarkid
  # https://api.frankerfacez.com/v1/badges
  # https://api.frankerfacez.com/v1/badge/supporter

  # https://api.betterttv.net/2/emotes
  # https://api.betterttv.net/2/channels/jbzdarkid

def on_chat(line_data, username, message):
  message = ''.join([c for c in message if ord(c) <= 0xFFFF]) # TODO: Currently filtering out emoji

  # TODO: line_data['bits'] (int) ???

  draw_text(datetime.now().strftime('%I:%M:%S') + ' ') # Draw the timestamp

  # TODO: Draw badges here

  if 'display-name' not in line_data or line_data['display-name'] == '':
    line_data['display-name'] = username
  if 'color' not in line_data or line_data['color'] == '' or True:
    line_data['color'] = 'black'

  draw_text(line_data['display-name'], line_data['color'])
  draw_text(':')
  
  message_pos = 0
  if 'emotes' in line_data and line_data['emotes'] != '':
    emotes = findall('(\d+):(\d+)-(\d+)', line_data['emotes'])
    emotes = [[x, int(y), int(z)] for x, y, z in emotes]
    emotes.sort(key = lambda s: s[1])
    for id, start, end in emotes:
      if id not in loaded_images:
        load_image(id)

      draw_text(message[message_pos:start])
      draw_image(loaded_images[id][1])
      message_pos = end + 1
  draw_text(message[message_pos:])

  draw_newline()

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
        on_chat({}, 'Twitch', m.group(2))
      elif CHAT_MSG.match(data):
        m = CHAT_MSG.match(data)
        line_data = {}
        for kvp in m.group(1).split(';'):
          line_data[kvp.split('=')[0]] = kvp.split('=')[1]
        print(line_data)
        on_chat(line_data, m.group(2), m.group(3))
      else:
        print('Unable to parse message: "' + data + '"')

        
def ping(*args):
  send_message('pong')
  
def debug():
  on_chat({}, 'Ircbot', 'DEBUG')
  
def kappa():
  on_chat({}, 'Ircbot', 'abc Kappa ;) 123')

if __name__ == '__main__':
  # Connect to twitch
  irc = socket()
  irc.connect(('irc.chat.twitch.tv', 6667))
  send(irc, 'PASS oauth:' + chat_token)
  send(irc, 'NICK ' + my_username)
  irc.recv(4096) # You are in a maze of twisty passages

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
  
  irc.setblocking(0)

  # Create the UI
  root = Tk()
  root.title('Ircbot')
  frame = Frame(root)
  frame.pack(expand=True, fill='both')
  canvas = Canvas(frame, bg='white', scrollregion=(0, 0, 500, 0))
  canvas.pack(side='left', expand=True, fill='both')
  # TODO: On mac, this should be just "event.delta"
  root.bind_all('<MouseWheel>', lambda event: canvas.yview_scroll(event.delta//-120, 'units'))
  scrollbar = Scrollbar(frame, orient='vertical', command=canvas.yview)
  scrollbar.pack(side='right', fill='y')
  canvas.config(yscrollcommand=scrollbar.set)
  Button(root, text='Ping', fg='red', command=ping).pack(side='bottom')
  Button(root, text='Debug', fg='red', command=debug).pack(side='bottom')
  Button(root, text='Kappa', fg='red', command=kappa).pack(side='bottom')
  
  chat_pos = (0, 0)
  draw_text('Chat bot started on ' + datetime.now().strftime('%m/%d/%Y'))
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
