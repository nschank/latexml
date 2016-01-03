import xml.etree.ElementTree as ET
from os import getenv

class ConfigurationError(Exception):
  pass

class AssignmentType:
  pass

class BuildConfiguration:
  pass

__configuration = None

def __build_configuration():
  if getenv('LATEXML_CONFIG') is None:
    raise ConfigurationError("No configuration file found in environment variable LATEXML_CONFIG")
  try: config_tree = ET.parse(getenv('LATEXML_CONFIG'))
  except IOError: 
    raise ConfigurationError("No such configuration file {}".format(getenv('LATEXML_CONFIG')))
  print config_tree.getroot().tag

def get_configuration():
  if __configuration is None:
    __build_configuration()
  return __configuration
  
print get_configuration()