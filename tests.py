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
    
if __name__ == '__main__':
  unittest.main()