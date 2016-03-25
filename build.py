import argparse
import os
import errno
from parseable import ImproperXmlException
from problem import Problem, Document
from subprocess import call
from random import randint
from config import get_problem_root
import xml.etree.ElementTree as ET
from color import *
from pdfbuilder import build, temp_file_remove

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
      if settings.not_used_in and actual.year in settings.not_used_in and not actual.private:
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

def build_wrapper(document, filename, settings):
  filename = os.path.basename(filename)
  if document.versions:
    if filename.endswith(".pdf"):
      filename = filename[:-4]
      assert filename
    else:
      print_warning("Output will be named '{}.pdf'".format(filename))
      
    resources = set()
    for version in document.versions:
      for resource in version.resources:
        resources.add(resource)
    build(document.build(settings.solutions, 
            settings.rubrics, settings.metadata),
        resources,
        filename,
        settings.keep)
  else:
    print_error("No problems were added to the build successfully.")

def build_doc(settings):
  document = Document(settings.document)
  try:
    tree = ET.parse(settings.document)
    document.parse_tree(tree)
    build_wrapper(document, settings.filename, settings)
  except (ImproperXmlException, ET.ParseError):
    print_error("Could not parse {}".format(settings.document))
    
def build_each(settings):
  document = Document(settings.document)
  try:
    tree = ET.parse(settings.document)
    document.parse_tree(tree)
    settings.metadata = True
    settings.solutions = True
    settings.rubrics = True
    settings.keep = False
    
    for i,v in enumerate(document.versions):
      problem_document = Document()
      problem_document.name = document.name + " Problem " + str(i+1)
      problem_document.year = "1901"
      problem_document.due = "Grading"
      problem_document.blurb = ""
      problem_document.versions.append(v)
      
      build_wrapper(problem_document, settings.document[:-4] + "." + str(i+1) + ".pdf", settings)
  except (ImproperXmlException, ET.ParseError):
    print_error("Could not parse {}".format(settings.document))
    
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
            
            currentVersions = []
            if settings.all:
              everyVersion = problem.get_versions()
              currentVersions = [everyVersion[0]] + [v for v in everyVersion[1:] if v.standalone]
            else:
              currentVersions = [problem.newest_version()]
              
            firstInProblem = settings.all # only use separators if including multiple versions per problem, 
            for version in currentVersions:
              try:
                version.validate()
                if satisfies(version, settings, problem.used_in):
                  version.separateFromPrevious = firstInProblem
                  firstInProblem = False
                  document.versions.append(version)
                  if settings.verbose:
                    print color("Added: ", color_code(GREEN)), filename, "Version {}".format(version.vid)
                elif settings.verbose:
                  print color("Skipped (Predicate): ", color_code(CYAN)), filename, "Version {}".format(version.vid)
              except ImproperXmlException:
                if settings.verbose:
                  print color("Error (Validation): ", color_code(YELLOW)), filename, "Version {}".format(version.vid)     
          except ImproperXmlException:
            if settings.verbose:
              print color("Error (Problem Validation): ", color_code(YELLOW)), filename     
          except ET.ParseError:
            if settings.verbose:
              print color("Error (XML Parsing): ", color_code(RED, bold=True)), filename
          except IOError as e:
            # Permission errors can be safely skipped
            if e.errno != errno.EACCES: 
              print color("Error (IO): ", color_code(RED)), filename
              raise # TODO
            elif settings.verbose:
              print color("Error (Permissions): ", color_code(MAGENTA)), filename
          except Exception:
            print_error(filename)
            raise
    build_wrapper(document, settings.filename, settings)
  else:
    print_error("The directory '{}' does not exist".format(settings.directory))
 
def build_list(settings):
  if os.path.isdir(get_problem_root()):
    for dirpath, dirnames, filenames in os.walk(get_problem_root()):
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
              if settings.verbose:
                print color("Added: ", color_code(GREEN)), filename
              else:
                print filename
            elif settings.verbose:
              print color("Skipped (Predicate): ", color_code(CYAN)), filename
          except ImproperXmlException:
            if settings.verbose:
              print color("Error (Validation): ", color_code(YELLOW)), filename
          except ET.ParseError:
            if settings.verbose:
              print color("Error (XML Parsing): ", color_code(RED, bold=True)), filename
          except IOError as e:
            # Permission errors can be safely skipped
            if e.errno != errno.EACCES: 
              print color("Error (IO): ", color_code(RED)), filename
              raise # TODO
            elif settings.verbose:
              print color("Error (Permissions): ", color_code(MAGENTA)), filename
          except Exception:
            print_error(filename)
            raise
  else:
    print_error("The directory '{}' does not exist".format(get_problem_root()))
    
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
    assert outname != ".pdf"
  else:
    print_error("Problem file does not have a .xml extension")
    exit(1)
  
  try:
    tree = ET.parse(settings.problem)
    problem = Problem(settings.problem)
    problem.parse_tree(tree, validate_versions=False)
    version = problem.newest_version()
    version.validate()
    
    document.versions.append(version)
    
    build_wrapper(document, outname, settings)
  except (ImproperXmlException, ET.ParseError):
    print_warning("Could not parse '{}'".format(settings.problem))
    print "Run '22edit validate' to check for common problems."
      

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
      print_warning("Could not parse {}".format(settings.filename))
      
  build_wrapper(document, settings.filename, settings)
    
