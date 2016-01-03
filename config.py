import xml.etree.ElementTree as ET
from os import getenv
from parseable import XmlParseable, ImproperXmlException
import string

class ConfigurationError(Exception):
  pass

class AssignmentType(XmlParseable):
  pass

class BuildConfiguration(XmlParseable):
  def __init__(self, filename=None):
    self.filename = filename
    self.topics = []
    self.types = []
    
  def __parse_topics(self, attributes, body):
    self.xml_assert(not attributes, "topics tag should have no attributes")
    self.xml_assert(not self.topics, "duplicate topics tag")
    self.topics = frozenset(string.split(body))
  
  def __parse_types(self, attributes, body):
    self.xml_assert(not attributes, "types tag should have no attributes")
    self.xml_assert(not self.types, "duplicate types tag")
    self.types = frozenset(string.split(body))
    
  __parsers = {'topics':__parse_topics,
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
  
def get_topics():
  return get_configuration().topics
  
def get_types():
  return get_configuration().types