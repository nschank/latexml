import xml.etree.ElementTree as ET
from os import getenv
from parseable import XmlParseable, ImproperXmlException
import string

class ConfigurationError(Exception):
  pass

class BuildConfiguration(XmlParseable):
  def __init__(self, filename=None):
    self.filename = filename
    self.topics = []
    self.types = []
    self.blurb = None
    self.include = []
    self.problemroot = None
    
  def __parse_blurb(self, attributes, body):
    self.xml_assert(not attributes, "blurb tag should have no attributes")
    self.xml_assert(self.blurb is None, "duplicate blurb tag")
    self.blurb = body
    
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
    
  def __parse_topics(self, attributes, body):
    self.xml_assert(not attributes, "topics tag should have no attributes")
    self.xml_assert(not self.topics, "duplicate topics tag")
    self.topics = frozenset(string.split(body))
  
  def __parse_types(self, attributes, body):
    self.xml_assert(not attributes, "types tag should have no attributes")
    self.xml_assert(not self.types, "duplicate types tag")
    self.types = frozenset(string.split(body))
    
  __parsers = {
    'blurb':__parse_blurb,
    'include':__parse_include,
    'problemroot':__parse_problemroot,
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
  
def get_inclusions():
  return ''.join(get_configuration().include)
  
def get_problem_root():
  return get_configuration().problemroot
  
def get_topics():
  return get_configuration().topics
  
def get_types():
  return get_configuration().types