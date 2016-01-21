import xml.etree.ElementTree as ET
import unittest
from config import BuildConfiguration
from parseable import ImproperXmlException
from problem import Version, ImproperXmlException, Problem, Document
from build import satisfies
import os
import string

test_filename = "test_filename"

class ConfigurationTest(unittest.TestCase):
  def test_invalid(self):
    for file in os.listdir("test/config_invalid"):
      if file.endswith(".xml"):
        tree = ET.parse("test/config_invalid/" + file)
        config = BuildConfiguration(file)
        root = tree.getroot()
        if root.tag != 'test' or len(root) != 2 or root[0].tag != 'error':
          print "Warning: Invalid config_invalid test {}".format(file)
          continue
        
        with self.assertRaisesRegexp(ImproperXmlException, root[0].text):
          config.parse_element(root[1])
          config.validate()
          
class DocumentTest(unittest.TestCase):
  def test_invalid(self):
    for file in os.listdir("test/document_invalid"):
      if file.endswith(".xml"):
        tree = ET.parse("test/document_invalid/" + file)
        document = Document(file)
        root = tree.getroot()
        if root.tag != 'test' or len(root) != 2 or root[0].tag != 'error':
          print "Warning: Invalid document_invalid test {}".format(file)
          continue
        
        with self.assertRaisesRegexp(ImproperXmlException, root[0].text):
          document.parse_element(root[1])
          document.validate()
          
  def test_version(self):
    root = ET.Element("assignment")
    
    year = ET.SubElement(root, "year")
    year.text = "2016"
    due = ET.SubElement(root, "due")
    due.text = "Never"
    name = ET.SubElement(root, "name")
    name.text = "Midterm 1"
    
    problem = ET.SubElement(root, "problem")
    problem.text = "test/valid1.xml"
    
    document1 = Document(test_filename)
    document1.parse_element(root)
    document1.validate()
    
    problem.set("version", "0")
    document2 = Document(test_filename)
    document2.parse_element(root)
    document2.validate()
    
    self.assertNotEqual(document1.versions[0].body, 
        document2.versions[0].body)
  

class ProblemTest(unittest.TestCase):
  def test_invalid(self):
    for file in os.listdir("test/problem_invalid"):
      if file.endswith(".xml"):
        tree = ET.parse("test/problem_invalid/" + file)
        problem = Problem(file)
        root = tree.getroot()
        if root.tag != 'test' or len(root) != 2 or root[0].tag != 'error':
          print "Warning: Invalid problem_invalid test {}".format(file)
          continue
        
        with self.assertRaisesRegexp(ImproperXmlException, root[0].text):
          problem.parse_element(root[1], validate_versions=True)
    for file in os.listdir("test/version_invalid"):
      if file.endswith(".xml"):
        tree = ET.parse("test/version_invalid/" + file)
        problem = Problem(file)
        version_root = tree.getroot()
        if (version_root.tag != 'test' or len(version_root) != 2 
            or version_root[0].tag != 'error'):
          print "Warning: Invalid version_invalid test {}".format(file)
          continue
        
        with self.assertRaisesRegexp(ImproperXmlException, 
            version_root[0].text):
          root = ET.Element("problem")
          root.append(version_root[1])
          problem.parse_element(root, validate_versions=True)
        
          
  def test_newest(self):
    problem = Problem(test_filename)
    
    versions = [Version(test_filename, 0), Version(test_filename, 1), 
        Version(test_filename, 2), Version(test_filename, 3)]
    problem.versions[0] = versions[0]
    self.assertEqual(problem.newest_version(), versions[0])
    problem.versions[1] = versions[1]
    self.assertEqual(problem.newest_version(), versions[1])
    problem.versions[2] = versions[2]
    self.assertEqual(problem.newest_version(), versions[2])
    problem.versions[3] = versions[3]
    self.assertEqual(problem.newest_version(), versions[3])
    del problem.versions[3]
    self.assertEqual(problem.newest_version(), versions[2])
    
  def test_next_id_direct(self):
    problem = Problem(test_filename)
    
    versions = [Version(test_filename, 0), Version(test_filename, 1), 
        Version(test_filename, 2), Version(test_filename, 3)]
    problem.versions[0] = versions[0]
    self.assertEqual(problem.next_id(), 1)
    problem.versions[1] = versions[1]
    self.assertEqual(problem.next_id(), 2)
    problem.versions[2] = versions[2]
    self.assertEqual(problem.next_id(), 3)
    problem.versions[3] = versions[3]
    self.assertEqual(problem.next_id(), 4)
    del problem.versions[3]
    self.assertEqual(problem.next_id(), 3)
    


