# Real Data Onboarding

This guide explains how to replace development sample Parquet files with real business Parquet files later.

The current app already supports:

- module registry metadata
- multiple Parquet-backed tables per module
- table relationships
- column metadata
- SQL validation
- DuckDB query execution

Do not add raw data directly to prompts or agent context. Future SQL Agent context must be built from metadata only.

## Where Real Data Goes

Store real Parquet files under the existing `data/` structure:

```text
data/
|-- pax_forecast/
|-- special_cruise/
`-- qa/
```

Use stable, descriptive file names:

```text
data/pax_forecast/pax_forecast.parquet
data/pax_forecast/pax_route_targets.parquet
data/special_cruise/special_cruise_profit.parquet
data/qa/qa.parquet
```

When replacing sample files, keep table names stable when possible. If a table name changes, update the module registry and any example SQL that references it.

## Required Registry Metadata

Every real table must be represented in `backend/app/modules/registry.py`.

Each table needs:

- `table_name`
- `data_path`
- `description`
- column metadata

Each module needs:

- `module_id`
- `label`
- `description`
- `tables`
- `relationships`
- `example_questions`
- `example_sql`

Relationships should be added whenever SQL may need to join tables.

## Table Metadata Checklist

Complete this checklist before adding a real table to the registry.

### Identity

- What does one row represent?
- What is the grain of the table?
- What is the primary key?
- Is the primary key unique?
- Is the table an event table, snapshot table, dimension table, or aggregate table?

### Columns

- Which columns are dates?
- Which columns are measures?
- Which columns are dimensions?
- Which columns are identifiers?
- Which columns are nullable?
- Which columns need business-friendly descriptions?
- Which columns have common aliases or business terms?
- Which columns have useful example values?

### Joins

- Which columns can be joined to other tables?
- Are join keys unique on one side or many-to-many?
- What is the relationship type?
- Are joins based on exact keys, dates, route names, event IDs, or other business identifiers?
- Are there known join caveats?

### Data Quality

- Are there duplicate rows?
- Are there missing values in important columns?
- Are dates in the expected range?
- Are numeric measures in expected units?
- Are currencies consistent?
- Are percentages represented as `0.32` or `32`?

### Sensitivity

- Are there sensitive columns?
- Are there personal data columns?
- Are there columns that should never be exposed to agents or users?
- Should sensitive columns be excluded from Parquet files or omitted from registry metadata?

### Business Definitions

- Are key metrics defined clearly?
- Are formulas documented?
- Are units documented?
- Are filters or exclusions documented?
- Is there an owner who can confirm the definition?

## Example Metadata Profile

Example table metadata for a real Pax Forecast table:

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
            name="route",
            type="VARCHAR",
            description="Commercial route for the sailing.",
            examples=("Stockholm-Tallinn",),
            business_terms=("line", "route"),
        ),
        ColumnDefinition(
            name="forecast_pax",
            type="INTEGER",
            description="Forecasted passenger count.",
            examples=("1840",),
            business_terms=("pax", "passengers", "demand"),
        ),
        ColumnDefinition(
            name="capacity",
            type="INTEGER",
            description="Available passenger capacity.",
            examples=("2100",),
            business_terms=("inventory", "capacity"),
        ),
    ),
)
```

Example relationship metadata:

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

Example questions:

```python
example_questions=(
    "Which routes are forecast to exceed target load factor next month?",
    "Show forecasted passenger volume by route and departure week.",
)
```

Example SQL:

```python
example_sql=(
    "SELECT * FROM pax_forecast LIMIT 10",
    "SELECT pf.route, pf.forecast_pax, rt.target_load_factor FROM pax_forecast pf JOIN pax_route_targets rt ON pf.route = rt.route LIMIT 10",
)
```

## Replacing Sample Parquet Files

1. Place the real Parquet file in the correct `data/<module>/` folder.
2. Confirm the file name and table name you want the app to use.
3. Update the module registry `data_path`.
4. Update column metadata to match the real file.
5. Add or update relationships.
6. Update example questions.
7. Update example SQL.
8. Run validation checks.
9. Test `/api/ask` for the affected module.

## Validating Real Data

Before using a real Parquet file, confirm these items.

### File Exists

Check that the file path in the registry exists:

```powershell
Get-ChildItem data\pax_forecast\pax_forecast.parquet
```

### DuckDB Can Read It

Run a simple DuckDB read:

```powershell
C:\Users\durmuyu\AppData\Local\anaconda3\python.exe -c "import duckdb; print(duckdb.sql(\"SELECT * FROM read_parquet('data/pax_forecast/pax_forecast.parquet') LIMIT 5\").fetchall())"
```

### Confirm Row Count

```sql
SELECT COUNT(*) FROM read_parquet('data/pax_forecast/pax_forecast.parquet');
```

### Confirm Column Names

```sql
DESCRIBE SELECT * FROM read_parquet('data/pax_forecast/pax_forecast.parquet');
```

Compare the real column names to the registry metadata.

### Confirm Joins Work

Use the registered table names in module example SQL:

```sql
SELECT pf.route, pf.forecast_pax, rt.target_load_factor
FROM pax_forecast pf
JOIN pax_route_targets rt ON pf.route = rt.route
LIMIT 10;
```

The query should run through `run_query(module_id, sql)`, not by bypassing the application query runner.

### Confirm SQL Validator Scope

For each module:

- queries against registered module tables should pass
- queries against tables from another module should fail
- file-reading functions such as `read_parquet()` should fail when used in user SQL

The validator should allow only tables listed in the selected module metadata.

## Agent Safety Note

The SQL Agent must only receive metadata, never full raw data.

Allowed future agent context:

- module description
- table names
- column names
- column types
- column descriptions
- examples
- business terms
- relationships
- example questions
- example SQL

Not allowed in future agent context:

- full Parquet rows
- sensitive raw values
- unrestricted file paths
- direct access instructions for `read_parquet()`

Use `build_agent_schema_context(module_id)` as the future source of SQL Agent schema context.

