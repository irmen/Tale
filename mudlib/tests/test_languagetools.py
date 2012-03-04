import unittest
import mudlib.languagetools


class TestLanguagetools(unittest.TestCase):
    def testA(self):
        self.assertEqual("a house", mudlib.languagetools.a("house"))
        self.assertEqual("a house", mudlib.languagetools.a("a house"))
        self.assertEqual("a House", mudlib.languagetools.a("House"))
        self.assertEqual("an egg", mudlib.languagetools.a("egg"))
        self.assertEqual("an egg", mudlib.languagetools.a("an egg"))
        self.assertEqual("a university", mudlib.languagetools.a("university"))
        self.assertEqual("a university magazine", mudlib.languagetools.a("university magazine"))
        self.assertEqual("an unindent", mudlib.languagetools.a("unindent"))
        self.assertEqual("a user", mudlib.languagetools.a("user"))
        self.assertEqual("a history", mudlib.languagetools.a("history"))
        self.assertEqual("an hour", mudlib.languagetools.a("hour"))

    def testAexceptions(self):
        self.assertEqual("an unicycle", mudlib.languagetools.a("unicycle"), "unicycle -> an, without regged exception")
        mudlib.languagetools.reg_a_exceptions({"unicycle": "a"})
        self.assertEqual("a unicycle", mudlib.languagetools.a("unicycle"), "unicycle -> a, with regged exception")
        self.assertEqual("a unicycle wheel", mudlib.languagetools.a("unicycle wheel"))

    def testFullstop(self):
        self.assertEqual("a.", mudlib.languagetools.fullstop("a"))
        self.assertEqual("a.", mudlib.languagetools.fullstop("a "))
        self.assertEqual("a.", mudlib.languagetools.fullstop("a."))
        self.assertEqual("a?", mudlib.languagetools.fullstop("a?"))
        self.assertEqual("a!", mudlib.languagetools.fullstop("a!"))
        self.assertEqual("a;", mudlib.languagetools.fullstop("a", punct=";"))

    def testJoin(self):
        self.assertEqual("", mudlib.languagetools.join([]))
        self.assertEqual("a", mudlib.languagetools.join(["a"]))
        self.assertEqual("a and b", mudlib.languagetools.join(["a", "b"]))
        self.assertEqual("a, b, and c", mudlib.languagetools.join(["a", "b", "c"]))
        self.assertEqual("a, b, or c", mudlib.languagetools.join(["a", "b", "c"], conj="or"))
        self.assertEqual("c, b, or a", mudlib.languagetools.join(["c", "b", "a"], conj="or"))

    def testAdverbs(self):
        self.assertTrue(len(mudlib.languagetools.ADVERB_LIST) > 0)
        self.assertTrue("noisily" in mudlib.languagetools.ADVERBS)
        self.assertFalse("zzzzzzzzzz" in mudlib.languagetools.ADVERBS)
        self.assertEqual(['nobly', 'nocturnally', 'noiselessly', 'noisily', 'nominally'], mudlib.languagetools.adverb_by_prefix("no", 5))
        self.assertEqual(['nobly'], mudlib.languagetools.adverb_by_prefix("no", 1))
        self.assertEqual(["abjectly"], mudlib.languagetools.adverb_by_prefix("a", 1))
        self.assertEqual([], mudlib.languagetools.adverb_by_prefix("zzzzzzzzzz"))

    def testPossessive(self):
        self.assertEqual("", mudlib.languagetools.possessive_letter(""))
        self.assertEqual("s", mudlib.languagetools.possessive_letter("julie"))
        self.assertEqual("'", mudlib.languagetools.possessive_letter("tess"))
        self.assertEqual("", mudlib.languagetools.possessive_letter("your own"))
        self.assertEqual("", mudlib.languagetools.possessive_letter(""))
        self.assertEqual("julies", mudlib.languagetools.possessive("julie"))
        self.assertEqual("tess'", mudlib.languagetools.possessive("tess"))
        self.assertEqual("your own", mudlib.languagetools.possessive("your own"))

    def testCapital(self):
        self.assertEqual("", mudlib.languagetools.capital(""))
        self.assertEqual("X", mudlib.languagetools.capital("x"))
        self.assertEqual("Xyz AbC", mudlib.languagetools.capital("xyz AbC"))

    def testSplit(self):
        self.assertEqual([], mudlib.languagetools.split(""))
        self.assertEqual(["a"], mudlib.languagetools.split("a"))
        self.assertEqual(["a","b","c"], mudlib.languagetools.split("a b c"))
        self.assertEqual(["a","b","c"], mudlib.languagetools.split(" a   b  c    "))
        self.assertEqual(["a","b c d","e"], mudlib.languagetools.split("a 'b c d' e"))
        self.assertEqual(["a","b c d","e"], mudlib.languagetools.split("a  '  b c d '   e"))
        self.assertEqual(["a","b c d","e","f g","h"], mudlib.languagetools.split("a 'b c d' e \"f g   \" h"))
        self.assertEqual(["a","b c \"hi!\" d","e"], mudlib.languagetools.split("a  '  b c \"hi!\" d '   e"))
        self.assertEqual(["a", "'b"], mudlib.languagetools.split("a 'b"))
        self.assertEqual(["a", "\"b"], mudlib.languagetools.split("a \"b"))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
