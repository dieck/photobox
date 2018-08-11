from gpiozero import Button, DigitalOutputDevice
from time import sleep
from threading import Timer

class PhotoBox:
  """My PhotoBox"""
  
  # Configuration
  
  # GPIO ports
  gpio_port_button_instant = 1
  gpio_port_button_delayed = 2
  gpio_port_switch_light_A = 3
  gpio_port_switch_light_B = 4

  # Image storage 
  storage = "/tmp"
  # backup = "/mnt" # optional backup storage

  # Time settings
  standby = 5 # minutes
  review = 15 # seconds


  # constants
  STANDBY=0
  ACTIVE=1
  REVIEW=2
  MAINTENANCE=4

  
  # class variables
  state = None
  button_instant = None
  button_delayed = None
  switch_light_A = None
  switch_light_B = None
  
  last_picture = None

  standby_timer = None

  
  def __init__(self):
    self.button_instant = Button(gpio_port_button_instant, hold_time=3)
    self.button_delayed = Button(gpio_port_button_delayed)
    self.switch_light_A = DigitalOutputDevice(gpio_port_switch_light_A, active_high=False)
    self.switch_light_B = DigitalOutputDevice(gpio_port_switch_light_B, active_high=False)

    # Prepare Standby Timer
    standby_timer = Timer(standby * 60.0, self.standby)

    # go into Standby after init    
    self.state=PhotoBox.STANDBY
    self.standby()


  def _dtb(self):
    # Disable Timers and Buttons
    self.standby_timer.cancel()
    self.button_instant.when_held = None
    self.button_instant.when_pressed = None
    self.button_delayed.when_pressed = None


  def _switch_lights(self, to = False):
    if to is None: # toggle 
      self.switch_light_A.value = not self.switch_light_A.value
      self.switch_light_B.value = not self.switch_light_B.value
    elif to == True: # turn on
      self.switch_light_A.on()
      self.switch_light_B.on()
    else: # secure state = off
      self.switch_light_A.off()
      self.switch_light_B.off()


  def _fbi(self, file = "active.png", folder = None, delay=15):
    # remove all old images
    os.system("killall fbi");
    
    # show new image
    fbi = "/usr/bin/fbi --noverbose -a -T 1"
    
    if folder is None:
      fbi += " " + file
    else:
      fbi += " -t %d -u \"%s/*\"" % (delay, folder)

    # TODO error handling   
    os.system(fbi)


  def _take_photo(self, delay = None):
    self._dtb() # disable Timer and Buttons
    
    if not delay is None:
      self._fbi(folder="delay",delay=1)
      sleep(delay) # TODO: time delayed display, so that it will take a photo at 0
    
    self.last_picture = "current.png" # TODO create photo name and make sure it doesn't already exist
    
    # TODO parameters, and error handling (e.g. look for camera first...)
    os.system("gphoto2 -some-params %s" % self.last_picture)
    
    # TODO file handling - move to self.storage, create a copy in self.backup maybe


  def _take_photo_delayed(self):
    return _take_photo(5)

  
  def _delete_photo(self):
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
    self._dtb() # disable Timer and Buttons
    self.state=PhotoBox.STANDBY

    # Turn off Lights
    self._switch_lights(False)
    
    # FBI slideshow "standby" folder
    self._fbi(folder="standby")
    
    # Wait for any key press to become active
    self.button_instant.when_pressed = self.active
    self.button_delayed.when_pressed = self.active
  
  def active(self):
    self._dtb() # disable Timer and Buttons
    self.state=PhotoBox.ACTIVE
    
    # Turn on Lights
    self._switch_lights(True)
    
    # FBI main screen
    self._fbi(file="active.png")
    
    # Wait for key press to init countdown / directly snap
    self.button_instant.when_pressed = self._take_photo
    self.button_delayed.when_pressed = self._take_photo_delayed
    
    # after snapshot, go to review
    self.review()
    
    # after self.standby minutes without state change, go to standby
    self.standby_timer.start()
    

  def review(self):
    self._dtb() # disable Timer and Buttons
    self.state=PhotoBox.REVIEW
    # Keep lights are they were
    # Show picture
    self._fbi(file=self.last_picture)
 
    # at "long?" Instant keypress, move Image to Deleted
    self.button_instant.when_held = self._delete_photo
 
    # at Delayede keypress or after 15sec, restart active
    self.button_delayed.when_pressed = self.active

    
  
  def maintenance(self):
    self._dtb() # disable Timer and Buttons
    self.state=PhotoBox.MAINTENANCE

    # Turn off lights
    self._switch_lights(False)

    # FBI slideshow "maintenance" folder
    self._fbi(folder="standby")
    
    # On DUAL keypress, output error information
    while 1:
      if button_instant.is_pressed && button_delayed.is_pressed:
        # TODO output error messages
        break
      sleep(0.5)
    
    sleep(3) # to avoid instant triggering
 
    # get active on keypress
    self.button_instant.when_pressed = self.active
    self.button_delayed.when_pressed = self.active


##TODO have a look at fblabel => https://www.gsp.com/cgi-bin/man.cgi?section=1&topic=fblabel
      
