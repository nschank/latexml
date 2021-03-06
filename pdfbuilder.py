from color import print_error, print_warning
from config import get_resource_root
from os import chdir, devnull, getcwd, getpid, mkdir, rename, remove
from os.path import basename, exists, join
from random import randint
from re import sub
from shutil import copy, move, rmtree
from stringutil import strip_latex_comments
from subprocess import CalledProcessError, check_call, check_output
import errno
import string

def prepare_resources(resource_list):
  for resource in set(resource_list):
    try:
      copy(join(get_resource_root(), resource), getcwd())
    except IOError as e:
      if e.errno == errno.ENOENT:
        print_error("Could not find resource {}".format(resource))
      elif e.errno == errno.EEXIST:
        print_error("Duplicate resource filename at {}".format(resource))
      elif e.errno == errno.EACCES:
        print_error("Resource at {} could not be accessed".format(resource))
      else:
        raise
      return False
  return True

def build(document_contents, resources, filename, keep=False):
  document_contents = strip_latex_comments(document_contents)
  assert document_contents
  root = getcwd()
  dir = ".22tmp.r" + str(getpid()) + str(randint(0,1000))
  try: 
    mkdir(dir)
  except OSError as e:
    if e.errno == errno.EEXIST:
      print_error("Temporary directory could not be created, please try again")
      return
    raise
  chdir(dir)
  if prepare_resources(resources):
    # Copied all resources successfully
    with open("render.tex", "w") as f:
      f.write(document_contents.encode('UTF-8'))
    try:
      with open(devnull, 'wb') as DEVNULL:
        check_output(["pdflatex", "-halt-on-error", "render.tex"],
            stderr=DEVNULL)
    except CalledProcessError as e:
      print_error("The rendering failed due to a LaTeX error:")
      lines = map(string.rstrip, e.output.split('\n'))
      if len(lines) > 7:
        for line in lines[-8:-2]:
          print "\t", line
      else:
        for line in lines:
          print "\t", line
      print_warning("Rendered .tex file kept as {}.tex".format(filename))
      safe_overwrite("render", root, filename, ".tex")
    except OSError as e:
      if e.errno == errno.ENOENT:
        print_error("Could not run pdflatex, is it installed?")
      else: raise
    else:
      while exists(root + "/" + filename + ".pdf"):
        print_warning("'{}' already exists.".format(filename + ".pdf"))
        response = raw_input("Type a new name or a blank line to replace file: ")
        if not response: break
        elif response.endswith(".pdf"):
          filename = response[:-4]
          assert filename
        else:
          filename = response
      safe_overwrite("render", root, filename, ".pdf")
      if keep:
        safe_overwrite("render", root, filename, ".tex")
  chdir(root)
  try: rmtree(dir)
  except OSError:
    print_warning("Could not delete temporary directory")

def can_build(document_contents, resources):
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
  result = False
  if prepare_resources(resources):
    with open("render.tex", "w") as f:
      f.write(document_contents.encode('UTF-8'))
    try:
      with open(devnull, 'wb') as DEVNULL:
        check_call(["pdflatex", "-halt-on-error", "render.tex"],
            stdout=DEVNULL, stderr=DEVNULL)
      result = True
    except CalledProcessError:
      result = False
    except OSError as e:
      result = False
      if e.errno == errno.ENOENT:
        print_error("Could not run pdflatex, is it installed?")
      else: raise
  chdir(root)
  try: rmtree(dir)
  except OSError:
    print_warning("Could not delete temporary directory")
  return result   
  
def safe_overwrite(oldname, dir, newname, extension):
  newname = basename(newname)
  try: remove(join(dir, newname + extension))
  except OSError as e:
    if e.errno != errno.ENOENT: raise  
  rename(oldname + extension, newname + extension)
  move(newname + extension, dir)

def temp_file_remove(tempfilename):
  try: 
    remove(tempfilename)
  except OSError as e:
    if e.errno != errno.ENOENT:
      print_warning("Could not remove temporary file '{}'".format(tempfilename))
  except Exception: 
    print_warning("Could not remove temporary file '{}'".format(tempfilename))