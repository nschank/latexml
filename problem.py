import xml.etree.ElementTree as ET
import string
from os.path import exists, isabs, join
from datetime import date
from parseable import XmlParseable, ImproperXmlException
from config import get_topics, get_types, get_blurb, get_inclusions, get_problem_root, get_default_author
  
def split_add(before, raw):
  """Used by any fields which can be whitespace separated"""
  if raw is None:
    return before
  return before + map(lambda x: string.strip(x), string.split(raw))
      
class Version(XmlParseable):
  """
  Internal representation of a problem Version.
  """
  def xml_assert(self, predicate, str):
    """Overridden to show ID"""
    if not predicate:
      raise ImproperXmlException("Error in {} (version {}): {}".format(self.filename, self.vid, str))
      
  def __init__(self, filename, vid=None):
    """Has public fields so that the tools can use them, there isn't much point in protecting them"""
    self.filename = filename
    self.vid = vid
    
    self.standalone = False
    
    self.authors = []
    self.topics = []
    self.types = []
    self.year = None
    self.params = dict()
    self.deps = []
    self.resources = []
    self.body = None
    self.solution = None
    self.rubric = None
    
  def add_defaults(self):
    self.authors = [get_default_author()]
    self.year = str(date.today().year)
    
  def _meta(self):
    filename = "\\texttt{" + self.filename.replace('_', "\\_") + "}"
    topics = "\\textbf{Topics Covered: }" + ", ".join(self.topics).replace('_', ' ')
    types = "\\textbf{Types: }" + ", ".join(self.types).replace('_', ' ')
    version = " Version " + str(self.vid) + " (Written " + str(self.year) + ")"
    authors = "\\textbf{Authors}: " + ", ".join(self.authors).replace('_', "\\_")
    return "\\\\".join([filename + version, topics, types, authors])
    
  def _solution(self):
    return ("\\begin{mdframed}\n{\\subsubsection*{Solution}\\setcounter{enum22i}{0}\n\n" 
              + self.solution + "}\\end{mdframed}\n")
  def _rubric(self):
    return ("\\begin{mdframed}\n{\\subsubsection*{Rubric}\\setcounter{enum22i}{0}\n\n" 
              + self.rubric + "}\\end{mdframed}\n")
    
  def pretty_print(self, solution=False, rubric=False, metadata=False):
    """Prints this version's contents as valid LaTeX, for building"""
    return ("\n".join(["\\newcommand\\" + name + "{" + value + "}" 
              for name, value in self.params.iteritems()]) +
            (self._meta() if metadata else "")
            + "\n\n{\\setcounter{enum22i}{0}\n" + self.body + "\n}" +
             (self._solution() if solution else "") +
             (self._rubric() if rubric else ""))
    
  def to_element(self):
    version = ET.Element('version')
    version.set('id', str(self.vid))
    if self.standalone:
      version.set('standalone', "true")
    
    author = ET.SubElement(version, 'authors')
    author.text = " ".join(self.authors)
    
    year = ET.SubElement(version, 'year')
    year.text = self.year
    
    topics = ET.SubElement(version, 'topics')
    topics.text = " ".join(self.topics) if self.topics else " "
    types = ET.SubElement(version, 'types')
    types.text = " ".join(self.types) if self.types else " "
    
    for name, value in self.params.iteritems():
      param = ET.SubElement(version, 'param')
      param.set('name', name)
      param.text = value
    
    if self.deps:
      deps = ET.SubElement(version, 'dependencies')
      deps.text = " ".join(self.deps)
    for resource in self.resources:
      tag = ET.SubElement(version, 'resource')
      tag.text = resource
      
    body = ET.SubElement(version, 'body')
    body.text = self.body
    
    solution = ET.SubElement(version, 'solution')
    solution.text = self.solution
    
    rubric = ET.SubElement(version, 'rubric')
    rubric.text = self.rubric
    
    return version
    
  def validate(self):
    """Asserts that the Version satisfies the minimal requirements of being complete"""
    self.xml_assert(self.authors, "No authors")
    self.xml_assert(self.body, "No body")
    self.xml_assert(self.rubric, "No rubric")
    self.xml_assert(self.solution, "No solution")
    self.xml_assert(self.topics, "No topics")
    for t in self.topics:
      self.xml_assert(t in get_topics(), "Invalid topic: {}".format(t))
    self.xml_assert(self.types, "No types")
    for t in self.types:
      self.xml_assert(t in get_types(), "Invalid type: {}".format(t))
    self.xml_assert(self.year, "No year")
    self.xml_assert(self.vid is not None, "No id")
      
  def __parse_author(self, attributes, body):
    self.authors = split_add(self.authors, body)
  
  def __parse_body(self, attributes, body):
    self.xml_assert(self.body is None, "duplicate body")
    self.body = body
    
  def __parse_dep(self, attributes, body):
    self.deps = split_add(self.deps, body)
    
  def __parse_param(self, attributes, body):
    self.xml_assert('name' in attributes, "parameter has no name")
    self.xml_assert(attributes['name'] not in self.params,
        "duplicate parameter {}".format(attributes['name']))
    self.xml_assert(body, 
        "Parameter {} has no value".format(attributes['name']))
    self.params[attributes['name']] = string.strip(body)
    
  def __parse_resource(self, attributes, body):
    self.xml_assert(body, "empty resource body")
    self.resources.append(body)
    
  def __parse_rubric(self, attributes, body):
    self.xml_assert(self.rubric is None, "duplicate rubric")
    self.rubric = body
    
  def __parse_solution(self, attributes, body):
    self.xml_assert(self.solution is None, "duplicate solution")
    self.solution = body
    
  def __parse_topic(self, attributes, body):
    self.topics = split_add(self.topics, body)
    
  def __parse_type(self, attributes, body):
    self.types = split_add(self.types, body)
    
  def __parse_year(self, attributes, body):
    self.xml_assert(self.year is None, "duplicate year tag")
    self.year = body
    
  __parsers = {'author':__parse_author, 'authors':__parse_author,
      'body':__parse_body,
      'dep':__parse_dep, 'deps':__parse_dep,
          'dependency':__parse_dep, 'dependencies':__parse_dep,
      'param':__parse_param, 'parameter':__parse_param,
      'resource':__parse_resource,
      'rubric':__parse_rubric,
      'solution':__parse_solution,
      'topic':__parse_topic, 'topics':__parse_topic,
      'type':__parse_type, 'types':__parse_type,
      'year':__parse_year}

  def parse_element(self, element):
    self.xml_assert(element.tag == 'version', 
        "Invalid version tag '{}'".format(element.tag))
    self.xml_assert('id' in element.attrib, "Version with no id")
    if 'standalone' in element.attrib:
      standalone = str.lower(element.attrib['standalone'])
      if standalone == 'true':
        self.standalone = True
      else:
        self.xml_assert(standalone == 'false',
          "Version has unknown value `{}' for the standalone attribute:".format(standalone))
      self.xml_assert(len(element.attrib) == 2,
        "Version has unknown attributes (only `id' and `standalone' are allowed): `{}'".format(str(element.attrib.keys())))
    else:
      self.xml_assert(len(element.attrib) == 1,
        "Version has unknown attributes (only `id' and `standalone' are allowed): `{}'".format(str(element.attrib.keys())))
    
    try: self.vid = int(element.attrib['id'])
    except ValueError: 
      self.xml_assert(False, 
        "Version has non-numeric id `{}'".format(element.attrib['id']))
    
    for tag in element:
      self.xml_assert(tag.tag in Version.__parsers, 
          "Invalid tag '{}'".format(tag.tag))
      Version.__parsers[tag.tag](self, tag.attrib, tag.text)
    
    
    