def add_common_flags(subparser, title=True):
  subparser.add_argument('-k', dest='keep', action='store_true', 
      default=False, help='Keeps the intermediate .tex file')
  subparser.add_argument('-m', dest='metadata', action='store_true', 
      default=False, help='Builds the problems with attached metadata')
  subparser.add_argument('-r', dest='rubrics', action='store_true', 
      default=False, help='Builds the problems with rubrics')
  subparser.add_argument('-s', dest='solutions', action='store_true', 
      default=False, help='Builds the problems with solutions')
  if title:
    subparser.add_argument('--title', nargs=1, required=False, 
        default="Problem", help='Sets the title of the problem build')

def add_verbose_flag(subparser):
  subparser.add_argument('--verbose', '-v', action='store_true',
      dest='verbose', default=False,
      help='Prints a verbose description of the files being considered')
    
def add_doc_parser(parser):
  subparser = parser.add_parser('doc', 
      help='Builds a particular assignment XML file into a pdf')
  subparser.set_defaults(func=build_doc)
  subparser.add_argument('document', metavar='D', 
      help='The assignment XML file to build')
  subparser.add_argument('filename', metavar='O', 
      help='The destination of the rendered PDF')
  add_common_flags(subparser, title=False)
    
def add_predicate_flags(subparser):
  subparser.add_argument('--all', required=False, 
      dest='all', action='store_true', default=False,      
      help='If present, will include any standalone versions in addition to the most recent ones')
  subparser.add_argument('--allowed-topics', required=False, 
      dest='allowed_topics', nargs='+', 
      help='If present, will restrict the allowed topics: a problem will not be built if it uses any topic outside of the provided')
  subparser.add_argument('--authors', required=False, dest='authors', 
      nargs='+', help='If present, restricts to problems which were written by any of the given authors')
  subparser.add_argument('--grep', required=False, dest='grep', nargs='+', 
      help='If present, restricts to problems which contain within the rubric, solution, or body that contain all of the given words. Words are treated separately, but case-insensitively.')
  subparser.add_argument('--not-used-in', required=False, dest='not_used_in', 
      nargs='+', help='If present, restricts to problems which were used in none of the given years')
  subparser.add_argument('--required-topics', required=False, 
      dest='required_topics', nargs='+', 
      help='If present, will specify the required topics: a problem will be built only if it uses at least one of the provided')
  subparser.add_argument('--required-types', required=False, 
      dest='required_types', nargs='+', 
      help='If present, will specify the required types: a problem will be built only if it uses at least one of the provided')
  subparser.add_argument('--todo', dest='todo', action='store_true', 
      default=False, help='If present, restricts to problems that have "todo" in their solution or rubric.')
  subparser.add_argument('--used-in', required=False, dest='used_in', 
      nargs='+', help='If present, restricts to problems which were used in any of the given years')
  subparser.add_argument('--written', required=False, dest='written', 
      nargs='+', help='If present, will specify a set of years that a problem\'s most recent version may have been written (to be included)')
    
def add_each_parser(parser):
  subparser = parser.add_parser('each', 
      help='Builds each problem of a document into separate PDFs, in preparation for grading')
  subparser.set_defaults(func=build_each)
  subparser.add_argument('document', metavar='D', 
      help='The assignment XML file where each problem is stored')
  
def add_from_parser(parser):
  subparser = parser.add_parser('from', 
      help='Builds all problems that satisfy the given predicates within a particular directory')
  subparser.set_defaults(func=build_if)
  subparser.add_argument('directory', 
      help='The search directory containing all problems to examine')
  subparser.add_argument('filename', metavar='O', 
      help='The destination of the rendered PDF')
  add_common_flags(subparser)
  add_predicate_flags(subparser)
  add_verbose_flag(subparser)
  
def add_all_parser(parser):
  subparser = parser.add_parser('all', 
      help='Builds all problems that satisfy the given predicates within the problem root directory')
  subparser.set_defaults(func=build_if, directory=get_problem_root())
  subparser.add_argument('filename', metavar='O', 
      help='The destination of the output PDF')
  add_common_flags(subparser)
  add_predicate_flags(subparser)
  add_verbose_flag(subparser)

def add_list_parser(parser):
  subparser = parser.add_parser('list', 
      help='Lists all problems that satisfy the given predicates within the problem root directory')
  subparser.set_defaults(func=build_list)
  add_predicate_flags(subparser)
  add_verbose_flag(subparser)
  
def add_problem_parser(parser):
  subparser = parser.add_parser('problems', 
      help='Builds a problem or series of problems, in order')
  subparser.set_defaults(func=build_specific)
  subparser.add_argument('filename', metavar='O', 
      help='The destination of the rendered PDF')
  subparser.add_argument('problems', metavar='P', nargs='+', 
      help='The locations of the problems to build')
  add_common_flags(subparser)

def add_single_parser(parser):
  subparser = parser.add_parser('single', 
      help='Builds a single problem XML file into a pdf of the same name')
  subparser.set_defaults(func=build_single)
  subparser.add_argument('problem', metavar='P', 
      help='The problem XML file to build')
  add_common_flags(subparser)
  
def build_args():
  """Parses command-line arguments using argparse and returns an 
  object containing runtime information."""
  parser = argparse.ArgumentParser(description='Builds PDFs from LaTeXML files')
  subparsers = parser.add_subparsers(
      help='Different methods of rendering problems')
  
  add_all_parser(subparsers)
  add_doc_parser(subparsers)
  add_each_parser(subparsers)
  add_from_parser(subparsers)
  add_list_parser(subparsers)
  add_problem_parser(subparsers)
  add_single_parser(subparsers)
  
  return parser.parse_args()

def main():
  settings = build_args()
  settings.func(settings)
  
if __name__ == '__main__':
  main()