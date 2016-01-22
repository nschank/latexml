import argparse
import os
from parseable import ImproperXmlException
from problem import Problem, Document
from subprocess import call
from random import randint
from config import get_problem_root
import xml.etree.ElementTree as ET

def satisfies(version, settings, used_ins):
  if (settings.allowed_topics and 
      [topic for topic in version.topics 
          if topic not in settings.allowed_topics]):
    return False
  if (settings.required_topics and not
      [topic for topic in version.topics
          if topic in settings.required_topics]):
    return False
  if (settings.required_types and not
      [type for type in version.types
          if type in settings.required_types]):
    return False
  if (settings.written and version.year not in settings.written):
    return False
  if settings.todo or settings.grep:
    lower_sol = version.solution.lower()
    lower_rub = version.rubric.lower()
    if (settings.todo and lower_sol.find("todo") == -1 
        and lower_rub.find("todo") == -1):
      return False
    if settings.grep:
      lower_body = version.body.lower()
      for word in settings.grep:
        word = word.lower()
        if (lower_sol.find(word) == -1 and 
            lower_rub.find(word) == -1 and 
            lower_body.find(word) == -1):
          return False
  if settings.used_in or settings.not_used_in:
    matches_used = False
    for actual in used_ins:
      if settings.used_in and actual.year in settings.used_in:
        matches_used = True
      if settings.not_used_in and actual.year in settings.not_used_in:
        return False
    if not used_ins:
      if settings.used_in and "none" in settings.used_in:
        matches_used = True
      if settings.not_used_in and "none" in settings.not_used_in: 
        return False
    if settings.used_in and not matches_used:
      return False
  if (settings.authors and not
      [author for author in version.authors
          if author in settings.authors]):
    return False
  return True

def build(document, filename, solutions=False, rubrics=False, metadata=False):
  if filename.endswith(".pdf"):
    filename = filename[:-4]
    assert filename
  else:
    print "Warning: Output will be named {}.pdf".format(filename)
  if document.versions:
    tempfilename = filename + ".tmp" + str(randint(0,100000))
    with open(tempfilename + ".tex", "w") as f:
      f.write(document.build(solutions, rubrics, metadata).encode('UTF-8'))
    code = call(["pdflatex", tempfilename + ".tex", "-quiet"])
    os.remove(tempfilename + ".aux")
    os.remove(tempfilename + ".log")
    if code:
      os.rename(tempfilename + ".tex", filename + ".tex")
      print "\n\nError: pdflatex reported an error."
      print "Temporary LaTeX file {} not deleted so that it can be manually inspected, if desired.".format(filename + ".tex")
      os.remove(tempfilename + ".pdf")
      exit(1)
    os.remove(tempfilename + ".tex")
    while os.path.exists(filename + ".pdf"):
      print "\nWarning: {} already exists.".format(filename + ".pdf")
      response = raw_input("Type a new name or a blank line to replace file: ")
      if not response: break
      elif response.endswith(".pdf"):
        filename = response[:-4]
        assert filename
      else:
        filename = response
    os.rename(tempfilename + ".pdf", filename + ".pdf")
  else:
    print "Error: No problems were added to the build successfully"

def build_doc(settings):
  document = Document(settings.document)
  try:
    tree = ET.parse(settings.document)
    document.parse_tree(tree)
    build(document, settings.filename, settings.solutions, settings.rubrics, settings.metadata)
  except (ImproperXmlException, ET.ParseError):
    print "Error: Could not parse {}".format(settings.document)
    
  
    
def build_if(settings):
  document = Document()
  document.name = "".join(settings.title)
  # TODO:
  document.year = "1901"
  document.due = "Never"
  document.blurb = ""
  
  if os.path.isdir(settings.directory):
    for dirpath, dirnames, filenames in os.walk(settings.directory):
      for filename in filenames:
        if filename.endswith(".xml"):
          filename = os.path.join(dirpath, filename)
          try:
            tree = ET.parse(filename)
            problem = Problem(filename)
            problem.parse_tree(tree, validate_versions=False)
            version = problem.newest_version()
            version.validate()
            
            if satisfies(version, settings, problem.used_in):
              document.versions.append(version)
            
          except (ImproperXmlException, ET.ParseError):
            pass
    build(document, settings.filename, settings.solutions, settings.rubrics, settings.metadata)
  else:
    print "Error: The directory {} does not exist".format(settings.directory)
  
def build_single(settings):
  document = Document("")
  document.name = "".join(settings.title)
  #TODO
  document.year = "1900"
  document.due = "Never"
  document.blurb = ""
  outname = ""
  if settings.problem.endswith(".xml"):
    outname = settings.problem[:-4] + ".pdf"
  else:
    print "Error: problem file does not have a .xml extension"
    exit(1)
  
  try:
    tree = ET.parse(settings.problem)
    problem = Problem(settings.problem)
    problem.parse_tree(tree, validate_versions=False)
    version = problem.newest_version()
    version.validate()
    
    document.versions.append(version)
  except (ImproperXmlException, ET.ParseError):
    print "Warning: Could not parse {}".format(settings.problem)
      
  build(document, outname, settings.solutions, settings.rubrics, settings.metadata)