class Problem(XmlParseable):
  """
  Internal representation of a Problem, which contains many Versions 
  """
  def __init__(self, filename):
    self.filename = filename
    self.versions = dict()
    self.used_in = []
    
  def newest_version(self):
    return self.versions[max(self.versions)]
    
  def next_id(self):
    return 1 + max(self.versions)
    
  def parse_element(self, root, validate_versions=True):
    self.xml_assert(root.tag == 'problem', 
        "Invalid root tag '{}' (should be 'problem')".format(root.tag))
    self.xml_assert(len(root) > 0, "Empty file")
    
    for child in root:
      if child.tag == 'usedin':
        self.xml_assert('year' in child.attrib, "usedin tag must have year")
        self.xml_assert(child.text, "usedin tag must have text")
        self.xml_assert(child.attrib['year'] and child.attrib['year'] != 'unknown', "usedin year must be present and not 'unknown'")
        private = False
        if 'private' in child.attrib and str.lower(child.attrib['private']) == 'true':
          private = True
        self.used_in.append(UsedIn(child.attrib['year'], child.text, private))
      else:
        version = Version(self.filename)
        version.parse_element(child)
        if validate_versions or version.standalone:
          version.validate()
        self.xml_assert(version.vid not in self.versions, 
          "Duplicate version {}".format(version.vid))
        self.versions[version.vid] = version
      
  def parse_tree(self, tree, validate_versions=True):
    self.parse_element(tree.getroot(), validate_versions)
      
  def to_element(self):
    root = ET.Element('problem')
    for pair in self.used_in:
      usedin = ET.SubElement(root, 'usedin')
      usedin.set("year", pair.year)
      if pair.private:
        usedin.set("private", "true")
      usedin.text = pair.assignment_name
    for key in sorted(self.versions.keys(), reverse=True):
      root.append(self.versions[key].to_element())
    return root
      
