import argparse
import errno
import os
import re
import stat
import string
import xml.etree.ElementTree as ET
from problem import Problem, Version, UsedIn, Document
from parseable import ImproperXmlException
from config import get_default_author, get_problem_root, get_resource_root, get_topics, get_types
from copy import deepcopy
from datetime import date
from color import *
from subprocess import call
from random import randint
from pdfbuilder import can_build
from grp import getgrgid
from sys import platform

stylistic_errors = {
  re.compile(r"HINT|Hint: |\\text(?:bf|it){\s*[Hh]int:?\s*}:?"):r"Use the \hint command instead.",
  re.compile(r"Note: |\\text(?:bf|it){\s*[Nn]ote:?\s*}:?"):r"Use the \note command instead.",
  re.compile(r"\\(?:small|med|big)skip"):r"Use two newlines to separate paragraphs.",
  re.compile(r"\$\$"):r"Use \[x\] instead of $$x$$ to produce an equation.",
  re.compile(r"\\(?:bmod|pod|mod)(?![A-Za-z])"):r"Always use \pmod.",
  re.compile(r"\\mathbb(?: N|\{N\})"):r"Use \N instead.",
  re.compile(r"\\mathbb(?: Z|\{Z\})"):r"Use \Z instead.",
  re.compile(r"\\mathbb(?: R|\{R\})"):r"Use \R instead.",
  re.compile(r"\\mathbb(?: Q|\{Q\})"):r"Use \Q instead.",
  re.compile(r"\\mathcal(?: P|\{P\})"):r"Use \Pow instead.",
  re.compile(r"\\newcommand(?![A-Za-z])"):r"Use a <param> tag instead.",
  re.compile(r"\\(?:usepackage|require)(?![A-Za-z])"):r"Use a <dependency> tag instead.",
  re.compile(r"\S(?:\r?\n)?[\t ]*\\(hint|note)"):r"The \hint and \note commands should be placed in their own paragraph. Add two newlines (NOT '\\') before them."
}

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
  print "Type '" + color_code(MAGENTA) + "list" + CLEAR_COLOR +"' to see the list of valid selections/indices."
  print "Type '" + color_code(MAGENTA) + "clear" + CLEAR_COLOR +"' to clear selection."
  print "Enter an empty line when done.\n"
        
  done = False
  while not done:
    print color_code(BLACK, bold=True), "\nCurrent selection" + CLEAR_COLOR + ":", (current if current else "None")
    tentative = raw_input(color_code(YELLOW) + "Selection or Command" + CLEAR_COLOR + ": ")
    matches = [el for el in space if el.startswith(tentative)]
    try: index = int(tentative)
    except ValueError: index = None
    if tentative == 'list':
      for i,el in enumerate(space):
        print "\t", color_code(BLUE, bold=True), i, CLEAR_COLOR, el
      print "\n"
    elif tentative == 'clear':
      current = []
    elif tentative == '':
      if current:
        print color_code(GREEN), "\nFinal selection" + CLEAR_COLOR + ":", current, "\n\n"
        done = True
      else:
        print_error("Must select at least one")
    elif len(matches) > 1:
      print_error("Multiple matches found for `{}' ({})".format(tentative, matches))
    elif len(matches):
      if matches[0] in current:
        print_warning("{} was already selected".format(matches[0]))
      else:
        current.append(matches[0])
    elif index is not None:
      if index < 0 or index >= len(space):
        print_error("Invalid index {}".format(index))
      elif space[index] in current:
        print_warning("{} was already selected".format(space[index]))
      else:
        current.append(space[index])
    else:
      print_error("Unknown token: {}".format(tentative))
          
  return current
  
