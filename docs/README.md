# Documentation

Reference documentation for the Delhi GRAP Analytics Platform, organized by
what stage of the project it governs. Start with the [root README](../README.md)
for the project overview — these documents go one level deeper.

## Methodology

| Document | Covers |
|---|---|
| [`analysis_plan.md`](analysis_plan.md) | The pre-analysis protocol: research question, unit of analysis, event-window design, planned analytical sequence, confounders, allowed vs. unsupported claims, and limitations. Written before the event-window notebooks, and the standard every one of them is checked against. |
| [`grap_event_data_contract.md`](grap_event_data_contract.md) | Schema and validation rules for the manually verified GRAP event calendar — what counts as an event, date-field semantics, controlled vocabularies, and why every row must be human-verified against an official CAQM order. |
| [`data_dictionary.md`](data_dictionary.md) | Field-level documentation for every dataset under `data/processed/` — grain, units, source, and missingness treatment. |

## Data engineering

| Document | Covers |
|---|---|
| [`sql_layer_design.md`](sql_layer_design.md) | Design of the optional SQLite analytical layer under [`sql/`](../sql/): storage strategy, table/view grain, relationships, and the 15 prepared queries. |
| [Data-quality reports](../reports/data_quality/) | Generated audit output: Gate 1 structural/missingness summary, GRAP calendar validation, merged-dataset validation. |

## Dashboard

| Document | Covers |
|---|---|
| [`powerbi_architecture.md`](powerbi_architecture.md) | The finalized Power BI semantic model: fact/dimension tables, relationships, keys, the measure catalogue, and performance/best-practice decisions. |
| [`dashboard_design_system.md`](dashboard_design_system.md) | The UX system the dashboard is built against: color palette, typography, card/KPI conventions, page-by-page interaction design, and accessibility rules. |
| [`page1_executive_overview.md`](page1_executive_overview.md) | The implementation spec for the Executive Overview page — exact visual placements, fields, and formatting. |
| [`powerbi/measures.md`](../powerbi/measures.md), [`powerbi/visual_inventory.md`](../powerbi/visual_inventory.md), [`powerbi/README_powerbi.md`](../powerbi/README_powerbi.md) | The DAX measure catalogue, the visual-by-visual build inventory, and the Power BI build manual, kept alongside the `.pbip` project itself. |

## Archive

[`archive/`](archive/) holds superseded planning documents (early development
log, pre-analysis issue tracker, a completion-percentage snapshot) kept for
process history. They describe an earlier, incomplete state of the project —
for current information, use the documents above.

## Other

`station_selection.xlsx` is the working file used to screen and lock the
8-station sample before any outcome analysis (see the root README's
[Methodology](../README.md#methodology) section for the selection criteria).
