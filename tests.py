import xml.etree.ElementTree as ET
import unittest
from parse import Version, ImproperXmlException
import os

test_filename = "test_filename"

class TestVersion(unittest.TestCase):
  def versions_equal(self, version1, version2):
    self.assertEqual(version1.filename, version2.filename)
    self.assertEqual(version1.vid, version2.vid)
    self.assertEqual(version1.year, version2.year)
    self.assertEqual(version1.body, version2.body)
    self.assertEqual(version1.rubric, version2.rubric)
    self.assertEqual(version1.solution, version2.solution)
    
    self.assertEqual(len(version1.authors), len(version2.authors))
    self.assertEqual(len(version1.topics), len(version2.topics))
    self.assertEqual(len(version1.types), len(version2.types))
    self.assertEqual(len(version1.params), len(version2.params))
    self.assertEqual(len(version1.deps), len(version2.deps))
    
    self.assertEqual(version1.authors, version2.authors)
    self.assertEqual(version1.types, version2.types)
    self.assertEqual(version1.topics, version2.topics)
    self.assertEqual(version1.deps, version2.deps)
    self.assertEqual(version1.params, version2.params)
      
  def test_add_defaults(self):
    version = Version(test_filename)
    self.assertFalse(version.authors)
    self.assertTrue(version.year is None)
    version.add_defaults()
    self.assertTrue(len(version.authors) == 1)
    self.assertFalse(version.year is None)
    
  def test_invalid(self):
    for file in os.listdir("test"):
      if file.startswith("version_invalid"):
        tree = ET.parse("test/" + file)
        version = Version(file)
        root = tree.getroot()
        if root.tag != 'test' or len(root) != 2 or root[0].tag != 'error':
          print "Warning: Invalid version_invalid test {}".format(file)
          continue
        
        with self.assertRaisesRegexp(ImproperXmlException, root[0].text):
          version.parse_element(root[1])
          version.validate()
        
  def test_parse(self):
    for file in os.listdir("test"):
      if file.startswith("version_valid"):
        tree = ET.parse("test/" + file)
        version = Version(file)
        version.parse_tree(tree)
        version2 = Version(file)
        version2.parse_element(tree.getroot())
        self.versions_equal(version, version2)
    
  def test_pretty_print(self):
    version = Version(test_filename, 1)
    version.params['alpha'] = 'beta'
    version.topics = ['gamma']
    version.types = ['delta']
    version.body = 'epsilon'
    version.solution = 'zeta'
    version.rubric = 'theta'
    
    basic = version.pretty_print()
    sol = version.pretty_print(solution=True)
    rubric = version.pretty_print(rubric=True)
    meta = version.pretty_print(metadata=True)
    
    self.assertTrue(basic.find('alpha') != -1)
    self.assertTrue(sol.find('alpha') != -1)
    self.assertTrue(rubric.find('alpha') != -1)
    self.assertTrue(meta.find('alpha') != -1)
    
    self.assertTrue(basic.find('beta') != -1)
    self.assertTrue(sol.find('beta') != -1)
    self.assertTrue(rubric.find('beta') != -1)
    self.assertTrue(meta.find('beta') != -1)
    
    self.assertTrue(basic.find('gamma') == -1)
    self.assertTrue(sol.find('gamma') == -1)
    self.assertTrue(rubric.find('gamma') == -1)
    self.assertTrue(meta.find('gamma') != -1)
    
    self.assertTrue(basic.find('delta') == -1)
    self.assertTrue(sol.find('delta') == -1)
    self.assertTrue(rubric.find('delta') == -1)
    self.assertTrue(meta.find('delta') != -1)
    
    self.assertTrue(basic.find('epsilon') != -1)
    self.assertTrue(sol.find('epsilon') != -1)
    self.assertTrue(rubric.find('epsilon') != -1)
    self.assertTrue(meta.find('epsilon') != -1)
    
    self.assertTrue(basic.find('zeta') == -1)
    self.assertTrue(sol.find('zeta') != -1)
    self.assertTrue(rubric.find('zeta') == -1)
    self.assertTrue(meta.find('zeta') == -1)
    
    self.assertTrue(basic.find('theta') == -1)
    self.assertTrue(sol.find('theta') == -1)
    self.assertTrue(rubric.find('theta') != -1)
    self.assertTrue(meta.find('theta') == -1)

  def test_to_element(self):
    for file in os.listdir("test"):
      if file.startswith("version_valid"):
        tree = ET.parse("test/" + file)
        version = Version(file)
        version.parse_tree(tree)
        
        version2 = Version(file)
        version2.parse_element(version.to_element())
        
        self.versions_equal(version, version2)
    
  def test_validate(self):
    for file in os.listdir("test"):
      if file.startswith("version_valid"):
        tree = ET.parse("test/" + file)
        version = Version(file)
        version.parse_tree(tree)
        version.validate()
    
if __name__ == '__main__':
  unittest.main()