def branch(settings):
  """
  Adds a new Version to the problem
  """
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print_error("Could not parse '{}'".format(settings.filename))
    print "Are you sure it exists?"
    exit(1)
    
  try:
    problem = Problem(settings.filename)
    problem.parse_tree(tree)
    next_id = problem.next_id()
  except ImproperXmlException:
    print_error("{} has invalid problem XML.".format(settings.filename))
    print "Try running `validate' to help find possible causes."
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
    print color_code(CYAN), "SELECT TOPICS\n-------------", CLEAR_COLOR
    version.topics = interactive_select(get_topics(), version.topics)
    print color_code(CYAN), "SELECT TYPES\n-------------", CLEAR_COLOR
    version.types = interactive_select(get_types(), version.types)
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
    document.validate()
  except ImproperXmlException, ET.ParseError:
    print_error("Could not parse '{}'".format(settings.document))
    print "Are you sure it exists?"
    exit(1)
    
  for version in document.versions:
    prob_tree = ET.parse(version.filename)
    problem = Problem(version.filename)
    problem.parse_tree(prob_tree, validate_versions=False)
    already_finalized = False
    for usedin in problem.used_in:
      if document.year == usedin.year and document.name == usedin.assignment_name:
        already_finalized = True
    if already_finalized:
      break
    
    problem.used_in.append(UsedIn(document.year, document.name, document.private))
    
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
        print color_code(CYAN), "SELECT TYPES\n-------------", CLEAR_COLOR
        version.topics = interactive_select(get_topics(), [])
        print color_code(CYAN), "SELECT TYPES\n-------------", CLEAR_COLOR
        version.types = interactive_select(get_types(), [])
      
      root = problem.to_element()
      indent(root)
      f.write(ET.tostring(root))
  except OSError:
    print_error("File '{}' already exists.".format(settings.filename))
    exit(1)
  try:
    print "New file created.\nSetting permissions..."
    os.chmod(settings.filename, stat.S_IRWXU | stat.S_IRWXG)
  except OSError:
    print_error("Permissions not successfully fixed, please run chmod 660")
    
def edit(settings):
  """
  Edits the newest version's topics and types
  """
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print_error("Could not parse '{}'".format(settings.filename))
    print "Are you sure it exists?"
    exit(1)
    
  try:
    problem = Problem(settings.filename)
    problem.parse_tree(tree, validate_versions=False)
    version = problem.newest_version()
  except ImproperXmlException:
    print_error("{} has invalid problem XML.".format(settings.filename))
    print "Try running `validate' to help find possible causes."
    exit(1)
    
  if settings.remove_todo:
    if "todo" in version.topics:
      version.topics.remove("todo")
    if "todo" in version.types:
      version.types.remove("todo")
    
  print color_code(CYAN), "SELECT TYPES\n-------------", CLEAR_COLOR
  version.topics = interactive_select(get_topics(), version.topics)
  print color_code(CYAN), "SELECT TYPES\n-------------", CLEAR_COLOR
  version.types = interactive_select(get_types(), version.types)
    
  root = problem.to_element()
  indent(root)
  with open(settings.filename, "w") as f:
    f.write(ET.tostring(root))
    
class ValidationResult:
  def __init__(self, failed):
    self.failed = failed
    self.completeness = True
    self.solutions = 2
    self.rubric = 2
    self.code_quality = 3
    self.render = 3
    
