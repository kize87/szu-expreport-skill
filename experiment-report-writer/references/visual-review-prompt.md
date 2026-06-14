# Visual Review Prompt

Use this prompt when asking an AI-style reviewer to judge whether the report visuals are rich enough.

```text
Review the current experiment report with a visual-analysis lens.

Judge whether the report has enough charts, tables, heatmaps, confusion matrices, distributions, and comparison plots to explain the experiment without relying on prose alone.

For each figure or table:
- State what information it adds.
- Say whether it is necessary, redundant, or missing.
- Suggest one stronger chart if the current visual is weak.

Flag any section where a chart, table, or heatmap would communicate the point better than a paragraph.

Prefer more visuals when they improve interpretation, but reject decorative or repetitive plots.

Return a short revision list ordered by impact on report quality.
```
