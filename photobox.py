from gpiozero import Button, DigitalOutputDevice
from time import sleep
from threading import Timer
import configparser
import os.path
import subprocess

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PhotoBox:
  """My PhotoBox"""
  
  # Configuration
  config = None

  FBI = "/usr/bin/fbi"
  GPHOTO = "/usr/bin/gphoto2"
  OMX = "/usr/bin/omxplayer"

  # class variables
  button_instant = None
  button_delayed = None
  switch_light_A = None
  switch_light_B = None
  
  last_picture = None

  standby_timer = None
  review_time = None
  
  
  def __init__(self):
    logger.debug("Initializing PhotoBox")
    self.config = configparser.ConfigParser()
    if os.path.isfile("photobox.ini"):
      self.config.read("photobox.ini")
    else:
      raise Exception("photobox.ini not found")

#    import pdb; pdb.set_trace()

    gpio = int(self.config['GPIO']['button_instant'])
    self.button_instant = Button(gpio, hold_time=3)
    
    gpio = int(self.config['GPIO']['button_delayed'])
    self.button_delayed = Button(gpio)
    
    gpio = int(self.config['GPIO']['switch_light_A'])
    self.switch_light_A = DigitalOutputDevice(gpio, active_high=False)
    
    gpio = int(self.config['GPIO']['switch_light_B'])
    self.switch_light_B = DigitalOutputDevice(gpio, active_high=False)

    # Prepare Standby Timer
    t = int(self.config['TIMES']['standby'])
    self.standby_timer = Timer(t * 60.0, self.standby)

    t = int(self.config['TIMES']['review'])
    self.review_timer = Timer(t * 1.0, self.active)

    # go into Active after init    
    self.active()


  def _dtb(self):
    logger.debug("_dtb: Disabling all Timers and Button activities")
    # Disable Timers and Buttons

    logger.debug("_dtb: cancel standby")
    self.standby_timer.cancel()
    t = int(self.config['TIMES']['standby'])
    self.standby_timer = Timer(t * 60.0, self.standby)

    logger.debug("_dtb: cancel review")
    self.review_timer.cancel()
    t = int(self.config['TIMES']['review'])
    self.review_timer = Timer(t * 1.0, self.active)

    logger.debug("_dtb: unset instant when_held")
    self.button_instant.when_held = None

    logger.debug("_dtb: unset instant when_pressed")
    self.button_instant.when_pressed = None

    logger.debug("_dtb: unset delayed when_pressed")
    self.button_delayed.when_pressed = None


  def _switch_lights(self, to = False):
    logger.debug("_switch_lights: Switching Lights state")
    if to is None: # toggle 
      self.switch_light_A.value = not self.switch_light_A.value
      self.switch_light_B.value = not self.switch_light_B.value
    elif to == True: # turn on
      self.switch_light_A.on()
      self.switch_light_B.on()
    else: # secure state = off
      self.switch_light_A.off()
      self.switch_light_B.off()


  def _fbi(self, file = None, folder = None, delay=15, random = 0):
    logger.debug("_fbi: Displaying image")
    # remove all old images
    os.system("killall fbi");
    
    # show new image
    fbi = self.FBI + " --noverbose -a -T 1"
    
    if random:
      fbi += " -u "
	  
    if folder is None:
      fbi += " %s " % file
    else:
      fbi += " -t %d -u %s/*" % (delay, folder)

    # TODO error handling   
    os.system(fbi)


  def _take_photo(self, delay = None):
    logger.debug("_take_photo")
    self._dtb() # disable Timer and Buttons
    
    if not delay is None:
      subprocess.Popen([self.OMX,"countdown/countdown.mp4"])
      sleep(8) # TODO: time delayed display, so that it will take a photo at 0
    
    self.last_picture = self.config['PATHS']['storage'] + "/current.png"
    # TODO create photo name and make sure it doesn't already exist
    
    # TODO parameters, and error handling (e.g. look for camera first...)
    os.system("%s --filename %s --force-overwrite --keep-raw --capture-image-and-download" % (self.GPHOTO, self.last_picture))
    
    # TODO file handling - move to self.storage, create a copy in self.backup maybe
    self.review()


  def _take_photo_delayed(self):
    logger.debug("_take_photo_delayed")
    return self._take_photo(delay=1)

  
  def _delete_photo(self):
    logger.debug("_delete_photo")
    self._dtb() # disable Timer and Buttons
    
    # Sorry, never delete anything :)  
    # But I'll mark it deleted, by moving it to another folder
    
    # TODO file handling - move to deleted folder
    
    # Display DELETED message
    
    # wait for 2 seconds so the users will notice it
    sleep(2)
           
    # become active afterwards 
    self.active()

    
  def standby(self):
    logger.debug("standby")
    self._dtb() # disable Timer and Buttons

    # Turn off Lights
    self._switch_lights(False)
    
    # FBI slideshow "standby" folder
    self._fbi(folder="fbi/standby",random=1)
    
    # Wait for any key press to become active
    self.button_instant.when_pressed = self.active
    self.button_delayed.when_pressed = self.active
  
  def active(self):
    logger.debug("active")
    self._dtb() # disable Timer and Buttons
    
    # Turn on Lights
    self._switch_lights(True)
    
    # FBI main screen
    self._fbi(file="fbi/active.png")
    
    # Wait for key press to init countdown / directly snap
    self.button_instant.when_pressed = self._take_photo
    self.button_delayed.when_pressed = self._take_photo_delayed
    
    # after self.standby minutes without state change, go to standby
    self.standby_timer.start()
    

  def review(self):
    logger.debug("review")
    self._dtb() # disable Timer and Buttons

    # Keep lights are they were
    # Show picture
    self._fbi(file=self.last_picture)
 
    # at "long?" Instant keypress, move Image to Deleted
    self.button_instant.when_held = self._delete_photo
 
    # at Delayede keypress or after 15sec, restart active
    self.button_delayed.when_pressed = self.active

    # go to active after review time
    self.review_timer.start()
    
  
  def maintenance(self):
    logger.debug("maintenance")
    self._dtb() # disable Timer and Buttons

    # Turn off lights
    self._switch_lights(False)

    # FBI slideshow "maintenance" folder
    self._fbi(folder="fbi/maintenance",random=1)
    
    # On DUAL keypress, output error information
    while 1:
      if button_instant.is_pressed and button_delayed.is_pressed:
        # TODO output error messages
        break
      sleep(0.5)
    
    sleep(3) # to avoid instant triggering
 
    # get active on keypress
    self.button_instant.when_pressed = self.active
    self.button_delayed.when_pressed = self.active


##TODO have a look at fblabel => https://www.gsp.com/cgi-bin/man.cgi?section=1&topic=fblabel
      
PhotoBox()
while (True):
    sleep(2)
