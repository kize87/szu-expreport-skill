---
name: experiment-report-writer
description: Use when the user asks to write, fill, generate, polish, or verify a university experiment report from Word templates, lab requirements, code, datasets, figures, formulas, or reference reports, especially for English reports based on Shenzhen University-style lab report templates.
---

# Experiment Report Writer

## Purpose

Generate polished English experiment reports from lab requirements, code, data, and a Word template while preserving the original report cover and form layout. Treat the template as the source of truth for page structure; copy and locally fill it instead of recreating the whole document.

## Required Skill Order

1. Load a Word document skill first (`docx` or `documents`) before reading or editing `.doc`/`.docx` files.
2. Use this skill to drive report-specific discovery, writing, formatting, and QA.
3. Use `references/report-structure.md` for section content rules.
4. Use `references/word-formatting.md` before editing formulas, figures, tables, or the final DOCX.
5. Use `references/visualization-strategy.md` when deciding whether to create a figure, table, metric plot, or profiling artifact.

## Inputs To Discover

Scan the working directory before asking the user questions. Identify:

- Template files: names containing `template`, `模板`, `实验报告模板`, `.doc`, or `.docx`.
- Completed reference reports: names containing student IDs, names, `实验`, or reports with substantial body text.
- Lab requirements: `.docx`, `.pdf`, `.md`, `.txt`, assignment docs, or task descriptions.
- Code and data: Python notebooks/scripts, source files, datasets, generated images, logs, CSV/XLSX outputs.

Ignore Word lock files beginning with `.~`.

## Workflow

1. **Read and convert safely**
   - Convert legacy `.doc` templates with LibreOffice using `scripts/prepare_master_template.sh`. Do not use `textutil` for final template preparation when form borders or page frames matter.
   - Do not overwrite the original template.
   - Extract text from requirements, reference reports, and relevant code comments.
   - Inspect the template structure before editing; preserve cover-page fields and layout.
   - If the template is a school form, start from a copied template document and edit that copy. Do not create a new blank document that imitates the cover page.
   - If LibreOffice conversion still loses the outer frame, stop and ask for a manually saved high-fidelity `.docx` master from Word/WPS.

2. **Understand the experiment**
   - Read the requirements and translate Chinese requirements into English.
   - Read code and infer the actual experiment flow, methods, parameters, outputs, and visualizations.
   - Run code when needed to produce missing figures or result tables, after handling environment and dependency constraints normally.
   - Reuse existing generated outputs when they are clearly current and match the code.
   - Prefer to collect a broad visual set first, then prune only redundant visuals after review.

3. **Draft the report**
   - Write all report body content in English.
   - Use the four-section structure in `references/report-structure.md`.
   - Use numbered subsections such as `2.1`, `2.2`, `3.1`, `3.1.1`.
   - Match a college student lab-report tone: clear, technically accurate, not over-polished or marketing-like.
   - Prefer depth over speed. For normal machine-learning reports, produce substantial method explanations, parameter reasoning, result interpretation, and limitations. Avoid one-paragraph algorithm summaries.
   - When formulas appear in the source analysis or report draft, keep them as LaTeX fragments in the drafting stage, then convert them into editable Word equations before finalizing the DOCX.

4. **Edit the Word template**
   - Copy the LibreOffice-prepared high-fidelity master `.docx` to a new output `.docx`.
   - Fill the report body inside the corresponding report area.
   - Keep the cover page unchanged except for fields the user explicitly wants filled.
   - Use Times New Roman, Chinese size 5 / 10.5 pt for body text unless the template requires otherwise.
   - Make headings and subheadings bold.
   - Preserve the original first-page and form-layout OOXML. Treat cover/template signature changes as a failed output unless the user explicitly requested a cover redesign.
   - Do not use `python-docx`, `docx-js`, or Pandoc to rebuild the whole report when a template is provided. Use deterministic OOXML edits against the copied master, or use those libraries only for helper fragments that are merged into the copied master.

