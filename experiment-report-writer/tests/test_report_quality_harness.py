import importlib.util
import pathlib
import sys
import tempfile
import unittest
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_quality_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("report_quality_harness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_docx(path, document_xml):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
        zf.writestr("word/document.xml", document_xml)


def paragraph(text):
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def doc(*paragraphs, extra_ns="", body_extra=""):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" {extra_ns}>
  <w:body>
    {"".join(paragraphs)}
    {body_extra}
  </w:body>
</w:document>"""


class ReportQualityHarnessTest(unittest.TestCase):
    def test_plain_text_equations_are_rejected(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "plain_formula.docx"
            make_docx(
                path,
                doc(
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("P(y=k|x)= exp(w_k^T x+b_k) / sum_j exp(w_j^T x+b_j) (1)"),
                    paragraph("This paragraph " * 40),
                    paragraph("Another paragraph " * 40),
                    paragraph("More analysis " * 40),
                ),
            )
            result = module.audit_report(path)

        self.assertFalse(result.ok)
        self.assertIn("No editable Word equations detected", result.errors)
        self.assertTrue(any("plain-text formula" in item for item in result.errors))

    def test_deep_report_with_word_equation_passes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "deep.docx"
            equation = """
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath><m:r><m:t>J</m:t></m:r></m:oMath>
</m:oMathPara>
"""
            make_docx(
                path,
                doc(
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("Discussion " * 120),
                    paragraph("Method explanation " * 120),
                    paragraph("Process analysis " * 120),
                    paragraph("Result interpretation " * 120),
                    body_extra=equation,
                ),
            )
            result = module.audit_report(path, min_body_words=100)

        self.assertTrue(result.ok)

    def test_formula_artifacts_warn_when_equation_exists(self):
        # When the document already contains Office Math equations, leftover
        # plain-text formula-like substrings (such as "exp(...)" or "sum_j" in
        # prose) are demoted to a warning rather than a hard error — those
        # mentions are usually casual prose alongside the real equation.
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "artifact_formula.docx"
            equation = """
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath><m:r><m:t>J</m:t></m:r></m:oMath>
</m:oMathPara>
"""
            make_docx(
                path,
                doc(
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("softmax uses exp(w_k^T x+b_k) and sum_j exp(w_j^T x+b_j)."),
                    paragraph("Discussion " * 120),
                    body_extra=equation,
                ),
            )
            result = module.audit_report(path, min_body_words=100)

        self.assertTrue(result.ok, result.errors)
        self.assertTrue(
            any("Formula-like prose" in w for w in result.warnings),
            result.warnings,
        )

    def test_shallow_report_is_rejected(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "shallow.docx"
            equation = """
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath><m:r><m:t>J</m:t></m:r></m:oMath>
</m:oMathPara>
"""
            make_docx(
                path,
                doc(
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("Too short."),
                    body_extra=equation,
                ),
            )
            result = module.audit_report(path, min_body_words=100)

        self.assertFalse(result.ok)
        self.assertIn("Report body is too short for a deep experiment report", result.errors)

    def test_missing_template_footer_anchor_is_rejected_when_required(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "missing_footer.docx"
            equation = """
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath><m:r><m:t>J</m:t></m:r></m:oMath>
</m:oMathPara>
"""
            make_docx(
                path,
                doc(
                    paragraph("深 圳 大 学 实 验 报 告"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("Discussion " * 120),
                    body_extra=equation,
                ),
            )
            result = module.audit_report(path, min_body_words=100, require_szubox=True)

        self.assertFalse(result.ok)
        self.assertIn("Missing Shenzhen University report footer/review anchor", result.errors)

    def test_too_few_figures_are_rejected_for_multi_model_report(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "few_figures.docx"
            equation = """
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath><m:r><m:t>J</m:t></m:r></m:oMath>
</m:oMathPara>
"""
            make_docx(
                path,
                doc(
                    paragraph("深 圳 大 学 实 验 报 告"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("Figure 1. Class distribution."),
                    paragraph("深圳大学学生实验报告用纸"),
                    paragraph("Discussion " * 120),
                    body_extra=equation,
                ),
            )
            result = module.audit_report(path, min_body_words=100, min_figures=3, require_szubox=True)

        self.assertFalse(result.ok)
        self.assertIn("Too few figure captions for this experiment report", result.errors)

    def test_visual_analysis_requirements_are_enforced(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "weak_visuals.docx"
            equation = """
<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
  <m:oMath><m:r><m:t>J</m:t></m:r></m:oMath>
</m:oMathPara>
"""
            make_docx(
                path,
                doc(
                    paragraph("深 圳 大 学 实 验 报 告"),
                    paragraph("2. Algorithms or Models Used"),
                    paragraph("3. Experiment Contents and Process"),
                    paragraph("Figure 1. Class distribution."),
                    paragraph("Figure 2. Confusion matrix."),
                    paragraph("Figure 3. Performance comparison."),
                    paragraph("深圳大学学生实验报告用纸"),
                    paragraph("Discussion " * 120),
                    body_extra=equation,
                ),
            )
            result = module.audit_report(
                path,
                min_body_words=100,
                min_figures=3,
                min_tables=1,
                require_visual_analysis=True,
                require_szubox=True,
            )

        self.assertFalse(result.ok)
        self.assertIn("Too few table captions for this experiment report", result.errors)
        self.assertIn("Visual analysis language is too thin", result.errors)


if __name__ == "__main__":
    unittest.main()