def validate_version(version, failed):
  result = ValidationResult(failed)
  
  if "unknown" in map(str.lower, version.authors):
    print_warning("Unknown author\n")
  if "unknown" == version.year.lower():
    print_warning("Unknown year\n") 
    
  for search_term, msg in stylistic_errors.iteritems():
    for search_space in [version.body, version.solution, version.rubric]:
      results = re.search(search_term, search_space)
      if results:
        print_error("Found problematic text \"{}\"".format(results.group(0)))
        print color("\t" + msg, 
            color_code(YELLOW, foreground=False) + color_code(BLACK))
        result.failed = True
        result.code_quality = result.code_quality - 1
        
  for search_space in [version.body, version.solution, version.rubric]:
    if r"\\" in search_space:
      align = r"\begin{align" in search_space
      tabular = r"\begin{tab" in search_space
      if align or tabular:
        print_warning("Found raw newlines \"\\\\\". Make sure newlines are never used for separating\n\tparagraphs -- only for alignment within align or tabular environments.")
      else:
        print_error("Found raw newlines \"\\\\\" and no environments that use newlines for alignment.\n\tNever use raw newlines instead of using paragraph breaks.")
        result.failed = True
        result.code_quality = result.code_quality - 1
     
  if version.resources and get_resource_root() is None:
    print_error("This problem has resources, but your system is not configured with a resource root.")
    result.failed = True
    result.render = 0
  elif version.resources and not os.path.exists(get_resource_root()):
    print_error("Resource root `{}' does not exist".format(get_resource_root()))
    result.failed = True
    result.render = 0
  elif version.resources:
    for resource in version.resources:
      resource_path = os.path.join(get_resource_root(), resource)
      if not os.path.exists(resource_path):
        print_warning("Resource at `{}' could not be found.".format(resource_path))
        result.failed = True
        result.render = 0
        
  try:
    version.validate()
  except ImproperXmlException as e:
    print_error(e.args[0])
    result.failed = True
    
  
  if result.failed:
    print color("\nValidation failure", color_code(RED))
  else:
    print color("\nValidation success", color_code(GREEN))
    
  if ("todo" in version.topics or "todo" in version.types 
      or "needs_work" in version.types):
    print color("This version needs work", color_code(YELLOW))
    result.completeness = False
  
  test_document = Document("Validation Render")
  test_document.name = "Temp"
  test_document.year = "1900"
  test_document.due = "Never"
  test_document.blurb = ""
  test_document.versions.append(version)
  
  if can_build(test_document.build(False, False, metadata=False),
      version.resources):
    print color("Body LaTeX compiles", color_code(GREEN))
  else:
    print color("Body LaTeX does not compile", color_code(RED))
    result.render = result.render - 1
    
  version.body = version.solution
  built_sol = can_build(test_document.build(False, False, metadata=False),
      version.resources)
  todo_sol = "TODO" in version.solution
  if built_sol and not todo_sol:
    print color("Solution LaTeX compiles", color_code(GREEN))
  elif built_sol and todo_sol:
    print color("Solution LaTeX compiles but need to be finished", 
        color_code(YELLOW))
    result.completeness = False
    result.solutions = 1
  elif not built_sol and not todo_sol:
    print color("Solution LaTeX does not compile", color_code(RED, bold=True))
    result.render = result.render - 1
    result.solutions = 1
  elif not built_sol and todo_sol:
    print color("Solution LaTeX does not compile and needs to be finished",
        color_code(RED))
    result.render = result.render - 1
    result.completeness = False
    result.solutions = 0
  
  version.body = version.rubric
  built_rub = can_build(test_document.build(False, False, metadata=False),
      version.resources)
  todo_rub = "TODO" in version.rubric
  if built_rub and not todo_rub:
    print color("Rubric LaTeX compiles", color_code(GREEN))
  elif built_rub and todo_rub:
    print color("Rubric LaTeX compiles but need to be finished", 
        color_code(YELLOW))
    result.completeness = False
    result.rubrics = 1
  elif not built_rub and not todo_rub:
    print color("Rubric LaTeX does not compile", color_code(RED, bold=True))
    result.render = result.render - 1
    result.rubrics = 1
  elif not built_rub and todo_rub:
    print color("Rubric LaTeX does not compile and needs to be finished",
        color_code(RED))
    result.render = result.render - 1
    result.completeness = False
    result.rubrics = 0
        
  return result
    
