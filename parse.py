import xml.etree.ElementTree as ET
import string

TOPICS = string.split("basic big_o circuits counting equivalence_relations graph_theory logic mod number_theory pigeonhole probability relations set_theory todo")

TYPES = string.split("bijective computation contradiction contrapositive direct element_method induction large notation piece proof repetitive todo")

class ImproperXmlException(Exception):
  pass
  
def split_add(before, raw):
  return before + map(lambda x: string.strip(x, " ,\t"), string.split(raw))
      
class Version:
  def __xml_assert(self, predicate, str):
    if not predicate:
      print "Error in {} (version {}): {}".format(self.filename, self.id, str)
      raise ImproperXmlException()
      
  def __parse_author(self, attributes, body):
    self.authors = split_add(self.authors, body)
  
  def __parse_body(self, attributes, body):
    self.__xml_assert(self.body is None, "duplicate body")
    self.body = body
    
  def __parse_dep(self, attributes, body):
    self.deps = split_add(self.deps, body)
    
  def __parse_param(self, attributes, body):
    self.__xml_assert('name' in attributes, "parameter has no name")
    self.__xml_assert(attributes['name'] not in self.params,
        "duplicate parameter {}".format(attributes['name']))
    self.params[attributes['name']] = string.strip(body)
    
  def __parse_rubric(self, attributes, body):
    self.__xml_assert(self.rubric is None, "duplicate rubric")
    self.rubric = body
    
  def __parse_solution(self, attributes, body):
    self.__xml_assert(self.solution is None, "duplicate solution")
    self.solution = body
    
  def __parse_topic(self, attributes, body):
    self.topics = split_add(self.topics, body)
    
  def __parse_type(self, attributes, body):
    self.types = split_add(self.types, body)
    
  def __parse_year(self, attributes, body):
    self.__xml_assert(self.year is None, "duplicate year tag")
    self.year = body
    
  __parsers = {'author':__parse_author, 'authors':__parse_author,
      'body':__parse_body,
      'dep':__parse_dep, 'deps':__parse_dep,
          'dependency':__parse_dep, 'dependencies':__parse_dep,
      'param':__parse_param, 'parameter':__parse_param,
      'rubric':__parse_rubric,
      'solution':__parse_solution,
      'topic':__parse_topic, 'topics':__parse_topic,
      'type':__parse_type, 'types':__parse_type,
      'year':__parse_year}

  def __init__(self, filename, id):
    self.filename = filename
    self.id = id
    
    self.authors = []
    self.topics = []
    self.types = []
    self.year = None
    self.params = dict()
    self.deps = []
    self.body = None
    self.solution = None
    self.rubric = None
    
  def parse(self, tag):
    self.__xml_assert(tag.tag in Version.__parsers, 
        "Invalid tag '{}'".format(tag.tag))
    Version.__parsers[tag.tag](self, tag.attrib, tag.text)
    
  def pretty_print(self, solution=False, rubric=False, metadata=False):
    return ("\n".join(["\\newcommand\\" + name + "{" + value + "}" 
              for name, value in self.params]) +
            ("\\texttt{" + self.filename.replace('_', "\\_") + "}\\\\\\textbf{Topics Covered: }" +
              ", ".join(self.topics).replace('_', ' ') if metadata else "")
            + "\n\n" + self.body +
            ("\\begin{mdframed}\n\\subsubsection*{Solution}\n\n" 
              + self.solution + "\\end{mdframed}\n"
             if solution else "") +
            ("\\begin{mdframed}\n\\subsubsection*{Rubric}\n\n" 
              + self.rubric + "\\end{mdframed}\n"
             if rubric else ""))
    
  def validate(self):
    self.__xml_assert(self.authors, "No authors")
    self.__xml_assert(self.body, "No body")
    self.__xml_assert(self.rubric, "No rubric")
    self.__xml_assert(self.solution, "No solution")
    self.__xml_assert(self.topics, "No topics")
    for t in self.topics:
      self.__xml_assert(t in TOPICS, "Invalid topic: {}".format(t))
    self.__xml_assert(self.types, "No question types")
    for t in self.types:
      self.__xml_assert(t in TYPES, "Invalid type: {}".format(t))
    