class Document(XmlParseable):
  """
  Internal representation of a Document, which contains an ordered list of Versions to print as well
  as metadata used to create headers or other LaTeX things.
  """
  def __init__(self, filename=None, blurb=get_blurb()):
    self.year = None
    self.due = None
    self.name = None
    self.filename = filename
    self.versions = []
    self.blurb = blurb
    self.private = False
    
  def build(self, solutions=False, rubrics=False, metadata=False):
    return self._header() + self._document(self._problems(solutions, rubrics, metadata))
    
  def to_element(self):
    assign = ET.Element('assignment')
    if self.private:
      assign.set("private", "true")
    
    year = ET.SubElement(assign, 'year')
    year.text = self.year
    
    name = ET.SubElement(assign, 'name')
    name.text = self.name
    
    due = ET.SubElement(assign, 'due')
    due.text = self.due
    
    for v in self.versions:
      prob = ET.SubElement(assign, 'problem')
      prob.text = v.filename
      prob.set('version', str(v.vid))
    
    return assign
    
  
  def validate(self):
    """
    Ensures that a Document is ready for building
    """
    self.xml_assert(self.year is not None, "no year provided")
    self.xml_assert(self.name is not None, "no assignment name provided")
    self.xml_assert(self.due is not None, "no due date provided")
    self.xml_assert(self.versions, "no problems provided")
    
  def _additional_dependencies(self):
    deps = set()
    for v in self.versions:
      deps = deps.union(v.deps)
    
    return "\n".join(["\\usepackage{" + x + "}" for x in deps]) if deps else ""
  
  def _document(self, body):
    return """\\begin{document}
  \\thispagestyle{firstpagestyle}
  \\begin{center}
    {\\huge \\textbf{""" + self.name + """}}\n
    {\\large \\textit{Due: """ + self.due + """}}
  \\end{center}\n\n""" + self.blurb + "\n\n" + body + "\\end{document}"
  
  def _header(self):
    dependencies = self._additional_dependencies()
    return ("\\documentclass[12pt,letterpaper]{article}\n\n" +
      get_inclusions() +
      """\\fancypagestyle{firstpagestyle} {
  \\renewcommand{\\headrulewidth}{0pt}%
  \\lhead{\\textbf{CSCI 0220}}%
  \\chead{\\textbf{Discrete Structures and Probability}}%
  \\rhead{C. Klivans}%
}\n
\\fancypagestyle{fancyplain} {%
  \\renewcommand{\\headrulewidth}{0pt}%
  \\lhead{\\textbf{CSCI 0220}}%
  \\chead{""" + self.name + """}%
  \\rhead{\\textit{""" + self.due + """}}%
}\n\\pagestyle{fancyplain}\n""" + dependencies + "\n\n")

  def _problems(self, solutions=False, rubrics=False, metadata=False):
    return "\n\n".join(
      ["\\subsection*{Problem " + str(i+1) + "}\n{\n" + 
        v.pretty_print(solutions,rubrics,metadata) + "\n}\n\n" 
        for i, v in enumerate(self.versions)])

  def __parse_due(self, attributes, body):
    self.xml_assert(self.due is None, "duplicate due tag")
    self.due = body
    
  def __parse_name(self, attributes, body):
    self.xml_assert(self.name is None, "duplicate name tag")
    self.name = body
    
  def __parse_problem(self, attributes, body):
    if isabs(body):
      self.xml_assert(exists(body), "Problem file {} does not exist".format(body))
    elif not exists(body):
      tentative = join(get_problem_root(), body)
      self.xml_assert(exists(tentative), 
          "Could not find a problem file at either {} or in problem directory at {}".format(body, tentative))
      body = tentative
         
    prob = Problem(body)
    prob.parse_tree(ET.parse(body))
    if 'version' in attributes:
      try: self.versions.append(prob.versions[int(attributes['version'])])
      except ValueError:
        self.xml_assert(False, "Non-numeric version '{}' does not exist".format(attributes['version']))
      except KeyError:
        self.xml_assert(False, "No such version '{}'".format(attributes['version']))
    else:
      if attributes:
        print "Warning: tag for problem {} has unknown attributes {}".format(body, attributes.keys())
      self.versions.append(prob.newest_version())
      
  def __parse_year(self, attributes, body):
    self.xml_assert(self.year is None, "duplicate year tag")
    self.year = body
      
  __parsers = {
      'name':__parse_name,
      'due':__parse_due,
      'problem':__parse_problem,
      'title':__parse_name,
      'year':__parse_year}
      
  def parse_element(self, root):
    self.xml_assert(root.tag == 'assignment',
        "Invalid root tag '{}' (should be 'assignment')".format(root.tag))
    if "private" in root.attrib and str.lower(root.attrib["private"]) == "true":
      self.private = True
    for tag in root:
      self.xml_assert(tag.tag in Document.__parsers, 
          "Invalid tag '{}'".format(tag.tag))
      Document.__parsers[tag.tag](self, tag.attrib, tag.text)
    
class UsedIn:
  def __init__(self, year, assignment_name, private=False):
    self.year = year
    self.assignment_name = assignment_name
    self.private = private
    
