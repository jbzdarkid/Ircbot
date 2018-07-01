from PIL import Image as PIL_Image
from PIL import ImageTk
from datetime import datetime
from io import BytesIO
from urllib import request
from tkinter import *

DEFAULT_TEXT = 'white'
emotes = {}
chat_pos = (2, 9) # Half-line height

def draw_text(text, color):
  global chat_pos
  canvas.update()
  if chat_pos[0] + len(text)*10 > canvas.winfo_width():
    draw_newline()
  canvas.create_text(chat_pos, anchor='w', font='courier', text=text, fill=color)
  chat_pos = (chat_pos[0] + len(text)*10, chat_pos[1])

loaded_images = {}
def draw_image(name, url):
  global loaded_images
  if name not in loaded_images:
    try:
      img_bytes = BytesIO(request.urlopen(url).read())
    except:
      print('Failed to load image [%s] from url [%s]' % (name, url))
      return
    loaded_images[name] = ImageTk.PhotoImage(PIL_Image.open(img_bytes))
    print('Loaded image [%s] from url [%s]' % (name, url))
  image = loaded_images[name]
  global chat_pos
  canvas.update()
  if chat_pos[0]  + image.width() > canvas.winfo_width():
    draw_newline()
  canvas.create_image(chat_pos, image=image, anchor='w')
  chat_pos = (chat_pos[0] + image.width(), chat_pos[1])

def draw_newline():
  global chat_pos
  chat_pos = (0, chat_pos[1] + 28)
  canvas.config(scrollregion=(0, 0, 0, chat_pos[1]))
  canvas.yview_moveto(1.0)

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

def debug():
  on_chat({}, 'Ircbot', 'DEBUG')

def kappa():
  on_chat({'emotes':''}, 'Ircbot', 'abc Kappa ;) 123')

def start_ui():
  global canvas
  global root
  # Create the UI
  root = Tk()
  root.title('Ircbot')
  root.geometry('500x500')
  Button(root, text='Debug', fg='red', command=debug).pack(side='bottom')
  Button(root, text='Kappa', fg='red', command=kappa).pack(side='bottom')
  canvas = Canvas(root, bg='black')
  canvas.pack(side='left', expand=True, fill='both')
  # TODO: On mac, this should be just "event.delta"
  root.bind_all('<MouseWheel>', lambda event: canvas.yview_scroll(event.delta//-120, 'units'))
  scrollbar = Scrollbar(root, orient='vertical', command=canvas.yview)
  scrollbar.pack(side='right', fill='y')
  canvas.config(yscrollcommand=scrollbar.set)

  draw_text('Chat bot started on ' + datetime.now().strftime('%m/%d/%Y'), DEFAULT_TEXT)
  draw_newline()
  
  root.mainloop()