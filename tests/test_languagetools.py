"""
Unittests for languagetools

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import tale.lang as lang


class TestLanguagetools(unittest.TestCase):
    def testA(self):
        self.assertEqual("a house", lang.a("house"))
        self.assertEqual("a house", lang.a("a house"))
        self.assertEqual("a House", lang.a("House"))
        self.assertEqual("an egg", lang.a("egg"))
        self.assertEqual("an egg", lang.a("an egg"))
        self.assertEqual("a university", lang.a("university"))
        self.assertEqual("a university magazine", lang.a("university magazine"))
        self.assertEqual("an unindent", lang.a("unindent"))
        self.assertEqual("a user", lang.a("user"))
        self.assertEqual("a history", lang.a("history"))
        self.assertEqual("an hour", lang.a("hour"))

    def testAexceptions(self):
        self.assertEqual("an unicycle", lang.a("unicycle"), "unicycle -> an, without regged exception")
        lang.reg_a_exceptions({"unicycle": "a"})
        self.assertEqual("a unicycle", lang.a("unicycle"), "unicycle -> a, with regged exception")
        self.assertEqual("a unicycle wheel", lang.a("unicycle wheel"))

    def testFullstop(self):
        self.assertEqual("a.", lang.fullstop("a"))
        self.assertEqual("a.", lang.fullstop("a "))
        self.assertEqual("a.", lang.fullstop("a."))
        self.assertEqual("a?", lang.fullstop("a?"))
        self.assertEqual("a!", lang.fullstop("a!"))
        self.assertEqual("a;", lang.fullstop("a", punct=";"))

    def testJoin(self):
        self.assertEqual("", lang.join([]))
        self.assertEqual("", lang.join(x for x in []))
        self.assertEqual("a", lang.join(["a"]))
        self.assertEqual("a and b", lang.join(["a", "b"]))
        self.assertEqual("a and b", lang.join(x for x in ["a", "b"]))
        self.assertEqual("a, b, and c", lang.join(["a", "b", "c"]))
        self.assertEqual("a, b, or c", lang.join(["a", "b", "c"], conj="or"))
        self.assertEqual("c, b, or a", lang.join(["c", "b", "a"], conj="or"))

    def testAdverbs(self):
        self.assertTrue(len(lang.ADVERB_LIST) > 0)
        self.assertTrue("noisily" in lang.ADVERBS)
        self.assertFalse("zzzzzzzzzz" in lang.ADVERBS)
        self.assertEqual(['nobly', 'nocturnally', 'noiselessly', 'noisily', 'nominally'], lang.adverb_by_prefix("no", 5))
        self.assertEqual(['nobly'], lang.adverb_by_prefix("no", 1))
        self.assertEqual(["abjectly"], lang.adverb_by_prefix("a", 1))
        self.assertEqual(["zonally", "zoologically"], lang.adverb_by_prefix("zo"))
        self.assertEqual(["zoologically"], lang.adverb_by_prefix("zoo"))
        self.assertEqual([], lang.adverb_by_prefix("zzzzzzzzzz"))

    def testPossessive(self):
        self.assertEqual("", lang.possessive_letter(""))
        self.assertEqual("'s", lang.possessive_letter("julie"))
        self.assertEqual("'s", lang.possessive_letter("tess"))
        self.assertEqual("", lang.possessive_letter("your own"))
        self.assertEqual("", lang.possessive_letter(""))
        self.assertEqual("julie's", lang.possessive("julie"))
        self.assertEqual("tess's", lang.possessive("tess"))
        self.assertEqual("your own", lang.possessive("your own"))

    def testCapital(self):
        self.assertEqual("", lang.capital(""))
        self.assertEqual("X", lang.capital("x"))
        self.assertEqual("Xyz AbC", lang.capital("xyz AbC"))

    def testSplit(self):
        self.assertEqual([], lang.split(""))
        self.assertEqual(["a"], lang.split("a"))
        self.assertEqual(["a", "b", "c"], lang.split("a b c"))
        self.assertEqual(["a", "b", "c"], lang.split(" a   b  c    "))
        self.assertEqual(["a", "b c d", "e"], lang.split("a 'b c d' e"))
        self.assertEqual(["a", "b c d", "e"], lang.split("a  '  b c d '   e"))
        self.assertEqual(["a", "b c d", "e", "f g", "h"], lang.split("a 'b c d' e \"f g   \" h"))
        self.assertEqual(["a", "b c \"hi!\" d", "e"], lang.split("a  '  b c \"hi!\" d '   e"))
        self.assertEqual(["a", "'b"], lang.split("a 'b"))
        self.assertEqual(["a", "\"b"], lang.split("a \"b"))

    def testFullverb(self):
        self.assertEqual("saying", lang.fullverb("say"))
        self.assertEqual("skiing", lang.fullverb("ski"))
        self.assertEqual("poking", lang.fullverb("poke"))
        self.assertEqual("polkaing", lang.fullverb("polka"))
        self.assertEqual("sniveling", lang.fullverb("snivel"))
        self.assertEqual("farting", lang.fullverb("fart"))
        self.assertEqual("trying", lang.fullverb("try"))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
