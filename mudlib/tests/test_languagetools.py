import unittest
import mudlib.languagetools


class TestLanguagetools(unittest.TestCase):
    def testA(self):
        self.assertEqual("a house", mudlib.languagetools.a("house"))
        self.assertEqual("an egg", mudlib.languagetools.a("egg"))
        self.assertEqual("a university", mudlib.languagetools.a("university"))
        self.assertEqual("an unindent", mudlib.languagetools.a("unindent"))
        self.assertEqual("a history", mudlib.languagetools.a("history"))
    def testFullstop(self):
        self.assertEqual("a.", mudlib.languagetools.fullstop("a"))
        self.assertEqual("a.", mudlib.languagetools.fullstop("a "))
        self.assertEqual("a.", mudlib.languagetools.fullstop("a."))
        self.assertEqual("a?", mudlib.languagetools.fullstop("a?"))
        self.assertEqual("a!", mudlib.languagetools.fullstop("a!"))
        self.assertEqual("a;", mudlib.languagetools.fullstop("a", punct=";"))
    def testJoin(self):
        self.assertEqual("a", mudlib.languagetools.join(["a"]))
        self.assertEqual("a and b", mudlib.languagetools.join(["a", "b"]))
        self.assertEqual("a, b, and c", mudlib.languagetools.join(["a", "b", "c"]))
        self.assertEqual("a, b, or c", mudlib.languagetools.join(["a", "b", "c"], conj="or"))
        self.assertEqual("c, b, or a", mudlib.languagetools.join(["c", "b", "a"], conj="or"))
    def testAdverbs(self):
        self.assertTrue(len(mudlib.languagetools.ADVERB_LIST)>0)
        self.assertTrue("noisily" in mudlib.languagetools.ADVERBS)
        self.assertFalse("zzzzzzzzzz" in mudlib.languagetools.ADVERBS)
        self.assertEqual(['nobly', 'nocturnally', 'noiselessly', 'noisily', 'nominally'], mudlib.languagetools.adverb_by_prefix("no", 5))
        self.assertEqual(['nobly'], mudlib.languagetools.adverb_by_prefix("no", 1))
        self.assertEqual(["acapella"], mudlib.languagetools.adverb_by_prefix("a",1))
        self.assertEqual([], mudlib.languagetools.adverb_by_prefix("zzzzzzzzzz"))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()



