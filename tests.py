import unittest
from parse import Version

test_filename = "test_filename"

class TestVersion(unittest.TestCase):
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