def validate(settings):
  """
  Validates the correctness and style of a problem XML document.
  """
  if not settings.filename.endswith(".xml"):
    print_error("{} must have a .xml extension to interoperate with build tool".format(settings.filename))
    exit(1)
  
  failed = False
  
  print color("Validating: ", color_code(BLUE)), settings.filename
  if platform in ["linux", "linux2"]:    
    stat_info = os.stat(settings.filename)
    gid = stat_info.st_gid
    mode = stat_info.st_mode & 0777
    group = getgrgid(gid)[0]
    if group != "cs022ta":
      print_error("Wrong group, you MUST run `chgrp cs022ta {}'".format(settings.filename))
      failed = True
    if mode ^ 0660 != 0000:
      print_error("Wrong permissions, you MUST run `chmod 660 {}'".format(settings.filename))
      failed = True
  
  invalid_lt = re.compile("<(?!/?(problem|usedin|version|authors?|year|topics?|types?|param|deps?|dependency|dependencies|body|solution|rubric|resource))")
  invalid_amp = re.compile(r"&(?!\w{1,10};)")
  invalid_char = re.compile(r"[^\x00-\x7f]")
  
  # Some more manual checking  
  with open(settings.filename) as f:
    for num, line in enumerate(f):
      if len(string.rstrip(line)) > 80:
        print_warning("Line {} longer than 80 characters (has {})".format(num+1, len(string.rstrip(line))))
        failed = True
      problem_lt = re.search(invalid_lt, line)
      if problem_lt:
        print_error("Invalid < character on line {} at character {}".format(num+1, problem_lt.start()))
        print color("\tA literal < can be escaped using \"&lt;\" instead.", 
            color_code(YELLOW, foreground=False) + color_code(BLACK))
        failed = True
      problem_amp = re.search(invalid_amp, line)
      if problem_amp:
        print_error("Invalid raw & character on line {} at character {}".format(num+1, problem_amp.start()))
        print color("\tA literal & can be escaped by using \"&amp;\" instead.", 
            color_code(YELLOW, foreground=False) + color_code(BLACK))
        failed = True
      problem_char = re.search(invalid_char, line)
      if problem_char:
        print_error("Invalid non-ASCII character on line {} at character {}".format(num+1, problem_char.start()))
        failed = True
      
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print_error("XML in {} could not be parsed.".format(settings.filename))
    print color("\nPlease rerun validation once XML is fixed", color_code(CYAN))
    exit(1)
  if tree.getroot().tag == 'assignment':
    print_error("This looks like an assignment xml file. Did you mean 22edit validate_doc?")
    exit(1)
  try:
    problem = Problem(settings.filename)
    problem.parse_tree(tree, False)
  except ImproperXmlException as e:
    print_error(e.args[0])
    print color("\nPlease rerun validation after fixing", color_code(CYAN))
    exit(1)
    
  firstProblem = True
  for version in problem.get_versions():
    if not version.standalone and not firstProblem:
      continue
    firstProblem = False
    
    print color("\n\nVERSION {}:\n".format(version.vid),
              color_code(BLUE))
    validate_version(version, failed)
    
def validate_document(settings):
  """
  Validates the correctness and style of a document XML.
  """
  if not settings.filename.endswith(".xml"):
    print_error("{} must have a .xml extension to interoperate with build tool".format(settings.filename))
    exit(1)
  
  failed = False
  
  print color("Validating: ", color_code(BLUE)), settings.filename
  if platform in ["linux", "linux2"]:    
    stat_info = os.stat(settings.filename)
    gid = stat_info.st_gid
    mode = stat_info.st_mode & 0777
    group = getgrgid(gid)[0]
    if group != "cs022ta":
      print_error("Wrong group, you MUST run `chgrp cs022ta {}'".format(settings.filename))
      failed = True
    if mode ^ 0660 != 0000:
      print_error("Wrong permissions, you MUST run `chmod 660 {}'".format(settings.filename))
      failed = True
  
  invalid_lt = re.compile("<(?!/?(assignment|problem|year|title|name|blurb|due))")
  invalid_amp = re.compile(r"&(?!\w{1,10};)")
  invalid_char = re.compile(r"[^\x00-\x7f]")
  
  # Some more manual checking  
  with open(settings.filename) as f:
    for num, line in enumerate(f):
      if len(string.rstrip(line)) > 80:
        print_warning("Line {} longer than 80 characters (has {})".format(num+1, len(string.rstrip(line))))
        failed = True
      problem_lt = re.search(invalid_lt, line)
      if problem_lt:
        print_error("Invalid < character on line {} at character {}".format(num+1, problem_lt.start()))
        print color("\tMake sure the tags you are using are correct.", 
            color_code(YELLOW, foreground=False) + color_code(BLACK))
        failed = True
      problem_amp = re.search(invalid_amp, line)
      if problem_amp:
        print_error("Invalid raw & character on line {} at character {}".format(num+1, problem_amp.start()))
        print color("\tA literal & can be escaped by using \"&amp;\" instead.", 
            color_code(YELLOW, foreground=False) + color_code(BLACK))
        failed = True
      problem_char = re.search(invalid_char, line)
      if problem_char:
        print_error("Invalid non-ASCII character on line {} at character {}".format(num+1, problem_char.start()))
        failed = True
      
  try:
    tree = ET.parse(settings.filename)
  except Exception:
    print_error("XML in {} could not be parsed at all.".format(settings.filename))
    print color("\tAre you sure all tags are closed?", color_code(YELLOW))
    print color("\nPlease rerun validation once XML is fixed", color_code(CYAN))
    exit(1)
  try:
    document = Document(settings.filename)
    document.parse_tree(tree)
    document.validate()
  except ImproperXmlException as e:
    print_error(e.args[0])
    print color("\nPlease rerun validation after fixing", color_code(CYAN))
    exit(1)
    
  for i, version in enumerate(document.versions):
    print color("\n\nProblem {}: {}\n".format(i+1, version.filename),
              color_code(BLUE))
    validate_version(version, failed)
      
