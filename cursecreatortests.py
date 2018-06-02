import unittest
import mock
import Tkinter
from cursecreator import Application

class TestNPCCreator(unittest.TestCase):
	def setUp(self):
		root = Tkinter.Tk()
		self.app = Application(root)

	def test_attribute_fixer(self):
		self.assertTrue(self.app.attribute_fixer("health", 0))
		self.assertFalse(self.app.attribute_fixer("banana", 0))

if __name__ == "__main__":
	unittest.main()