class VersionTest(unittest.TestCase):
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
    
  def test_authors(self):
    for file in os.listdir("test/version_valid"):
      if file.startswith("version_valid_author"):
        tree = ET.parse("test/version_valid/" + file)
        version = Version(file)
        root = tree.getroot()
        
        version.parse_element(root)
        authors = []
        for child in root:
          if child.tag in ['author', 'authors']:
            authors = authors + string.split(child.text)
        self.assertEqual(authors, version.authors)
    
  def test_invalid(self):
    for file in os.listdir("test/version_invalid"):
      if file.endswith(".xml"):
        tree = ET.parse("test/version_invalid/" + file)
        version = Version(file)
        root = tree.getroot()
        if root.tag != 'test' or len(root) != 2 or root[0].tag != 'error':
          print "Warning: Invalid version_invalid test {}".format(file)
          continue
        
        with self.assertRaisesRegexp(ImproperXmlException, root[0].text):
          version.parse_element(root[1])
          version.validate()
        
  def test_params(self):
    for file in os.listdir("test/version_valid"):
      if file.startswith("version_valid_param"):
        tree = ET.parse("test/version_valid/" + file)
        version = Version(file)
        root = tree.getroot()
        
        version.parse_element(root)
        params = dict()
        for child in root:
          if child.tag in ['param', 'params']:
            params[child.attrib['name']] = child.text
        self.assertEqual(params, version.params)
    
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
    for file in os.listdir("test/version_valid"):
      if file.endswith(".xml"):
        tree = ET.parse("test/version_valid/" + file)
        version = Version(file)
        version.parse_tree(tree)
        
        version2 = Version(file)
        version2.parse_element(version.to_element())
        
        self.versions_equal(version, version2)
    
  def test_topics(self):
    for file in os.listdir("test/version_valid"):
      if file.startswith("version_valid_topic"):
        tree = ET.parse("test/version_valid/" + file)
        version = Version(file)
        root = tree.getroot()
        
        version.parse_element(root)
        topics = []
        for child in root:
          if child.tag in ['topic', 'topics']:
            topics = topics + string.split(child.text)
        self.assertEqual(topics, version.topics)
        
  def test_types(self):
    for file in os.listdir("test/version_valid"):
      if file.startswith("version_valid_type"):
        tree = ET.parse("test/version_valid/" + file)
        version = Version(file)
        root = tree.getroot()
        
        version.parse_element(root)
        types = []
        for child in root:
          if child.tag in ['type', 'types']:
            types = types + string.split(child.text)
        self.assertEqual(types, version.types)
        
  def test_validate(self):
    for file in os.listdir("test/version_valid"):
      if file.startswith("version_valid"):
        tree = ET.parse("test/version_valid/" + file)
        version = Version(file)
        version.parse_tree(tree)
        version.validate()
        
class DummyObject():
  def __getattr__(self, name):
    return False
        
class BuildPredicateTest(unittest.TestCase):
  def test_empty(self):
    version = DummyObject()
    settings = DummyObject()
    
    self.assertTrue(satisfies(version, settings))
    
  def test_allowed_topics(self):
    version = DummyObject()
    settings = DummyObject()
    version.topics = ['set_theory', 'number_theory']
    
    settings.allowed_topics = ['set_theory', 'graph_theory', 'number_theory']
    self.assertTrue(satisfies(version, settings))
    
    settings.allowed_topics = ['set_theory']
    self.assertFalse(satisfies(version, settings))
    
  def test_required_topics(self):
    version = DummyObject()
    settings = DummyObject()
    version.topics = ['set_theory']
    
    # Matches exactly
    settings.required_topics = ['set_theory']
    self.assertTrue(satisfies(version, settings))
    
    # One required topic, but not the other
    settings.required_topics = ['set_theory', 'graph_theory']
    self.assertTrue(satisfies(version, settings))
    
    # One required topic matches, one real topic not present
    version.topics = ['set_theory', 'number_theory']
    self.assertTrue(satisfies(version, settings))
    
    version.topics = ['number_theory']
    self.assertFalse(satisfies(version, settings))
    
    
    
if __name__ == '__main__':
  unittest.main()