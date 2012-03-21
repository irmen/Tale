"""
Unittests for languagetools

Snakepit mud driver and mudlib - Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import mudlib.lang


class TestLanguagetools(unittest.TestCase):
    def testA(self):
        self.assertEqual("a house", mudlib.lang.a("house"))
        self.assertEqual("a house", mudlib.lang.a("a house"))
        self.assertEqual("a House", mudlib.lang.a("House"))
        self.assertEqual("an egg", mudlib.lang.a("egg"))
        self.assertEqual("an egg", mudlib.lang.a("an egg"))
        self.assertEqual("a university", mudlib.lang.a("university"))
        self.assertEqual("a university magazine", mudlib.lang.a("university magazine"))
        self.assertEqual("an unindent", mudlib.lang.a("unindent"))
        self.assertEqual("a user", mudlib.lang.a("user"))
        self.assertEqual("a history", mudlib.lang.a("history"))
        self.assertEqual("an hour", mudlib.lang.a("hour"))

    def testAexceptions(self):
        self.assertEqual("an unicycle", mudlib.lang.a("unicycle"), "unicycle -> an, without regged exception")
        mudlib.lang.reg_a_exceptions({"unicycle": "a"})
        self.assertEqual("a unicycle", mudlib.lang.a("unicycle"), "unicycle -> a, with regged exception")
        self.assertEqual("a unicycle wheel", mudlib.lang.a("unicycle wheel"))

    def testFullstop(self):
        self.assertEqual("a.", mudlib.lang.fullstop("a"))
        self.assertEqual("a.", mudlib.lang.fullstop("a "))
        self.assertEqual("a.", mudlib.lang.fullstop("a."))
        self.assertEqual("a?", mudlib.lang.fullstop("a?"))
        self.assertEqual("a!", mudlib.lang.fullstop("a!"))
        self.assertEqual("a;", mudlib.lang.fullstop("a", punct=";"))

    def testJoin(self):
        self.assertEqual("", mudlib.lang.join([]))
        self.assertEqual("", mudlib.lang.join(x for x in []))
        self.assertEqual("a", mudlib.lang.join(["a"]))
        self.assertEqual("a and b", mudlib.lang.join(["a", "b"]))
        self.assertEqual("a and b", mudlib.lang.join(x for x in ["a", "b"]))
        self.assertEqual("a, b, and c", mudlib.lang.join(["a", "b", "c"]))
        self.assertEqual("a, b, or c", mudlib.lang.join(["a", "b", "c"], conj="or"))
        self.assertEqual("c, b, or a", mudlib.lang.join(["c", "b", "a"], conj="or"))

    def testAdverbs(self):
        self.assertTrue(len(mudlib.lang.ADVERB_LIST) > 0)
        self.assertTrue("noisily" in mudlib.lang.ADVERBS)
        self.assertFalse("zzzzzzzzzz" in mudlib.lang.ADVERBS)
        self.assertEqual(['nobly', 'nocturnally', 'noiselessly', 'noisily', 'nominally'], mudlib.lang.adverb_by_prefix("no", 5))
        self.assertEqual(['nobly'], mudlib.lang.adverb_by_prefix("no", 1))
        self.assertEqual(["abjectly"], mudlib.lang.adverb_by_prefix("a", 1))
        self.assertEqual(["zonally","zoologically"], mudlib.lang.adverb_by_prefix("zo"))
        self.assertEqual(["zoologically"], mudlib.lang.adverb_by_prefix("zoo"))
        self.assertEqual([], mudlib.lang.adverb_by_prefix("zzzzzzzzzz"))

    def testPossessive(self):
        self.assertEqual("", mudlib.lang.possessive_letter(""))
        self.assertEqual("'s", mudlib.lang.possessive_letter("julie"))
        self.assertEqual("'s", mudlib.lang.possessive_letter("tess"))
        self.assertEqual("", mudlib.lang.possessive_letter("your own"))
        self.assertEqual("", mudlib.lang.possessive_letter(""))
        self.assertEqual("julie's", mudlib.lang.possessive("julie"))
        self.assertEqual("tess's", mudlib.lang.possessive("tess"))
        self.assertEqual("your own", mudlib.lang.possessive("your own"))

    def testCapital(self):
        self.assertEqual("", mudlib.lang.capital(""))
        self.assertEqual("X", mudlib.lang.capital("x"))
        self.assertEqual("Xyz AbC", mudlib.lang.capital("xyz AbC"))

    def testSplit(self):
        self.assertEqual([], mudlib.lang.split(""))
        self.assertEqual(["a"], mudlib.lang.split("a"))
        self.assertEqual(["a", "b", "c"], mudlib.lang.split("a b c"))
        self.assertEqual(["a", "b", "c"], mudlib.lang.split(" a   b  c    "))
        self.assertEqual(["a", "b c d", "e"], mudlib.lang.split("a 'b c d' e"))
        self.assertEqual(["a", "b c d", "e"], mudlib.lang.split("a  '  b c d '   e"))
        self.assertEqual(["a", "b c d", "e", "f g", "h"], mudlib.lang.split("a 'b c d' e \"f g   \" h"))
        self.assertEqual(["a", "b c \"hi!\" d", "e"], mudlib.lang.split("a  '  b c \"hi!\" d '   e"))
        self.assertEqual(["a", "'b"], mudlib.lang.split("a 'b"))
        self.assertEqual(["a", "\"b"], mudlib.lang.split("a \"b"))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
