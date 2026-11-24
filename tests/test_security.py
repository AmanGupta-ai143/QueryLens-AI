import unittest

from services.security import verify_password


class SecurityTests(unittest.TestCase):
    def test_correct_password(self):
        self.assertTrue(verify_password("s3cret!", "s3cret!"))

    def test_wrong_password(self):
        self.assertFalse(verify_password("s3cret", "s3cret!"))
        self.assertFalse(verify_password("S3CRET!", "s3cret!"))

    def test_unset_or_empty_password_never_matches(self):
        for expected in (None, ""):
            self.assertFalse(verify_password("anything", expected))
            self.assertFalse(verify_password("", expected))

    def test_unicode_password(self):
        self.assertTrue(verify_password("pässwörd✓", "pässwörd✓"))


if __name__ == "__main__":
    unittest.main()
