import xml.etree.ElementTree as ET
from os import getenv, getlogin
from parseable import XmlParseable, ImproperXmlException
import string
from copy import copy

class ConfigurationError(Exception):
  pass

class BuildConfiguration(XmlParseable):
  def __init__(self, filename=None):
    self.filename = filename
    self.author = None
    self.topics = []
    self.types = []
    self.blurb = None
    self.classname = None
    self.include = []
    self.problemroot = None
    self.professor = None
    self.resourceroot = None
    self.shortname = None
    
  def __parse_author(self, attributes, body):
    self.xml_assert(not attributes, "author tag should have no attributes")
    self.xml_assert(self.author is None, "duplicate author tag")
    self.author = body
    
  def __parse_blurb(self, attributes, body):
    self.xml_assert(not attributes, "blurb tag should have no attributes")
    self.xml_assert(self.blurb is None, "duplicate blurb tag")
    self.blurb = body
    
  def __parse_classname(self, attributes, body):
    self.xml_assert(not attributes, "classname tag should have no attributes")
    self.xml_assert(body, "classname tag must have a body")
    self.xml_assert(self.classname is None, "duplicate classname tag")
    self.classname = string.strip(body)
    
  def __parse_include(self, attributes, body):
    self.xml_assert(not attributes, "include tag should have no attributes")
    self.xml_assert(body, "include tag must have a body")
    try:
      with open(string.strip(body)) as f:
        self.include.append(''.join(f.readlines()))
    except IOError:
      raise ConfigurationError("Could not include {}".format(body))
      
  def __parse_problemroot(self, attributes, body):
    self.xml_assert(not attributes, "problemroot tag should have no attributes")
    self.xml_assert(body, "problemroot tag must have a body")
    self.xml_assert(self.problemroot is None, "duplicate problemroot tag")
    self.problemroot = string.strip(body)
    
  def __parse_professor(self, attributes, body):
    self.xml_assert(not attributes, "professor tag should have no attributes")
    self.xml_assert(body, "professor tag must have a body")
    self.xml_assert(self.professor is None, "duplicate professor tag")
    self.professor = string.strip(body)
    
  def __parse_resourceroot(self, attributes, body):
    self.xml_assert(not attributes, "resourceroot tag should have no attributes")
    self.xml_assert(body, "resourceroot tag must have a body")
    self.xml_assert(self.resourceroot is None, "duplicate resourceroot tag")
    self.resourceroot = string.strip(body)
    
  def __parse_shortname(self, attributes, body):
    self.xml_assert(not attributes, "shortname tag should have no attributes")
    self.xml_assert(body, "shortname tag must have a body")
    self.xml_assert(self.shortname is None, "duplicate shortname tag")
    self.shortname = string.strip(body)
    
  def __parse_topics(self, attributes, body):
    self.xml_assert(not attributes, "topics tag should have no attributes")
    self.xml_assert(not self.topics, "duplicate topics tag")
    self.topics = string.split(body)
  
  def __parse_types(self, attributes, body):
    self.xml_assert(not attributes, "types tag should have no attributes")
    self.xml_assert(not self.types, "duplicate types tag")
    self.types = string.split(body)
    
  __parsers = {
    'author':__parse_author,
    'blurb':__parse_blurb,
    'classname':__parse_classname,
    'include':__parse_include,
    'problemroot':__parse_problemroot,
    'professor':__parse_professor,
    'resourceroot':__parse_resourceroot,
    'shortname':__parse_shortname,
    'topics':__parse_topics,
    'types':__parse_types}

  def parse_element(self, element):
    self.xml_assert(element.tag == 'configuration', 
        "Invalid config tag '{}'".format(element.tag))
    self.xml_assert(not element.attrib, 
        "configuration tag should not have attributes")
    for tag in element:
      self.xml_assert(tag.tag in BuildConfiguration.__parsers, 
          "Invalid tag '{}'".format(tag.tag))
      BuildConfiguration.__parsers[tag.tag](self, tag.attrib, tag.text)

  def validate(self):
    """Asserts that the BuildConfiguration satisfies the minimal requirements of being complete"""
    self.xml_assert(self.topics, "No topics")
    self.xml_assert(self.types, "No types")
    self.xml_assert(self.blurb is not None, "No blurb")
    self.xml_assert(self.problemroot is not None, "No problemroot")
    
__configuration = None

def __build_configuration():
  global __configuration
  
  if getenv('LATEXML_CONFIG') is None:
    raise ConfigurationError("No configuration file found in environment variable LATEXML_CONFIG")
  __configuration = BuildConfiguration(getenv('LATEXML_CONFIG'))
  try: config_tree = ET.parse(__configuration.filename)
  except IOError: 
    raise ConfigurationError("No such configuration file {}".format(getenv('LATEXML_CONFIG')))
  except ET.ParseError as p:
    raise ImproperXmlException("Could not parse XML: {}".format(p.strerror))
    
  __configuration.parse_tree(config_tree)
  __configuration.validate()

def get_configuration():
  if __configuration is None:
    __build_configuration()
  return __configuration
  
def get_blurb():
  return get_configuration().blurb
  
def get_classname():
  classname = get_configuration().classname
  if classname is None:
    return ""
  return classname
  
def get_default_author():
  if get_configuration().author is None:
    return getlogin()
  else:
    return get_configuration().author
  
def get_inclusions():
  return ''.join(get_configuration().include)
  
def get_problem_root():
  return get_configuration().problemroot
  
def get_professor():
  professor = get_configuration().professor
  if professor is None:
    return ""
  return professor
  
def get_resource_root():
  return get_configuration().resourceroot
  
def get_shortname():
  shortname = get_configuration().shortname
  if shortname is None:
    return ""
  return shortname
  
def get_topics():
  return copy(get_configuration().topics)
  
def get_types():
  return copy(get_configuration().types)