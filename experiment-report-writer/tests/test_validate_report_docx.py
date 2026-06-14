import importlib.util
import pathlib
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_report_docx.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_report_docx", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_docx(path, body_xml):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        zf.writestr("word/document.xml", body_xml)


def paragraph(text):
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def document_xml(*paragraphs):
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    %s
  </w:body>
</w:document>""" % "\n".join(paragraphs)


class ValidateReportDocxTest(unittest.TestCase):
    def test_valid_report_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "valid.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    paragraph("Figure 1. Clustering result"),
                ),
            )

            result = module.validate_docx(docx)

        self.assertTrue(result.ok)
        self.assertEqual(result.errors, [])

    def test_missing_required_section_fails(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "missing.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                ),
            )

            result = module.validate_docx(docx)

        self.assertFalse(result.ok)
        self.assertIn("Missing section: Discussion and Conclusions", result.errors)

    def test_raw_latex_markers_fail(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docx = pathlib.Path(tmp) / "latex.docx"
            make_docx(
                docx,
                document_xml(
                    paragraph("Experimental Purposes and Requirements"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("4. Discussion and Conclusions"),
                    paragraph("The objective is $J = \\sum_i x_i$."),
                ),
            )

            result = module.validate_docx(docx)

        self.assertFalse(result.ok)
        self.assertIn("Raw LaTeX/math marker found: $", result.errors)


if __name__ == "__main__":
    unittest.main()
