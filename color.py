CLEAR_COLOR = "\033[0;0m"
BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7

def color_code(color, foreground=True, bold=False):
  ret = "\033["
  if foreground:
    ret = ret + "3" + str(color)
  elif bold:
    ret = ret + "10" + str(color)
  else:
    ret = ret + "4" + str(color)
  if bold and foreground:
    ret = ret + ";1"
  elif foreground:
    ret = ret + ";22"
  return ret + "m"
  
def color(text, code):
  return code + text + CLEAR_COLOR
  
def print_error(message):
  print color("Error: ", color_code(RED, bold=True)) + message
  
def print_warning(message):
  print color("Warning: ", color_code(YELLOW, bold=True)) + message
  