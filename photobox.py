
class PhotoBox:
  """My PhotoBox"""
  
  # configuration
  gpio_button_instant=1
  gpio_button_delayed=2
  gpio_switch_light=[1,2]

  # constants
  STANDBY=0
  ACTIVE=1
  MAINTENANCE=2
  
  # class variables
  state = null
 
  
  def __init__(self):
    self.state=PhotoBox.STANDBY
    self.standby()
    
  
  def standby(self):
    self.state=PhotoBox.STANDBY
    # Turn off Lights
    # FBI slideshow "standby" folder
    # Wait for any key press to become active
     
  
  def active(self):
    self.state=PhotoBox.ACTIVE
    # Turn on Lights
    # FBI main screen
    # Wait for key press to init countdown / directly snap
    # Show picture
    # at keypress or after 15sec, restart standby
     
  
  def maintenance(self):
    self.state=PhotoBox.MAINTENANCE
    # Turn off lights
    # FBI slideshow "maintenance" folder
    # On DUAL keypress, output error information

