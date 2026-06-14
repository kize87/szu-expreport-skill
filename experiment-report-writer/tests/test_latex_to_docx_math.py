import importlib.util
import pathlib
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "latex_to_docx_math.py"


def load_module():
    spec = importlib.util.spec_from_file_location("latex_to_docx_math", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LatexToDocxMathTest(unittest.TestCase):
    def test_wrap_latex(self):
        module = load_module()
        self.assertEqual(module.wrap_latex(r"x^2 + y^2 = z^2", True), "$$\nx^2 + y^2 = z^2\n$$\n")
        self.assertEqual(module.wrap_latex(r"a+b", False), "$a+b$\n")
        self.assertEqual(module.normalize_latex(r"\\frac{a}{b}"), r"\frac{a}{b}")

    def test_render_latex_to_docx_creates_office_math(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            output = pathlib.Path(tmp) / "formula.docx"
            module.render_latex_to_docx(r"\frac{a}{b} = c", output)
            self.assertTrue(output.exists())
            with zipfile.ZipFile(output) as zf:
                xml = zf.read("word/document.xml").decode("utf-8")
            self.assertTrue("<m:oMath" in xml or "<m:oMathPara" in xml)


if __name__ == "__main__":
    unittest.main()
