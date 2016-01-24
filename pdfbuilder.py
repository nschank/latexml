from color import print_warning
from os import chdir, devnull, getcwd, getpid, mkdir, remove
from os.path import exists
from random import randint
from shutil import rmtree
from subprocess import CalledProcessError, check_call
import errno

def can_build(document_contents):
  assert document_contents
  root = getcwd()
  dir = ".22tmp.v" + str(getpid()) + str(randint(0,1000))
  try: 
    mkdir(dir)
  except OSError as e:
    if e.errno == errno.EEXIST:
      print_error("Temporary directory could not be created, please try again")
      return False
    raise
  chdir(dir)
  with open("render.tex", "w") as f:
    f.write(document_contents.encode('UTF-8'))
  try:
    with open(devnull, 'wb') as DEVNULL:
      check_call(["pdflatex", "render.tex", "-halt-on-error"],
          stdout=DEVNULL, stderr=DEVNULL)
    result = True
  except CalledProcessError:
    result = False
  except OSError as e:
    failed = True
    if e.errno == errno.ENOENT:
      print_error("Could not run pdflatex, is it installed?")
    else: raise
  chdir(root)
  try: rmtree(dir)
  except OSError:
    print_warning("Could not delete temporary directory")
  return result   
  

def temp_file_remove(tempfilename):
  try: 
    remove(tempfilename)
  except OSError as e:
    if e.errno != errno.ENOENT:
      print_warning("Could not remove temporary file '{}'".format(tempfilename))
  except Exception: 
    print_warning("Could not remove temporary file '{}'".format(tempfilename))