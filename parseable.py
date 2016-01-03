class ImproperXmlException(Exception):
  pass
  
class ParseNotImplementedException(Exception):
  pass
  
class XmlParseable:
  """
  An object which can be built or modified by providing it with a tree.
  It may also be returned back as a new tree, modified directly, or created without
  an initial tree.
  """
  
  def xml_assert(self, predicate, str):
    """Used internally: check that something is true about the structure of an XML tree"""
    if not predicate:
      raise ImproperXmlException("Error in {}: {}".format(self.filename, str))

  def __init__(self, filename=None):
    self.filename = filename
    
  def parse_element(self, element):
    """Should be overridden to use the information in a root element to overwrite any relevant data in this tree"""
    raise ParseNotImplementedException()
    
  def parse_tree(self, tree):
    """Should be overridden to use the information in a tree to overwrite any relevant data in this tree"""
    self.parse_element(tree.getroot())
    
    
  def to_element(self):
    """
    Should be overridden such that the tree returned, if re-parsed by another object, would be semantically
    identical to this object
    """
    raise ParseNotImplementedException()