from io import BytesIO
from PIL import Image as PIL_Image
from PIL import ImageTk
from tkinter import *
from urllib import request

class ChatWindow(Canvas):
  def __init__(self, parent, *args, **kwargs):
    Canvas.__init__(self, parent, *args, **kwargs)
    scrollbar = Scrollbar(parent, orient='vertical', command=self.yview)
    scrollbar.pack(side='right', fill='y')
    self.yscrollcommand = scrollbar.set
    # self.config(yscrollcommand=scrollbar.set)
    self.bind_all('<MouseWheel>', self.onscroll)

    self.x = 2
    self.y = 9 # Half-line height
    self.loaded_images = {}
    self.previous_was_text = False
    
  def onscroll(self, event):
    # TODO: On mac, this should be just "event.delta"
    self.yview_scroll(event.delta//-120, 'units')

  def linewrap(self, length):
    self.update()
    if self.x + length > self.winfo_width():
      self.draw_newline()

  def draw_text(self, text, fill):
    if self.previous_was_text:
      self.previous_was_text = False
      self.draw_text(' ', fill)

    self.linewrap(len(text)*10)
    self.create_text((self.x, self.y), anchor='w', font='courier', text=text, fill=fill)
    self.x += len(text)*10
    self.previous_was_text = True

  def draw_image(self, name, url):
    if name not in self.loaded_images:
      try:
        img_bytes = BytesIO(request.urlopen(url).read())
      except:
        print('Failed to load image [%s] from url [%s]' % (name, url))
        return
      self.loaded_images[name] = ImageTk.PhotoImage(PIL_Image.open(img_bytes))
      print('Loaded image [%s] from url [%s]' % (name, url))
    image = self.loaded_images[name]
    self.linewrap(image.width())
    self.create_image((self.x, self.y), image=image, anchor='w')
    self.x += image.width()
    self.previous_was_text = False

  def draw_newline(self):
    self.x = 0
    self.y += 28 # Standard twitch image height
    self.scrollregion = (0, 0, 0, self.y)
    # self.config(scrollregion=(0, 0, 0, self.y))
    self.yview_moveto(1.0)
    self.previous_was_text = False
