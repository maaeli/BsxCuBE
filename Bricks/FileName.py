"Attention: Test only works as opd29, not as blissadm!!!!"

import re
import unittest
from os.path import isdir
from os import access, R_OK,W_OK

allowedSymbols = "a-zA-Z0-9_-"
forbiddenSymbols = r"[^" + allowedSymbols + "]"

controlPattern = re.compile(forbiddenSymbols)

def testName(pattern,name):
    """Tests whether the name contains any symbols included in pattern; a hit implies that the name is invalid, and returns FALSE
    pattern: A regular expression
    name: A string
    """
    if pattern.search(name): 
        return False
    return True

def testPrefix(prefix):
    return testName(controlPattern,prefix)

def testValidDir(directory):
    if not isdir(directory):
        return False
    if not access(directory,R_OK):
        return False
    if not access(directory,W_OK):
        return False
    if not (directory.startswith("/data/bm29/inhouse") or directory.startswith("/data/visitor")):
        return False
    return True
    


def testDirectory(directory):
    if not testValidDir(directory):
        return False
    return testName(controlPattern,directory.replace("/",""))
    



class FileNameMethodsTest(unittest.TestCase):
    "This still needs good test for the directories..."
    def test_validPrefix(self):
        self.assertTrue(testPrefix("water_12-AX"))
        for symbol in " ?./\\!@*&":
            self.assertFalse(testPrefix(symbol))

    def test_validDicName(self):
        self.assertTrue(testName(controlPattern,"/ab/cd/ef".replace("/","")))
        for symbol in [" /", "/?", "/.", "/\\", "/!","/@","/*","/&"]:
            self.assertFalse(testName(controlPattern,symbol.replace("/",""))) 


    def test_validtestValidDir(self):
        self.assertTrue(testValidDir("/data/bm29/inhouse"))
        self.assertFalse(testValidDir("/users/opd29"))


if __name__ == '__main__':
    unittest.main()
