import argparse
import os
from parse import Problem, Document, ImproperXmlException
from subprocess import call
from random import randint
from xml.etree.ElementTree import ParseError

def build(document, filename, solutions=False, rubrics=False, metadata=False):
  if filename.endswith(".pdf"):
    filename = filename[:-4]
  else:
    print "Warning: Output will be named {}.pdf".format(filename)
  if document.problems:
    tempfilename = filename + ".tmp" + str(randint(0,100000))
    with open(tempfilename + ".tex", "w") as f:
      f.write(document.header())
      f.write(document.document(document.problem_str(solutions, rubrics, metadata)))
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

def build_if(settings):
  document = Document()
  document.name = "".join(settings.title)
  document.year = "1901"
  document.due = " "
  
  if os.path.isdir(settings.directory):
    for dirpath, dirnames, filenames in os.walk(settings.directory):
      for filename in filenames:
        if filename.endswith(".xml"):
          try:
            problem = Problem(os.path.join(dirpath, filename)).get_newest()
            sat_allowed = not settings.allowed_topics or not [topic for topic in problem.topics if topic not in settings.allowed_topics]
            sat_required_topics = not settings.required_topics or [topic for topic in problem.topics if topic in settings.required_topics]
            sat_required_types = not settings.required_types or [type for type in problem.types if type in settings.required_types]
            if sat_allowed and sat_required_topics and sat_required_types:
              document.add_problem(problem)
          except ImproperXmlException:
            pass
    build(document, settings.filename, settings.solutions, settings.rubrics, settings.metadata)
  else:
    print "Error: The directory {} does not exist".format(settings.directory)
  

def build_specific(settings):
  document = Document()
  document.name = "".join(settings.title)
  document.year = "1900"
  document.due = " "
  
  for problem in settings.problems:
    try:
      document.add_problem(Problem(problem).get_newest())
    except ImproperXmlException, ParseError:
      print "Warning: Could not parse {}".format(problem)
      
  build(document, settings.filename, settings.solutions, settings.rubrics, settings.metadata)
    
def add_if_parser(parser):
  subparser = parser.add_parser('if', help='Builds all problems that satisfy the given predicates within a particular directory')
  subparser.set_defaults(func=build_if)
  subparser.add_argument('directory', help='The search directory containing all problems to examine')
  subparser.add_argument('-m', dest='metadata', action='store_true', default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', default=False, help='Builds the problems with solutions')
  subparser.add_argument('--allowed-topics', required=False, dest='allowed_topics', nargs='+', 
      help='If present, will restrict the allowed topics: a problem will be not be built if it uses any topic outside of the provided')
  subparser.add_argument('--required-topics', required=False, dest='required_topics', nargs='+', 
      help='If present, will specify the required topics: a problem will be built only if it uses at least one of the provided')
  subparser.add_argument('--required-types', required=False, dest='required_types', nargs='+', 
      help='If present, will specify the required types: a problem will be built only if it uses at least one of the provided')
  subparser.add_argument('--title', nargs=1, required=False, default="Problem", help='Sets the title of the problem build')
    
def add_problem_parser(parser):
  subparser = parser.add_parser('problems', help='Builds a problem or series of problems, in order')
  subparser.set_defaults(func=build_specific)
  subparser.add_argument('problems', metavar='P', nargs='+', help='The locations of the problems to build')
  subparser.add_argument('-m', dest='metadata', action='store_true', default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', default=False, help='Builds the problems with solutions')
  subparser.add_argument('--title', nargs=1, required=False, default="Problem", help='Sets the title of the problem build')

  
def build_args():
  """Parses command-line arguments using argparse and returns an object containing runtime information."""
  parser = argparse.ArgumentParser(description='Builds PDFs from CS22 XML files')
  parser.add_argument('filename', metavar='O', help='The destination of the output PDF')
  subparsers = parser.add_subparsers(help='How to choose which files to build')
  
  add_if_parser(subparsers)
  add_problem_parser(subparsers)
  
  return parser.parse_args()

def main():
  settings = build_args()
  settings.func(settings)
  
  
main()