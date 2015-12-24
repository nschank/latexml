import argparse
import os
import xml.etree.ElementTree as ET
from parse import TOPICS, TYPES, Problem, Version, ImproperXmlException
from copy import deepcopy
from datetime import date

def indent(elem, level=0):
  i = "\n" + level*"  "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + "  "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i
      
def interactive_select(space, current):
  print "Type an element name, an element index, or an unambiguous prefix to add to your selection."
  print "Type 'list' to see the list of valid selections/indices."
  print "Type 'clear' to clear selection."
  print "Enter an empty line when done.\n"
        
  done = False
  while not done:
    print "\nCurrent selection: ", (current if current else "None")
    tentative = raw_input("Selection or Command: ")
    matches = [el for el in space if el.startswith(tentative)]
    try: index = int(tentative)
    except ValueError: index = None
    if tentative == 'list':
      for i,el in enumerate(space):
        print "\t", i, el
      print "\n"
    elif tentative == 'clear':
      current = []
    elif tentative == '':
      if current:
        print "\nFinal selection: ", current, "\n\n"
        done = True
      else:
        print "Error: Must select at least one"
    elif len(matches) > 1:
      print "Error: Multiple matches found for `{}' ({})".format(tentative, matches)
    elif len(matches):
      if matches[0] in current:
        print "Warning: {} was already selected".format(matches[0])
      else:
        current.append(matches[0])
    elif index is not None:
      if index < 0 or index >= len(space):
        print "Error: Invalid index {}".format(index)
      elif space[index] in current:
        print "Warning: {} was already selected".format(space[index])
      else:
        current.append(space[index])
    else:
      print "Error: Unknown token: {}".format(tentative)
          
  return " ".join(current)
  
def empty_version(root, id='1'):
  version = ET.SubElement(root, 'version')
  version.set('id', id)
  
  author = ET.SubElement(version, 'author')
  author.text = os.getlogin()
  
  year = ET.SubElement(version, 'year')
  year.text = str(date.today().year)
  
  topics = ET.SubElement(version, 'topics')
  topics.text = " "
  types = ET.SubElement(version, 'types')
  types.text = " "
  
  body = ET.SubElement(version, 'body')
  body.text = "\n\n    "
  
  solution = ET.SubElement(version, 'solution')
  solution.text = "\n      TODO\n    "
  
  rubric = ET.SubElement(version, 'rubric')
  rubric.text = "\n      TODO\n    "
  
  return version, topics, types
  
def branch(settings):
  try:
    tree = ET.parse(settings.filename)
    problem = Problem(settings.filename, tree)
  except ImproperXmlException:
    print "Error: {} has invalid problem XML. Try `validate'".format(settings.filename)
    exit(1)
  except Exception:
    print "Error: Could not parse {}".format(settings.filename)
    exit(1)
  try: next_id = 1 + int(problem.get_newest().id)
  except ValueError: 
    print "Error: Highest version has invalid id {}".format(problem.get_newest().id)
    exit(1)
  root = tree.getroot()
  if settings.action == 0:
    empty_version(root, str(next_id))
  elif settings.action == 1:
    version, topics, types = empty_version(root)
    print "SELECT TOPICS\n-------------"
    topics.text = interactive_select(TOPICS, [])
    print "SELECT TYPES\n-------------"
    types.text = interactive_select(TYPES, [])
  else:
    previous = problem.get_newest()
    
    version = ET.SubElement(root, 'version')
    version.set('id', str(next_id))
    
    author = ET.SubElement(version, 'author')
    author.text = os.getlogin()
    
    year = ET.SubElement(version, 'year')
    year.text = str(date.today().year)
    
    topics = ET.SubElement(version, 'topics')
    topics.text = " ".join(previous.topics)
    types = ET.SubElement(version, 'types')
    types.text = " ".join(previous.types)
    
    for name,value in previous.params.iteritems():
      param = ET.SubElement(version, 'param')
      param.set('name', name)
      param.text = value
    
    if previous.deps:
      deps = ET.SubElement(version, 'deps')
      deps.text = " ".join(previous.deps)
      
    body = ET.SubElement(version, 'body')
    body.text = previous.body
    
    solution = ET.SubElement(version, 'solution')
    solution.text = previous.solution
    
    rubric = ET.SubElement(version, 'rubric')
    rubric.text = previous.rubric
    
  
  indent(root)
  with open(settings.filename, "w") as f:
    f.write(ET.tostring(root))
    