class Problem:
  def __xml_assert(self, predicate, str):
    if not predicate:
      print "Error in {}: {}".format(self.filename, str)
      raise ImproperXmlException()

  def add_version(self, block):
    self.__xml_assert(block.tag == 'version', 
        "Invalid version tag '{}'".format(block.tag))
    self.__xml_assert('id' in block.attrib, "Version with no id")
    v = Version(self.filename, block.attrib['id'])
    self.__xml_assert(v.id not in self.__versions, 
        "Duplicate version {}".format(v.id))
    self.__versions[v.id] = v
    for child in block:
      v.parse(child)
    v.validate()
    
  def get_version(self, id):
    if id in self.__versions:
      return self.__versions[id]
    raise AttributeError()
    
  def get_newest(self):
    return self.__versions[max(self.__versions.keys())]

  def __init__(self, filename, tree=None):
    self.filename = filename
    if tree is None:
      try:
        tree = ET.parse(filename)
      except ET.ParseError:
        print "Error: Could not parse {}".format(filename)
        raise ImproperXmlException()
    root = tree.getroot()
    
    self.__xml_assert(root.tag == 'problem', 
        "Invalid root tag '{}' (should be 'problem')".format(root.tag))
    self.__xml_assert(len(root) > 0, "Empty file")
    
    self.__versions = dict()
    map(self.add_version, root[:])
    
class Document:
  def __xml_assert(self, predicate, str):
    if not predicate:
      print "Error in {}: {}".format(self.filename, str)
      raise ImproperXmlException()
      
  def __parse_due(self, attributes, body):
    self.__xml_assert(self.due is None, "duplicate due tag")
    self.due = body
    
  def __parse_name(self, attributes, body):
    self.__xml_assert(self.name is None, "duplicate name tag")
    self.name = body
    
  def __parse_problem(self, attributes, body):
    prob = Problem(body)
    if 'version' in attributes:
      self.problems.append(prob.get_version(attributes['version']))
    else:
      if attributes:
        print "Warning: tag for problem {} has unknown attributes {}".format(body, attributes.keys())
      self.problems.append(prob.get_newest())
      
    
  def __parse_year(self, attributes, body):
    self.__xml_assert(self.year is None, "duplicate year tag")
    self.year = body
      
  __parsers = {
      'name':__parse_name,
      'due':__parse_due,
      'problem':__parse_problem,
      'year':__parse_year}
      
  def __parse_child(self, tag):
    self.__xml_assert(tag.tag in Document.__parsers, 
        "Invalid tag '{}'".format(tag.tag))
    Document.__parsers[tag.tag](self, tag.attrib, tag.text)
    
  def validate(self):
    self.__xml_assert(self.year is not None, "no year provided")
    self.__xml_assert(self.name is not None, "no assignment name provided")
    self.__xml_assert(self.due is not None, "no due date provided")
    self.__xml_assert(self.problems, "no problems provided")
    
  def parse(self, filename):
    self.filename = filename
    tree = ET.parse(filename)
    root = tree.getroot()
    
    self.__xml_assert(root.tag == 'assignment',
        "Invalid root tag '{}' (should be 'assignment')".format(root.tag))
    
    for child in root:
      self.parse(child)
    self.validate()
    
  def add_problem(self, version):
    self.problems.append(version)
    
  def __init__(self):
    self.year = None
    self.due = None
    self.name = None
    self.problems = []
    
  def problem_dependencies(self):
    deps = set()
    for p in self.problems:
      deps = deps.union(p.deps)
    
    return "\n".join(["\\usepackage{" + x + "}" for x in deps]) if deps else ""
    
  def header(self):
    dependencies = self.problem_dependencies()
    return "\\documentclass[12pt,letterpaper]{article}\n\n\
\\usepackage{simple22}\n\
\\fancypagestyle{firstpagestyle} {\n\
  \\renewcommand{\\headrulewidth}{0pt}%\n\
  \\lhead{\\textbf{CSCI 0220}}%\n\
  \\chead{\\textbf{Discrete Structures and Probability}}%\n\
  \\rhead{C. Klivans}%\n\
}\n\n\
\\fancypagestyle{fancyplain} {%\n\
  \\renewcommand{\\headrulewidth}{0pt}%\n\
  \\lhead{\\textbf{CSCI 0220}}%\n\
  \\chead{" + self.name + "}%\n\
  \\rhead{\\textit{" + self.due + "}}%\n\
}\n\\pagestyle{fancyplain}\n" + dependencies + "\n\n"
  
  def document(self, body):
    return "\\begin{document}\n\
  \\thispagestyle{firstpagestyle}\n\
  \\begin{center}\n\
    {\\huge \\textbf{" + self.name + "}}\n\n\
    {\\large \\textit{Due: " + self.due + "}}\n\
  \\end{center}\n\n\
  \\hwblurb\n\n" + body + "\end{document}"
  
  def problem_str(self, solutions=False, rubrics=False, metadata=False):
    return "\n\n".join(
      ["\\subsection*{Problem " + str(i+1) + "}\n{\n" + 
        v.pretty_print(solutions,rubrics,metadata) + "\n}\n\n" 
        for i, v in enumerate(self.problems)])
