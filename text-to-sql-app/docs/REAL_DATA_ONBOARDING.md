# Real Data Onboarding

This guide explains how to replace development sample Parquet files or add new real business Parquet files.

The app now uses one central data catalog for a single Question & Answer Text-to-SQL workflow. Do not add raw data directly to planner or query prompts. The Analysis Planner and Query Agent receive metadata only.

## Where Real Data Goes

Store real Parquet files under `data/` using stable, descriptive paths:

```text
data/
|-- pax_forecast/
|-- special_cruise/
`-- qa/
```

Existing Pax Forecast and Special Cruise files are no longer active modules. They may remain as catalog data sources. New data sources can use new folders under `data/`.

## Required Catalog Metadata

Every table that SQL may query must be represented in `backend/app/catalog.py`.

Each table needs:

- `table_name`
- `data_path`
- `description`
- column metadata

The catalog also supports:

- relationships
- example questions
- example SQL

Relationships should be added whenever SQL may need to join tables.

## Table Metadata Checklist

Complete this checklist before adding a real table to the catalog.

## Identity

- What does one row represent?
- What is the grain of the table?
- What is the primary key?
- Is the primary key unique?
- Is the table an event table, snapshot table, dimension table, or aggregate table?

## Columns

- Which columns are dates?
- Which columns are measures?
- Which columns are dimensions?
- Which columns are identifiers?
- Which columns are nullable?
- Which columns need business-friendly descriptions?
- Which columns have common aliases or business terms?
- Which columns have useful example values?

## Joins

- Which columns can be joined to other tables?
- Are join keys unique on one side or many-to-many?
- What is the relationship type?
- Are there known join caveats?

## Data Quality

- Are there duplicate rows?
- Are there missing values in important columns?
- Are dates in the expected range?
- Are numeric measures in expected units?
- Are currencies consistent?
- Are percentages represented as `0.32` or `32`?

## Sensitivity

- Are there sensitive columns?
- Are there personal data columns?
- Are there columns that should never be exposed to agents or users?
- Should sensitive columns be excluded from Parquet files or omitted from catalog metadata?

## Example Metadata Profile

```python
TableDefinition(
    table_name="pax_forecast",
    data_path="data/pax_forecast/pax_forecast.parquet",
    description="Passenger forecast rows by departure date and route.",
    columns=(
        ColumnDefinition(
            name="departure_date",
            type="DATE",
            description="Scheduled departure date for the sailing.",
            examples=("2026-06-01",),
            business_terms=("sailing date", "departure"),
        ),
        ColumnDefinition(
            name="forecast_pax",
            type="INTEGER",
            description="Forecasted passenger count.",
            examples=("1840",),
            business_terms=("pax", "passengers", "demand"),
        ),
    ),
)
```

```python
RelationshipDefinition(
    left_table="pax_forecast",
    left_column="route",
    right_table="pax_route_targets",
    right_column="route",
    relationship_type="many_to_one",
    description="Each forecast row can join to one route target by route.",
)
```

## Replacing Sample Parquet Files

1. Place the real Parquet file under `data/`.
2. Confirm the file name and table name you want the app to use.
3. Update the table `data_path` in `backend/app/catalog.py`.
4. Update column metadata to match the real file.
5. Add or update relationships.
6. Update example questions.
7. Update example SQL.
8. Run validation checks.
9. Test `/api/ask` with representative questions.

## Validating Real Data

Check that the file path in the catalog exists:

```powershell
Get-ChildItem data\pax_forecast\pax_forecast.parquet
```

Confirm DuckDB can read it:

```powershell
C:\Users\durmuyu\AppData\Local\anaconda3\python.exe -c "import duckdb; print(duckdb.sql(\"SELECT * FROM read_parquet('data/pax_forecast/pax_forecast.parquet') LIMIT 5\").fetchall())"
```

Confirm row count:

```sql
SELECT COUNT(*) FROM read_parquet('data/pax_forecast/pax_forecast.parquet');
```

Confirm column names:

```sql
DESCRIBE SELECT * FROM read_parquet('data/pax_forecast/pax_forecast.parquet');
```

Compare real column names to catalog metadata.

Use app-level table names in example SQL:

```sql
SELECT pf.route, pf.forecast_pax, rt.target_load_factor
FROM pax_forecast pf
JOIN pax_route_targets rt ON pf.route = rt.route
LIMIT 10;
```

The query should run through `run_query(sql)` or `run_queries([...])`, not by bypassing the application query runner.

## Confirm SQL Validator Scope

- Queries against catalog tables should pass.
- Queries against unknown tables should fail.
- File-reading functions such as `read_parquet()` should fail when used in user SQL.
- Destructive or modifying statements should fail.

The validator should allow only tables listed in the central data catalog.

## Agent Safety Note

Allowed Analysis Planner and Query Agent context:

- catalog description
- table names
- column names
- column types
- column descriptions
- examples
- business terms
- relationships
- example questions
- example SQL

Not allowed in Analysis Planner or Query Agent context:

- full Parquet rows
- sensitive raw values
- unrestricted file paths
- direct access instructions for `read_parquet()`

Use `build_catalog_context()` as the source of planner and Query Agent schema context. The Response Agent may receive validated, limited query results for answer writing, but it must not receive unrestricted Parquet rows or execute SQL.
