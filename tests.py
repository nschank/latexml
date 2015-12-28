import unittest
from parse import Version

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
    
    for elem in version1.authors:
      self.assertTrue(elem in version2.authors)
      
    for elem in version1.topics:
      self.assertTrue(elem in version2.topics)
      
    for elem in version1.types:
      self.assertTrue(elem in version2.types)
      
    for elem in version1.deps:
      self.assertTrue(elem in version2.deps)
      
    for name, value in version1.params.iteritems():
      self.assertTrue(name in version2.params)
      self.assertEqual(version2.params[name], value)

  def test_add_defaults(self):
    version = Version(test_filename)
    self.assertFalse(version.authors)
    self.assertTrue(version.year is None)
    version.add_defaults()
    self.assertTrue(len(version.authors) == 1)
    self.assertFalse(version.year is None)
    
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

    
if __name__ == '__main__':
  unittest.main()