5. **Insert formulas, figures, and tables**
   - Convert important formulas from LaTeX fragments into editable Word equations using Office Math (`m:oMath` / `m:oMathPara`). Keep LaTeX only as an intermediate drafting format.
   - Do not leave formulas as plain text such as `exp(w_k^T x+b_k)` when the formula is central to the method.
   - Do not leave `$`, `\(`, `\)`, raw braces from LaTeX, or uncompiled equation syntax in visible text.
   - Center important display formulas and put equation numbers at the far right.
   - Put figure captions below figures and table captions above tables.
   - Use real Word tables or embedded spreadsheet-derived tables for tabular data; avoid pasted plain-text tables.

6. **Quality gate**
   - Run `scripts/validate_report_docx.py` on the final `.docx`.
   - Run `scripts/report_quality_harness.py` on the final `.docx`. For Shenzhen University templates use `--require-szubox`; when a converted master `.docx` is available, pass it with `--template`; for multi-model ML reports set `--min-figures` to the expected visualization count.
   - For richer visual reports, also pass `--min-tables` and `--require-visual-analysis` when the report should include dense comparative analysis.
   - If LibreOffice/Word rendering is available, render pages and visually inspect every page for cover damage, content overflow, broken tables, figure placement, large blank gaps, and strange spacing.
   - If rendering is unavailable, state that only structural QA was completed.

## Helper Scripts

- `scripts/inspect_docx.py`: Extract text and basic OOXML structure from a `.docx`.
- `scripts/validate_report_docx.py`: Check required sections and common report formatting hazards.
- `scripts/report_quality_harness.py`: Check editable equations, minimum report depth, and optional cover/template signature preservation.
- `scripts/prepare_master_template.sh`: Convert a legacy `.doc` template through LibreOffice and optionally render preview artifacts.
- `scripts/latex_to_docx_math.py`: Convert LaTeX formula fragments to a DOCX containing editable Word math.
- `scripts/convert_doc_to_docx.sh`: Convert `.doc` to `.docx` with available local tools.

## Prompt Contract For Report Generation

When delegating or starting a report generation task, include these constraints verbatim:

```text
Use the provided Word template as the base document. Prepare a high-fidelity master DOCX with LibreOffice when the source is .doc. Copy that master and fill the copy; do not rebuild the cover page or simulate the template in a new document. Preserve the first page, outer report frame, and report form layout.

Write a deep English experiment report. Spend time reading the requirements, code, data outputs, and figures. The report should include detailed algorithm principles, parameter choices, formulas, experiment process, result interpretation, method comparison, limitations, and possible improvements.

Before each revision, create as many useful visualizations as possible and then prune only redundant ones. Use the visual-review note to justify whether each figure adds information that text alone would miss. Favor charts, heatmaps, and comparison plots over text-only descriptions whenever the data supports them.

Important formulas must be editable Word equations, not plain text or screenshots. Formula-like text such as exp(w_k^T x+b_k), argmax_y, sum_i, product_i, and ||x-y|| must be converted into Office Math equations when used as important formulas.

Draft formulas first in LaTeX if that makes the reasoning clearer, then convert them to Word equations before finalizing. Do not ship the LaTeX delimiters or visible symbol artifacts.

Run the skill QA scripts before delivery: validate_report_docx.py and report_quality_harness.py. For Shenzhen University templates, include --require-szubox. Render the final report with LibreOffice and inspect page images; if visual render QA is unavailable, say so explicitly.

If visualization coverage is weak, run a second pass: ask an AI-style reviewer to critique the current figure set, identify missing plots or comparisons, and prefer chart/table additions over extra prose.
```

## Stop Conditions

Ask the user only when a required preference cannot be discovered from files, such as the exact experiment date, student metadata, or whether to install missing runtime dependencies. Do not ask where files are until after scanning the working directory.