def report_card(settings):
  grading = settings.author
  count = 0
  validates = 0
  complete = 0
  solutions = 0
  rubrics = 0
  code_quality = 0
  rendering = 0
  
  root = get_problem_root()
  if os.path.isdir(root):
    for dirpath, dirnames, filenames in os.walk(root):
      for filename in filenames:
        if filename.endswith(".xml"):
          filename = os.path.join(dirpath, filename)
          try:
            tree = ET.parse(filename)
            problem = Problem(filename)
            problem.parse_tree(tree, validate_versions=False)
            
            everyVersion = problem.get_versions()
            currentVersions = [everyVersion[0]] + [v for v in everyVersion[1:] if v.standalone]
            for version in currentVersions:
              try:
                if grading in version.authors:
                  count = count + 1
                  print color("\n\nProblem {}\n\t{} ver{}".format(count, filename, version.vid),
                            color_code(BLUE))
                  result = validate_version(version, False)
                  if not result.failed:
                    validates = validates + 1
                  if result.completeness:
                    complete = complete + 1
                  solutions = solutions + result.solutions
                  rubrics = rubrics + result.rubrics
                  code_quality = code_quality + result.code_quality
                  rendering = rendering + result.render
              except ImproperXmlException:
                pass 
          except ImproperXmlException:
            pass   
          except ET.ParseError:
            pass
          except IOError as e:
            # Permission errors can be safely skipped
            if e.errno != errno.EACCES: 
              print color("Error (IO): ", color_code(RED)), filename
              raise # TODO
          except Exception:
            raise
            
    if count > 0:
      print color("\n\nREPORT CARD: {}\n--------------------\n".format(grading), 
          color_code(MAGENTA))
      print "\tCode Quality:\t{}/{}".format(code_quality, 3*count)
      print "\tCompleteness:\t{}/{}".format(complete, count)
      print "\tRendering:   \t{}/{}".format(rendering, 3*count)
      print "\tSolutions:   \t{}/{}".format(solutions, 2*count)
      print "\tRubrics:     \t{}/{}".format(rubrics, 2*count)
      print "\tValidation:  \t{}/{}".format(validates, count)
      
      final = code_quality + complete + rendering + solutions + rubrics + validates
      out_of = 12*count
      code = color_code(RED)
      if final > out_of / 2:
        code = color_code(YELLOW)
      elif final == out_of:
        code = color_code(GREEN)
      print color("\tFINAL SCORE:\t{}/{}".format(final, out_of), code)
    else:
      print color("NO PROBLEMS FOUND", color_code(RED))
  else:
    print_error("The directory '{}' does not exist".format(root))
  
   

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
  
def add_grade_parser(parser):
  subparser = parser.add_parser('report_card', 
      help='Renders your report card')
  subparser.add_argument('author', nargs='?', default=get_default_author())
  subparser.set_defaults(func=report_card)
  
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
  
def add_validate_document_parser(parser):
  subparser = parser.add_parser('validate_doc', help='Validates the correctness of an assignment XML file')
  subparser.add_argument('filename', metavar='F', help='The assignment to validate')
  subparser.set_defaults(func=validate_document)
  
def build_args():
  """Parses command-line arguments using argparse and returns an object containing runtime information."""
  parser = argparse.ArgumentParser(description='Validates, edits, or creates a 22 XML file')
  subparsers = parser.add_subparsers(help='sub-command help')
  
  add_branch_parser(subparsers)
  add_edit_parser(subparsers)
  add_finalize_parser(subparsers)
  add_grade_parser(subparsers)
  add_new_parser(subparsers)
  add_validate_parser(subparsers)
  add_validate_document_parser(subparsers)
  
  return parser.parse_args()

def main():
  settings = build_args()
  settings.func(settings)
  
  
if __name__ == '__main__':
  main()