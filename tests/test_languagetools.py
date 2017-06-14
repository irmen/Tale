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
        self.assertEqual("An egg", lang.a("An egg"))
        self.assertEqual("a university", lang.a("university"))
        self.assertEqual("a university magazine", lang.a("university magazine"))
        self.assertEqual("an unindent", lang.a("unindent"))
        self.assertEqual("a user", lang.a("user"))
        self.assertEqual("a history", lang.a("history"))
        self.assertEqual("an hour", lang.a("hour"))
        self.assertEqual("A user", lang.A("user"))
        self.assertEqual("An hour", lang.A("hour"))
        self.assertEqual("An egg", lang.A("An egg"))

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

    def testJoinMulti(self):
        self.assertEqual("two bikes", lang.join(["bike"] * 2))
        self.assertEqual("two bikes", lang.join(["a bike"] * 2))
        self.assertEqual("three bikes", lang.join(["a bike"] * 3))
        self.assertEqual("bike, bike, and bike", lang.join(["bike"] * 3, group_multi=False))
        self.assertEqual("twelve keys", lang.join(["key"] * 12))
        self.assertEqual("twelve keys", lang.join(["a key"] * 12))
        self.assertEqual("two keys and two bikes", lang.join(["key", "bike"] * 2))
        self.assertEqual("two bikes and two keys", lang.join(["bike", "key"] * 2))
        self.assertEqual("two bikes and two apples", lang.join(["a bike", "an apple"] * 2))
        self.assertEqual("two bikes, two keys, and two mice", lang.join(["bike", "key", "mouse"] * 2))
        self.assertEqual("two bikes, two apples, and two mice", lang.join(["a bike", "an apple", "the mouse"] * 2))
        self.assertEqual("two apples, bike, and two keys", lang.join(["apple", "apple", "bike", "key", "key"]))
        self.assertEqual("two apples, two keys, and bike", lang.join(["apple", "apple", "key", "bike", "key"]))
        self.assertEqual("two apples, two keys, and a bike", lang.join(["an apple", "an apple", "a key", "a bike", "a key"]))
        self.assertEqual("three apples, two keys, and someone", lang.join(["an apple", "an apple", "the key", "an apple", "someone", "the key"]))
        self.assertEqual("key, bike, key, and bike", lang.join(["key", "bike"] * 2, group_multi=False))

    def testAdverbs(self):
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

    def testNumberSpell(self):
        self.assertEqual("zero", lang.spell_number(0))
        self.assertEqual("one", lang.spell_number(1))
        self.assertEqual("twenty", lang.spell_number(20))
        self.assertEqual("forty-five", lang.spell_number(45))
        self.assertEqual("seventy", lang.spell_number(70))
        self.assertEqual("minus forty-five", lang.spell_number(-45))
        self.assertEqual("ninety-nine", lang.spell_number(99))
        self.assertEqual("minus ninety-nine", lang.spell_number(-99))
        self.assertEqual("100", lang.spell_number(100))
        self.assertEqual("minus 100", lang.spell_number(-100))
        self.assertEqual("minus one", lang.spell_number(-1))
        self.assertEqual("minus twenty", lang.spell_number(-20))
        self.assertEqual("two and a half", lang.spell_number(2.5))
        self.assertEqual("two and a quarter", lang.spell_number(2.25))
        self.assertEqual("two and three quarters", lang.spell_number(2.75))
        self.assertEqual("minus two and three quarters", lang.spell_number(-2.75))
        self.assertEqual("ninety-nine and a half", lang.spell_number(99.5))
        self.assertEqual("minus ninety-nine and a half", lang.spell_number(-99.5))
        self.assertEqual("1.234", lang.spell_number(1.234))
        self.assertEqual("2.994", lang.spell_number(2.994))
        self.assertEqual("about three", lang.spell_number(2.996))
        self.assertEqual("about three", lang.spell_number(3.004))
        self.assertEqual("about three", lang.spell_number(3.004))
        self.assertEqual("about ninety-nine", lang.spell_number(99.004))
        self.assertEqual("about 100", lang.spell_number(99.996))
        self.assertEqual("about minus three", lang.spell_number(-2.996))
        self.assertEqual("about minus three", lang.spell_number(-3.004))
        self.assertEqual("about minus ninety-nine", lang.spell_number(-99.004))
        self.assertEqual("-3.006", lang.spell_number(-3.006))

    def test_ordinal(self):
        self.assertEqual("0th", lang.ordinal(0))
        self.assertEqual("1st", lang.ordinal(1))
        self.assertEqual("1st", lang.ordinal(1.4))
        self.assertEqual("2nd", lang.ordinal(2))
        self.assertEqual("3rd", lang.ordinal(3))
        self.assertEqual("4th", lang.ordinal(4))
        self.assertEqual("-2nd", lang.ordinal(-2))
        self.assertEqual("10th", lang.ordinal(10))
        self.assertEqual("11th", lang.ordinal(11))
        self.assertEqual("12th", lang.ordinal(12))
        self.assertEqual("13th", lang.ordinal(13))
        self.assertEqual("14th", lang.ordinal(14))
        self.assertEqual("20th", lang.ordinal(20))
        self.assertEqual("21st", lang.ordinal(21))
        self.assertEqual("99th", lang.ordinal(99))
        self.assertEqual("100th", lang.ordinal(100))
        self.assertEqual("101st", lang.ordinal(101))
        self.assertEqual("102nd", lang.ordinal(102))
        self.assertEqual("110th", lang.ordinal(110))
        self.assertEqual("111th", lang.ordinal(111))
        self.assertEqual("123rd", lang.ordinal(123))

    def test_spell_ordinal(self):
        self.assertEqual("zeroth", lang.spell_ordinal(0))
        self.assertEqual("first", lang.spell_ordinal(1))
        self.assertEqual("first", lang.spell_ordinal(1.4))
        self.assertEqual("second", lang.spell_ordinal(2))
        self.assertEqual("third", lang.spell_ordinal(3))
        self.assertEqual("minus second", lang.spell_ordinal(-2))
        self.assertEqual("tenth", lang.spell_ordinal(10))
        self.assertEqual("eleventh", lang.spell_ordinal(11))
        self.assertEqual("twentieth", lang.spell_ordinal(20))
        self.assertEqual("twenty-first", lang.spell_ordinal(21))
        self.assertEqual("seventieth", lang.spell_ordinal(70))
        self.assertEqual("seventy-sixth", lang.spell_ordinal(76))
        self.assertEqual("ninety-ninth", lang.spell_ordinal(99))
        self.assertEqual("100th", lang.spell_ordinal(100))
        self.assertEqual("101st", lang.spell_ordinal(101))

    def test_pluralize(self):
        self.assertEqual("cars", lang.pluralize("car"))
        self.assertEqual("cars", lang.pluralize("car", amount=0))
        self.assertEqual("car", lang.pluralize("car", amount=1))
        self.assertEqual("boxes", lang.pluralize("box"))
        self.assertEqual("bosses", lang.pluralize("boss"))
        self.assertEqual("bushes", lang.pluralize("bush"))
        self.assertEqual("churches", lang.pluralize("church"))
        self.assertEqual("gases", lang.pluralize("gas"))
        self.assertEqual("quizzes", lang.pluralize("quiz"))
        self.assertEqual("volcanoes", lang.pluralize("volcano"))
        self.assertEqual("photos", lang.pluralize("photo"))
        self.assertEqual("pianos", lang.pluralize("piano"))
        self.assertEqual("ladies", lang.pluralize("lady"))
        self.assertEqual("crises", lang.pluralize("crisis"))
        self.assertEqual("wolves", lang.pluralize("wolf"))
        self.assertEqual("ladies", lang.pluralize("lady"))
        self.assertEqual("keys", lang.pluralize("key"))
        self.assertEqual("homies", lang.pluralize("homy"))
        self.assertEqual("buoys", lang.pluralize("buoy"))

    def test_yesno(self):
        self.assertTrue(lang.yesno("y"))
        self.assertTrue(lang.yesno("Yes"))
        self.assertTrue(lang.yesno("SURE"))
        self.assertFalse(lang.yesno("n"))
        self.assertFalse(lang.yesno("NO"))
        self.assertFalse(lang.yesno("Hell No"))
        with self.assertRaises(ValueError):
            lang.yesno(None)
        with self.assertRaises(ValueError):
            lang.yesno("")
        with self.assertRaises(ValueError):
            lang.yesno("i dunno")

    def test_gender(self):
        self.assertEqual("f", lang.validate_gender("f"))
        self.assertEqual("m", lang.validate_gender("m"))
        self.assertEqual("n", lang.validate_gender("n"))
        self.assertEqual("f", lang.validate_gender("F"))
        self.assertEqual("female", lang.validate_gender("Female"))
        self.assertEqual("male", lang.validate_gender("MALE"))
        with self.assertRaises(ValueError):
            lang.validate_gender(None)
        with self.assertRaises(ValueError):
            lang.validate_gender("")
        with self.assertRaises(ValueError):
            lang.validate_gender("nope")

    def test_gender_mf(self):
        self.assertEqual("f", lang.validate_gender_mf("f"))
        self.assertEqual("m", lang.validate_gender_mf("m"))
        self.assertEqual("f", lang.validate_gender_mf("F"))
        self.assertEqual("female", lang.validate_gender_mf("Female"))
        self.assertEqual("male", lang.validate_gender_mf("MALE"))
        with self.assertRaises(ValueError):
            self.assertEqual("n", lang.validate_gender_mf("n"))
        with self.assertRaises(ValueError):
            lang.validate_gender_mf(None)
        with self.assertRaises(ValueError):
            lang.validate_gender_mf("")
        with self.assertRaises(ValueError):
            lang.validate_gender_mf("nope")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
