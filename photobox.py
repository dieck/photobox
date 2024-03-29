from gpiozero import Button, DigitalOutputDevice
from time import sleep
from threading import Timer
from shutil import copyfile
from os.path import expanduser
from os import remove
import configparser
import os.path
import subprocess
import re
import uuid

# create logging capabilities
import logging
logFormatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler(expanduser("~") + "/photobox.log")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


# TODO: Jumping around in modes will most certainly consume head memory
# as they might think of returning - but actually never will, just forward to other states

# Need to find a way to make this a kind of stateless machine without memory leaks
# For now, assuming it will take more than an evening to fill up RAM on my Pi3 :)

class PhotoBox:
  """My PhotoBox"""
  
  # Configuration
  config = None

  FBI = "/usr/bin/sudo /usr/bin/fbi"
  FBI_KILL = "/usr/bin/sudo /usr/bin/killall fbi"
  GPHOTO = "/usr/bin/gphoto2"
  OMX = "/usr/bin/omxplayer"

  # class variables
  button_instant = None
  button_delayed = None
  switch_light_A = None
  switch_light_B = None

  last_picture = None

  standby_timer = None
  review_timer = None
  error_timer = None
  
  
  def __init__(self):
    logger.info("Initializing PhotoBox")
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

    gpio = int(self.config['GPIO']['button_shutdown'])
    self.button_shutdown = Button(gpio)
    self.button_shutdown.when_pressed = self.shutdownRaspi
	
    gpio = int(self.config['GPIO']['switch_light_A'])
    self.switch_light_A = DigitalOutputDevice(gpio, active_high=False)
    
    gpio = int(self.config['GPIO']['switch_light_B'])
    self.switch_light_B = DigitalOutputDevice(gpio, active_high=False)

    # Prepare Standby Timer
    t = int(self.config['TIMES']['standby'])
    self.standby_timer = Timer(t * 60.0, self.standby)

    t = int(self.config['TIMES']['review'])
    self.review_timer = Timer(t * 1.0, self.active)

    t = 5 # also change _dtb ## fixed: 5sec error screen
    self.error_timer = Timer(t * 1.0, self.active)
    

    # set camera settings
    os.system("%s --set-config-value capturetarget=1" % self.GPHOTO)

    # setting config value does not seem to stick with all cameras. So just modifying gphoto2 settings here. Need to exist...
    # Yes, sorry, this does expect Linux, for now. Well, as do file/dir separators later on :)
    os.system('/bin/grep "ptp2=capturetarget=card" ~/.gphoto/settings || /bin/echo "ptp2=capturetarget=card" >>~/.gphoto/settings')    

    # go into Active after init    
    self.active()

  def shutdownRaspi(self):
    self._switch_lights(to = True)
    sleep(2)
    self._switch_lights(to = False)
    sleep(2)
    self._switch_lights(to = True)
    sleep(2)
    self._switch_lights(to = False)
    sleep(2)
    self._switch_lights(to = True)
    sleep(2)
    self._switch_lights(to = False)
    sleep(2)
    os.system("sudo shutdown -r now")


  def _remove_state(self, state):
    f = self.config['PATHS']['state'] + "/" + state
    if os.path.isfile(f):
      os.remove(f)

  def _set_state(self, state):
    if not self.config['PATHS']['state']:
      return
    # remove all possible files - do not care about old state
    self._remove_state("active")
    self._remove_state("standby")
    self._remove_state("error")
    self._remove_state("maintenance")
  
    f = open(self.config['PATHS']['state'] + "/" + state,"w+")
    f.write(state)
    f.close()

  ## disable timers and buttons
  def _dtb(self):
    dtbdebug = False
    
    dtbdebug and logger.debug("_dtb: Disabling all Timers and Button activities")
    # Disable Timers and Buttons

    dtbdebug and logger.debug("_dtb: cancel standby")
    self.standby_timer.cancel()
    t = int(self.config['TIMES']['standby'])
    self.standby_timer = Timer(t * 60.0, self.standby)

    dtbdebug and logger.debug("_dtb: cancel review")
    self.review_timer.cancel()
    t = int(self.config['TIMES']['review'])
    self.review_timer = Timer(t * 1.0, self.active)

    dtbdebug and logger.debug("_dtb: cancel error")
    self.error_timer.cancel()
    t = 5 # also change __init__ ## fixed: 5sec error screen 
    self.error_timer = Timer(t * 1.0, self.active)
    
    dtbdebug and logger.debug("_dtb: unset instant when_held")
    self.button_instant.when_held = None

    dtbdebug and logger.debug("_dtb: unset instant when_pressed")
    self.button_instant.when_pressed = None

    dtbdebug and logger.debug("_dtb: unset delayed when_pressed")
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
    os.system(self.FBI_KILL);
    
    # show new image
    fbi = self.FBI + " --noverbose -a -T 1"
    
    if random:
      fbi += " -u "
	  
    if folder is None:
      fbi += " %s " % file
    else:
      fbi += " -t %d -u %s/*" % (delay, folder)

    os.system(fbi)


  def _get_battery_level(self):
    logger.debug("_get_battery_level")
    
    call = "LANG=en %s --get-config /main/status/batterylevel" % self.GPHOTO
    out = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True).communicate()[0]

    # analyze lines returned
    power = 0
    cameraerror = False
    
    if out:
      # analyze lines returned

      for o in out.splitlines():
        logger.debug("LINE: %s" % o)

        # look for battery current state
        mtch = re.search('Current: (\d+)%',o)
        if mtch:
          power = int(mtch.group(1))
          logger.info("---- Found Battery level %i" % power)
          
        # look for error state
        mtch = re.search('Error: No camera found',o)
        if mtch:
          cameraerror = True
          logger.critical("---- Found No Camera found error")


    # camera error - unrecoverable: Go to maintenance
    if cameraerror:
      self.maintenance()
      return

    # battery power low? show notice for 5 seconds
    if power <= 15:
      self._fbi(file="fbi/battery.png")
      sleep(3)
      return
    
    # and do whatever was planned to do next :)
    return power

 
  def _take_photo(self, delay = None, rnd=0):
    logger.debug("_take_photo")
    self._dtb() # disable Timer and Buttons
    
    # tried to take a photo 3 times - something is wrong, going to error mode
    if (rnd == 3):
      logger.warn("Encountered multiple errors, stopping at 3 retries")
      self.error(file="fbi/error-retry.png")
      return

    # delayed picture: show countdown video
    if delay is None:
      # No countdown, just turn on lights
      if self.config['LIGHTS']['flash_lights']:
        self._switch_lights(True)
        # and give it a second to be sure it's on
        sleep(1)
    elif delay == 3:
      if self.config['LIGHTS']['flash_lights']:
        self._switch_lights(True)
      subprocess.Popen([self.OMX,"countdown/countdown3.mp4"])
      sleep(3)
    else:  
      subprocess.Popen([self.OMX,"countdown/countdown.mp4"])
      sleep(5) # time delayed display, so that it will take a photo at 0
      if self.config['LIGHTS']['flash_lights']:
        self._switch_lights(True)
      sleep(4)
 
    
    self.last_picture = self.config['PATHS']['storage'] + "/current.png"
    
    call = "LANG=en %s --filename %s --force-overwrite --keep-raw --capture-image-and-download --get-config /main/status/batterylevel" % (self.GPHOTO, self.last_picture)
    logger.debug("starting: " + call)

    prc = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True);
    
    self._fbi(file="fbi/transfer.png")
    
    # blocking, await gphoto2 finish    
    out = prc.communicate()[0]
    
    if self.config['LIGHTS']['flash_lights']:
      self._switch_lights(False)

    # analyze lines returned
    power = 0
    filename = ""
    focuserror = False
    cameraerror = None
    
    if out:
      # analyze lines returned

      for o in out.splitlines():
        logger.debug("LINE: %s" % o)

        # look for filename        
        mtch = re.search('Deleting file .*/(DSC.*\.JPG) on the camera',o)
        if mtch:
          filename = mtch.group(1)
          logger.debug("---- Found filename %s" % filename)

       # look if camera is set to RAW
        mtch = re.search('Keeping file .*/(DSC.*\.NEF) on the camera',o)
        if mtch:
          logger.error("---- Camera uses RAW/NEF")
          cameraerror = "fbi/error-raw.png"

        # look for battery level
        mtch = re.search('Current: (\d+)%',o)
        if mtch:
          power = int(mtch.group(1))
          logger.debug("---- Found Battery level %i" % power)

        # look for error state
        # no camera
        mtch = re.search('Error: No camera found',o)
        if mtch:
          cameraerror = "fbi/error-nocam.png"
          logger.error("---- Found No Camera error")

        # sd card problems (most likely full)
        mtch = re.search('PTP Store Not Available',o)
        if mtch:
          cameraerror = "fbi/storage-ptp.png"
          logger.error("---- Found PTP (SD Card) error")

        # camera does not store to SD
        mtch = re.search('New file is in location /capt0000.jpg on the camera',o)
        if mtch:
          cameraerror = "fbi/storage-sd.png"
          logger.error("---- Found file location error, not storing to SD card")
        
        # local pi storage full
        mtch = re.search('write: No space left on device',o)
        if mtch:
          cameraerror = "fbi/storage-pi.png"
          logger.error("---- Found Storage (main or backup) error")

        mtch = re.search('Out of Focus',o)
        if mtch:
          focuserror = True
          logger.debug("---- Found Focus error")

    # camera error - unrecoverable: Go to maintenance
    if cameraerror:
      self._fbi(file=cameraerror)
      sleep(30)
      self.maintenance()
      return

    # focus error - try again, up to 3 times
    if focuserror:
      self._take_photo(rnd = rnd+1)
      return
      
    # battery power low? show notice for 5 seconds
    if power <= 15:
      logger.warn("Low battery level: %i %" % power)
      self._fbi(file="fbi/battery.png")
      sleep(3)
      return
    
    
    if filename:
    
      # review pic
      # note: will not activate buttons
      self.review(activateButtons = False)

      splfile = filename.split('.')
      splfile.insert(len(splfile)-1, str(uuid.uuid4()))
      filenameuuid = '.'.join(splfile)

      # copy to storage dir
      new_target = self.config['PATHS']['storage'] + "/" + filenameuuid
      try:
        copyfile(self.last_picture, new_target)
      except (OSError, IOError) as e:
        # if an error occurs, assume storage problem and move to maintenance
        logger.critical(e)
        self._fbi(file="fbi/storage-file.png")
        sleep(30)
        self.maintenance()
        return
        
      # copy to backup dir, if exists
      if self.config['PATHS']['backup']:
        new_target = self.config['PATHS']['backup'] + "/" + filenameuuid   
        try:
          copyfile(self.last_picture, new_target)
        except (OSError, IOError) as e:
          # if an error occurs, assume storage problem and move to maintenance
          logger.critical(e)
          self._fbi(file="fbi/storage-backup.png")
          sleep(30)
          self.maintenance()
          return
        
      # copy to web last dir, if exists
      if self.config['PATHS']['lastweb']:
        new_target = self.config['PATHS']['lastweb'] + "/" + filenameuuid   
        try:
          copyfile(self.last_picture, new_target)
          # Create HTML file
          lw = open(self.config['PATHS']['lastweb'] + "/index.html","w+")
          lw.write('<html><body><img width="640" src="%s" /></body></html>' % filenameuuid)
          lw.close()
          
        except (OSError, IOError) as e:
          # if an error occurs, ignore.
          logger.critical(e)
          logger.critical("ignored for web")
          return
        
      # activate buttons in review mode
      self.review(buttonsOnly = True)
      return
   
    else:
      # no filename found - most likely not downloaded from camera?
      logger.error("no filename found in camera output")
      self.error(file="fbi/error-file.png")
      return

  def _take_photo_delayed(self):
    logger.debug("_take_photo_delayed")
    return self._take_photo(delay=1)

  def _take_photo_delayedshort(self):
    logger.debug("_take_photo_delayedshort")
    return self._take_photo(delay=3)

  
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
    self._set_state("standby")

    # Turn off Lights
    if not self.config['LIGHTS']['flash_lights']:
      self._switch_lights(False)
    
    # FBI slideshow "standby" folder
    self._fbi(folder="fbi/standby",random=1)
    
    # Wait for any key press to become active
    self.button_instant.when_pressed = self.active
    self.button_delayed.when_pressed = self.active
  
  def active(self):
    logger.debug("active")
    self._dtb() # disable Timer and Buttons
    self._set_state("active")
    
    # looks for battery level, will display warning, and go to maintenance if camera not found
    self._get_battery_level()
    
    # Turn on Lights
    if not self.config['LIGHTS']['flash_lights']:
      self._switch_lights(True)
    
    # FBI main screen
    self._fbi(file="fbi/active.png")
    
    # Wait for key press to init countdown / directly snap
    self.button_instant.when_pressed = self._take_photo_delayedshort
    self.button_delayed.when_pressed = self._take_photo_delayed
    
    # after self.standby minutes without state change, go to standby
    self.standby_timer.start()
    

  def review(self, activateButtons=True, buttonsOnly=False):
    logger.debug("review")
    
    if buttonsOnly == False:
      self._dtb() # disable Timer and Buttons

      # Keep lights are they were
      # Show picture
      self._fbi(file=self.last_picture)
 
    if buttonsOnly == True or activateButtons == True: 
      # at "long?" Instant keypress, move Image to Deleted
      self.button_instant.when_held = self._delete_photo
 
      # at Delayede keypress or after 15sec, restart active
      self.button_delayed.when_pressed = self.active
      self.button_instant.when_pressed = self.active

    if buttonsOnly == False:
      # go to active after review time
      self.review_timer.start()


  def error(self):
    logger.debug("error")
    self._dtb() # disable Timer and Buttons
    self._set_state("error")

    # Keep lights are they were

    # FBI error screen
    self._fbi(file="fbi/error.png")
 
    # at Delay keypress or after 15sec, restart active
    self.button_delayed.when_pressed = self.active
    self.button_instant.when_pressed = self.active

    # go to active after review time
    self.error_timer.start()
    
  
  def maintenance(self):
    logger.debug("maintenance")
    self._dtb() # disable Timer and Buttons
    self._set_state("maintenance")

    # Turn off lights
    if not self.config['LIGHTS']['flash_lights']:
      self._switch_lights(False)

    # FBI slideshow "maintenance" folder
    self._fbi(folder="fbi/maintenance",random=1)
    
    # On DUAL keypress, output error information
    while 1:
      if self.button_instant.is_pressed and self.button_delayed.is_pressed:
        # TODO output error messages
        break
      sleep(0.5)

    # output log to console 1
    os.system(self.FBI_KILL);
    os.system("/usr/bin/sudo /bin/cat ~pi/photobox.log >/dev/tty1")
    
    sleep(5) # to avoid instant triggering
 
    # get active on keypress
    self.button_instant.when_pressed = self.active
    self.button_delayed.when_pressed = self.active


##TODO have a look at fblabel => https://www.gsp.com/cgi-bin/man.cgi?section=1&topic=fblabel
      
PhotoBox()
while (True):
    sleep(2)
