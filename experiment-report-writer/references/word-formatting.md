# Word Formatting Rules

## Template Preservation

- Treat the template as the source of truth.
- Copy the template and edit the copy.
- Preserve the cover page unless the user explicitly asks to fill or change cover fields.
- Keep all report body content inside the original report body area.
- Avoid rebuilding the whole document from scratch because this often destroys school template layout.
- Do not recreate the school cover with ordinary paragraphs, spaces, or a blank DOCX. This loses the original form border/page-frame behavior in Word/WPS.
- For legacy `.doc` templates, prepare a high-fidelity master `.docx` with LibreOffice. Avoid `textutil` for final template preparation because it may drop old Word/WPS form borders, page frames, and compatibility layout.
- Use a copy of the LibreOffice-prepared master as the final document base. Insert or replace body content inside that copy.
- Compare the generated report against a converted template with `scripts/report_quality_harness.py --template` when possible.
- If LibreOffice conversion aborts on macOS due to app quarantine/signing, do not fall back to `textutil` for final output. Ask the user to fix LibreOffice permissions/quarantine or provide a manually saved `.docx` master from Word/WPS.
- If the rendered master already lacks the outer report frame, stop and ask for a manually saved `.docx` master from Word/WPS before generating the report.

## Typography

- Body text: Times New Roman, 10.5 pt / Chinese size 5.
- Headings and subheadings: bold.
- Use numbered headings such as `2.1`, `2.2`, `3.1`, `3.1.1`.
- Keep spacing compact and consistent. Remove strange large spaces and empty paragraphs.

## Formulas

- Important formulas must be drafted as LaTeX fragments first, then converted into editable Word equations (`m:oMath` / `m:oMathPara`), not screenshots and not plain text.
- Plain strings such as `exp(w_k^T x+b_k)`, `argmax_y`, `sum_i`, `product_i`, and `||x-y||` are not acceptable for important formulas.
- Visible underscores, carets, raw braces, slash fractions, and LaTeX delimiters mean the formula conversion failed.
- Use `scripts/latex_to_docx_math.py` for isolated formula conversion checks. When inserting formulas into the final report, preserve the resulting Office Math XML rather than copying the visible text.
- Do not leave visible raw LaTeX markers such as `$`, `\(`, `\)`, `\[`, `\]`, or unmatched braces.
- Center important display formulas.
- Put equation numbers at the far right, for example `(1)`, `(2)`.
- Inline formulas are acceptable only when they render cleanly as normal Word equation text.

## Figures

- Insert visualization outputs near the discussion that refers to them.
- Use a clear figure caption below the image, for example `Figure 1. Scatter plots of the five datasets`.
- Keep each figure and its caption together when possible.
- Avoid oversized images that force large blank areas or overflow outside margins.

## Tables

- Use real Word tables or spreadsheet-derived tables.
- Put table captions above tables, for example `Table 1. Dataset descriptions`.
- Avoid plain-text tables made with spaces.
- Set table width, column widths, padding, and wrapping explicitly when generating OOXML.
- Check that table text is not clipped or pinned to borders.

## Final QA Checklist

- Cover page formatting unchanged.
- Required four report sections present.
- Body content is English.
- Headings are numbered and bold.
- Body font is consistent.
- No raw LaTeX syntax visible.
- Editable Word equation objects are present when the report contains important formulas.
- Figures have lower captions.
- Tables have upper captions.
- No abnormal large blanks.
- Final `.docx` opens successfully.
- LibreOffice/Word-rendered preview confirms that the first page and outer report frame are still visible.