def build_specific(settings):
  document = Document("")
  document.name = "".join(settings.title)
  #TODO
  document.year = "1900"
  document.due = " "
  
  for filename in settings.problems:
    try:
      tree = ET.parse(filename)
      problem = Problem(filename)
      problem.parse_tree(tree, validate_versions=False)
      version = problem.newest_version()
      version.validate()
      
      document.versions.append(version)
    except (ImproperXmlException, ET.ParseError):
      print "Warning: Could not parse {}".format(settings.filename)
      
  build(document, settings.filename, settings.solutions, settings.rubrics, settings.metadata)
    
def add_doc_parser(parser):
  subparser = parser.add_parser('doc', help='Builds a particular document XML file into a pdf')
  subparser.set_defaults(func=build_doc)
  subparser.add_argument('document', metavar='D', help='The document XML file to build')
  subparser.add_argument('filename', metavar='O', help='The destination of the output PDF')
  subparser.add_argument('-m', dest='metadata', action='store_true', default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', default=False, help='Builds the problems with solutions')
    
def apply_predicate_arguments(subparser):
  subparser.add_argument('-m', dest='metadata', action='store_true', default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', default=False, help='Builds the problems with solutions')
  subparser.add_argument('--allowed-topics', required=False, dest='allowed_topics', nargs='+', help='If present, will restrict the allowed topics: a problem will be not be built if it uses any topic outside of the provided')
  subparser.add_argument('--authors', required=False, dest='authors', nargs='+', help='If present, restricts to problems which were written by any of the given authors')
  subparser.add_argument('--grep', required=False, dest='grep', nargs='+', help='If present, restricts to problems which contain within the rubric, solution, or body that contain all of the given words. Words are treated separately, but case-insensitively.')
  subparser.add_argument('--not-used-in', required=False, dest='not_used_in', nargs='+', 
      help='If present, restricts to problems which were used in none of the given years')
  subparser.add_argument('--required-topics', required=False, dest='required_topics', nargs='+', 
      help='If present, will specify the required topics: a problem will be built only if it uses at least one of the provided')
  subparser.add_argument('--required-types', required=False, dest='required_types', nargs='+', 
      help='If present, will specify the required types: a problem will be built only if it uses at least one of the provided')
  subparser.add_argument('--title', nargs=1, required=False, default="Problem", help='Sets the title of the problem build')
  subparser.add_argument('--todo', dest='todo', action='store_true', default=False, help='If present, restricts to problems that have "todo" in their solution or rubric.')
  subparser.add_argument('--used-in', required=False, dest='used_in', nargs='+', 
      help='If present, restricts to problems which were used in any of the given years')
  subparser.add_argument('--written', required=False, dest='written', nargs='+', 
      help='If present, will specify a set of years that a problem\'s most recent version may have been written (to be included)')
    
def add_from_parser(parser):
  subparser = parser.add_parser('from', help='Builds all problems that satisfy the given predicates within a particular directory')
  subparser.set_defaults(func=build_if)
  subparser.add_argument('directory', help='The search directory containing all problems to examine')
  subparser.add_argument('filename', metavar='O', help='The destination of the output PDF')
  apply_predicate_arguments(subparser)
  
def add_all_parser(parser):
  subparser = parser.add_parser('all', help='Builds all problems that satisfy the given predicates within the problem root directory')
  subparser.set_defaults(func=build_if, directory=get_problem_root())
  subparser.add_argument('filename', metavar='O', help='The destination of the output PDF')  
  apply_predicate_arguments(subparser)
    
def add_problem_parser(parser):
  subparser = parser.add_parser('problems', help='Builds a problem or series of problems, in order')
  subparser.set_defaults(func=build_specific)
  subparser.add_argument('filename', metavar='O', help='The destination of the output PDF')
  subparser.add_argument('problems', metavar='P', nargs='+', help='The locations of the problems to build')
  subparser.add_argument('-m', dest='metadata', action='store_true', default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', default=False, help='Builds the problems with solutions')
  subparser.add_argument('--title', nargs=1, required=False, default="Problem", help='Sets the title of the problem build')

def add_single_parser(parser):
  subparser = parser.add_parser('single', help='Builds a single problem XML file into a pdf of the same name')
  subparser.set_defaults(func=build_single)
  subparser.add_argument('problem', metavar='P', help='The problem XML file to build')
  subparser.add_argument('-m', dest='metadata', action='store_true', default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', default=False, help='Builds the problems with solutions')
  subparser.add_argument('--title', nargs=1, required=False, default="Problem", help='Sets the title of the problem build')
  
def build_args():
  """Parses command-line arguments using argparse and returns an object containing runtime information."""
  parser = argparse.ArgumentParser(description='Builds PDFs from CS22 XML files')
  subparsers = parser.add_subparsers(help='How to choose which files to build')
  
  add_all_parser(subparsers)
  add_doc_parser(subparsers)
  add_from_parser(subparsers)
  add_problem_parser(subparsers)
  add_single_parser(subparsers)
  
  return parser.parse_args()

def main():
  settings = build_args()
  settings.func(settings)
  
if __name__ == '__main__':
  main()