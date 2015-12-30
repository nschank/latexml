import argparse
import os
import xml.etree.ElementTree as ET
from parse import TOPICS, TYPES, Problem, Version, ImproperXmlException, UsedIn, Document
from copy import deepcopy
from datetime import date

def indent(elem, level=0):
  """
  Edits an XML tree so that it indents nicely when written.
  """
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
  """
  Given a list {space} and an existing selection {current}, interacts with the user and returns
  their updated selection among space. Requires that the selection be non-empty.
  """
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
          
  return current
  
def branch(settings):
  """
  Adds a new Version to the problem
  """
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print "Error: Could not parse {}".format(settings.filename)
    exit(1)
    
  try:
    problem = Problem(settings.filename)
    problem.parse_tree(tree)
    next_id = problem.next_id()
  except ImproperXmlException:
    print "Error: {} has invalid problem XML. Try `validate'".format(settings.filename)
    exit(1)
    
  version = deepcopy(problem.newest_version())
  version.vid = next_id
  problem.versions[version.vid] = version
  
  version.add_defaults()
  
  if settings.action in [0,1]:
    version.body = "\n      TODO\n    "
    version.solution = "\n      TODO\n    "
    version.rubric = "\n      TODO\n    "
    version.deps = []
    version.params = dict()
    
  if settings.action == 0:
    version.topics = []
    version.types = []
  elif settings.action == 1:
    print "SELECT TOPICS\n-------------"
    version.topics = interactive_select(TOPICS, version.topics)
    print "SELECT TYPES\n-------------"
    version.types = interactive_select(TYPES, version.types)
  else:
    assert settings.action == 2
    
  root = problem.to_element()
  indent(root)
  with open(settings.filename, "w") as f:
    f.write(ET.tostring(root))
    
def finalize(settings):
  document = Document(settings.document)
  try:
    tree = ET.parse(settings.document)
    document.parse_tree(tree)
  except ImproperXmlException, ET.ParseError:
    print "Error: Could not parse {}".format(settings.document)
    exit(1)
    
  for version in document.versions:
    prob_tree = ET.parse(version.filename)
    problem = Problem(version.filename)
    problem.parse_tree(prob_tree, validate_versions=False)
    problem.used_in.append(UsedIn(document.year, document.name))
    
    root = problem.to_element()
    indent(root)
    with open(version.filename, "w") as f:
      f.write(ET.tostring(root))
  doc = document.to_element()
  indent(doc)
  with open(settings.document, "w") as f:
    f.write(ET.tostring(doc))
    
def create_new(settings):
  try:
    fd = os.open(settings.filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(fd, 'w') as f:
      problem = Problem(settings.filename)
      version = Version(settings.filename, "1")
        
      problem.versions["1"] = version
    
      version.add_defaults()
      version.body = "\n      TODO\n    "
      version.solution = "\n      TODO\n    "
      version.rubric = "\n      TODO\n    "
      
      if settings.interactive:
        print "SELECT TOPICS\n-------------"
        version.topics = interactive_select(TOPICS, [])
        print "SELECT TYPES\n-------------"
        version.types = interactive_select(TYPES, [])
      
      root = problem.to_element()
      indent(root)
      f.write(ET.tostring(root))
  except OSError:
    print "Error: File '{}' already exists.".format(settings.filename)
    
def edit(settings):
  """
  Edits the newest version's topics and types
  """
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print "Error: Could not parse {}".format(settings.filename)
    exit(1)
    
  try:
    problem = Problem(settings.filename)
    problem.parse_tree(tree, validate_versions=False)
    version = problem.newest_version()
  except ImproperXmlException:
    print "Error: {} has invalid problem XML. Try `validate'".format(settings.filename)
    exit(1)
    
  if settings.remove_todo:
    if "todo" in version.topics:
      version.topics.remove("todo")
    if "todo" in version.types:
      version.types.remove("todo")
    
  print "SELECT TOPICS\n-------------"
  version.topics = interactive_select(TOPICS, version.topics)
  print "SELECT TYPES\n-------------"
  version.types = interactive_select(TYPES, version.types)
    
  root = problem.to_element()
  indent(root)
  with open(settings.filename, "w") as f:
    f.write(ET.tostring(root))
    
def validate(settings):
  """
  Validates the correctness and style of a problem XML document.
  TODO: INCOMPLETE
  """
  if not settings.filename.endswith(".xml"):
    print "Error: {} must have a .xml extension to interoperate with build tool".format(settings.filename)
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print "Error: XML in {} could not be parsed.".format(settings.filename)
    exit(1)
  try:
    problem = Problem(settings.filename)
    problem.parse_tree(tree)
  except ImproperXmlException as e:
    print "{}\nRerun validation".format(e.strerror)
    exit(1)
  newest = problem.newest_version()
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
  subparser.add_argument('filename', metavar='F', help='The XML file to create, edit, or validate')
  subparser.set_defaults(func=branch, action=0)
  how_to_add = subparser.add_mutually_exclusive_group()
  how_to_add.add_argument('-c', dest='action', action='store_const', const=2, help='The tool copies the previous version exactly and adds it as a new version')
  how_to_add.add_argument('-e', dest='action', action='store_const', const=0, help='The tool creates an empty version and adds it')
  how_to_add.add_argument('-i', dest='action', action='store_const', const=1, help='The tool creates an empty version and interactively adds topics and types')

def add_finalize_parser(parser):
  subparser = parser.add_parser('finalize', help='Marks that a document XML has been released, and thus <usedin> tags should be added to appropriate problems')
  subparser.add_argument('document', metavar='D', help='The document file which has been released as an assignment')
  subparser.set_defaults(func=finalize)
  
def add_new_parser(parser):
  subparser = parser.add_parser('new', help='Creates a new XML file')
  subparser.set_defaults(func=create_new)
  subparser.add_argument('filename', metavar='F', help='The XML file to create, edit, or validate')
  subparser.add_argument('-i', dest='interactive', action='store_true', default=False, help='Allows for the tool to interactively add all required fields')

def add_edit_parser(parser):
  subparser = parser.add_parser('edit', help='The interactive editor for topics and types')
  subparser.set_defaults(func=edit)
  subparser.add_argument('filename', metavar='F', help='The XML file to create, edit, or validate')  
  subparser.add_argument('--remove-todo', dest='remove_todo', action='store_true', default=False, help='Removes the todo topic and type automatically, if present')
  
def add_validate_parser(parser):
  subparser = parser.add_parser('validate', help='Validates the correctness of a problem XML file')
  subparser.add_argument('filename', metavar='F', help='The XML file to create, edit, or validate')
  subparser.set_defaults(func=validate)
  
def build_args():
  """Parses command-line arguments using argparse and returns an object containing runtime information."""
  parser = argparse.ArgumentParser(description='Validates, edits, or creates a 22 XML file')
  subparsers = parser.add_subparsers(help='sub-command help')
  
  add_branch_parser(subparsers)
  add_edit_parser(subparsers)
  add_finalize_parser(subparsers)
  add_new_parser(subparsers)
  add_validate_parser(subparsers)
  
  return parser.parse_args()

def main():
  settings = build_args()
  settings.func(settings)
  
  
main()