def create_new(settings):
  try:
    fd = os.open(settings.filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(fd, 'w') as f:
      root = ET.Element('problem')
      version, topics, types = empty_version(root)
      
      if settings.interactive:
        print "SELECT TOPICS\n-------------"
        topics.text = interactive_select(TOPICS, [])
        print "SELECT TYPES\n-------------"
        types.text = interactive_select(TYPES, [])
      
      indent(root)
      f.write(ET.tostring(root))
  except OSError:
    print "Error: File '{}' already exists.".format(settings.filename)
    
def validate(settings):
  if not settings.filename.endswith(".xml"):
    print "Error: {} must have a .xml extension to interoperate with build22".format(settings.filename)
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print "Error: XML in {} could not be parsed.".format(settings.filename)
    exit(1)  
  try:
    problem = Problem(settings.filename, tree)
  except ImproperXmlException:
    print "Fix the error above and rerun validation"
    exit(1)
  newest = problem.get_newest()
  if "\\newcommand" in newest.body or "\\newcommand" in newest.solution or "\\newcommand" in newest.rubric:
    print "Should not be using `\\newcommand' within the body, solution, or rubric of a problem XML. Use <param> instead."
    exit(1)
  if "\\usepackage" in newest.body or "\\usepackage" in newest.solution or "\\usepackage" in newest.rubric:
    print "Should not be using `\\usepackage' within the body, solution, or rubric of a problem XML. Use <dependency> instead."
    exit(1)
  print "Looks good to me!"
  sol = "TODO" in newest.solution
  rub = "TODO" in newest.rubric
  if sol or rub:
    print "Make sure to write a " + ("solution" if sol else "") + (" and " if sol and rub else "") + ("rubric" if rub else "") 

def add_branch_parser(parser):
  subparser = parser.add_parser('branch', help='Adds a new version to an XML file')
  subparser.set_defaults(func=branch, action=0)
  how_to_add = subparser.add_mutually_exclusive_group()
  how_to_add.add_argument('-c', dest='action', action='store_const', const=2, help='The tool copies the previous version exactly and adds it as a new version')
  how_to_add.add_argument('-e', dest='action', action='store_const', const=0, help='The tool creates an empty version and adds it')
  how_to_add.add_argument('-i', dest='action', action='store_const', const=1, help='The tool creates an empty version and interactively adds topics and types')

def add_new_parser(parser):
  subparser = parser.add_parser('new', help='Creates a new XML file')
  subparser.set_defaults(func=create_new)
  subparser.add_argument('-i', dest='interactive', action='store_true', default=False, help='Allows for the tool to interactively add all required fields')

def add_validate_parser(parser):
  subparser = parser.add_parser('validate', help='Validates the correctness of a problem XML file')
  subparser.set_defaults(func=validate)
  
def build_args():
  """Parses command-line arguments using argparse and returns an object containing runtime information."""
  parser = argparse.ArgumentParser(description='Validates, edits, or creates a 22 XML file')
  parser.add_argument('filename', metavar='F', help='The XML file to create, edit, or validate')
  subparsers = parser.add_subparsers(help='sub-command help')
  
  add_branch_parser(subparsers)
  add_new_parser(subparsers)
  add_validate_parser(subparsers)
  
  return parser.parse_args()

def main():
  settings = build_args()
  settings.func(settings)
  
  
main()