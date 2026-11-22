import ast
import json
import plistlib
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
class SourceTests(unittest.TestCase):
    def test_python_syntax(self):
        compile((ROOT / "src/app.py").read_text(encoding="utf-8"), "app.py", "exec")
    def test_languages(self):
        data = json.loads((ROOT / "src/languages.json").read_text(encoding="utf-8"))
        self.assertIn("it", data)
        self.assertIn("en", data)
    def test_bundle_version(self):
        data = plistlib.loads((ROOT / "macos/Info.plist").read_bytes())
        self.assertEqual(data["CFBundleShortVersionString"], "3.14.16")
if __name__ == "__main__":
    unittest.main()
