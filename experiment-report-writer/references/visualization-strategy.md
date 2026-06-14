# Visualization Strategy

## Principle

Prefer visual evidence whenever it clarifies data, model behavior, or experimental results. A strong machine-learning report should not only state metrics; it should show the dataset, preprocessing effects, model errors, comparisons, and interpretation.

## Minimum Visual Set For Classification Reports

Generate as many of these as the data supports:

- Target class distribution bar chart.
- Missing-value heatmap or missingness table.
- Numeric feature distributions grouped by target.
- Categorical feature frequency plots grouped by target for the most important categories.
- Correlation heatmap for numeric variables.
- Train/test split or preprocessing summary table.
- Confusion matrix for each classifier.
- Per-class precision/recall/F1 table.
- Overall metric comparison bar chart.
- ROC or precision-recall curves when the task and model probabilities support them.
- Feature importance, coefficient magnitude, permutation importance, or SHAP-style explanation when feasible.
- Error-analysis chart showing which classes or feature groups are most often misclassified.

For clustering reports, prefer scatterplots, cluster assignment plots, parameter-sensitivity plots, silhouette or internal metric comparisons, and side-by-side method comparisons.

## Optional Open-Source Accelerators

Use these only when installed or when dependency installation is acceptable:

- `ydata-profiling` / pandas-profiling: quick exploratory profile with distributions, correlations, missing values, and interactions.
- `Sweetviz`: useful for target analysis and train/test comparison reports.
- `AutoViz`: one-line automatic visualization generation for tabular datasets.
- `DataPrep.EDA`: quick EDA plots and correlation/missingness summaries.

Do not paste entire HTML reports into the Word report. Use them to decide which figures matter, then export or recreate selected clean figures with matplotlib, seaborn, plotly, or sklearn.

## Figure Quality Rules

- Every figure must answer a concrete question.
- Every figure needs 2-4 sentences of interpretation immediately after it.
- Avoid generic screenshots from profiling tools if a cleaner custom plot can be generated.
- Prefer consistent color palettes and readable labels.
- Use multi-panel figures when they make comparison easier, especially confusion matrices and per-model metrics.
- Keep captions descriptive, not generic.

## Visual Coverage Gate

Before final delivery, create a short visual-review note with:

- Figures included and what each one proves.
- Missing figures that would improve the report.
- Whether tables could replace or complement any figure.
- Whether the report overuses text where a chart would be clearer.
- A revision plan if visual coverage is weak.
