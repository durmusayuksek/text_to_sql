# Real Data Onboarding

This guide explains how to add real business Parquet files safely to the central Data Catalog.

The app stays a single Question & Answer Text-to-SQL workflow. Do not connect production files automatically. Add one table first, verify it, then add relationships and joins later.

## Safety Principles

- Prefer cleaned analytical Parquet files over raw operational exports.
- Remove unnecessary personal or sensitive columns before they reach the app.
- Keep customer names, emails, phone numbers, addresses, personal notes, and free-text comments out of analytical files unless there is a strong approved reason.
- Mark identifier columns as sensitive in `backend/app/catalog.py`.
- Analysis Planner and Query Agent receive catalog metadata only, not raw rows.
- Response Agent receives minimized query result summaries. Sensitive columns are redacted before OpenAI payloads are built.
- `DEBUG_QUERY_RESULTS=true` can still return local raw rows to the API client for debugging, so use it carefully.

## Prepare Parquet Files

1. Export from the source system into a controlled staging area.
2. Remove columns that are not needed for analysis.
3. Remove direct personal data such as names, email, phone, address, and free-text comments.
4. Keep stable business dimensions, dates, and numeric measures.
5. Convert to Parquet with clear column names using lowercase snake_case.
6. Store the file under `data/<domain>/<table_name>.parquet`.

Example:

```text
data/
`-- sales/
    `-- sales_bookings.parquet
```

## Inspect A Parquet File

Use the helper script before adding a file to the catalog:

```powershell
C:\Users\durmuyu\AppData\Local\anaconda3\python.exe scripts\inspect_parquet.py data\sales\sales_bookings.parquet
```

The script prints:

- column names
- data types
- row count
- sample rows
- null counts
- possible identifier columns
- possible date columns
- possible numeric measure columns

Use this output to decide which columns belong in the catalog and which should be removed or marked sensitive.

## Catalog Metadata

Every queryable table must be represented in `backend/app/catalog.py`.

Each table needs:

- `table_name`
- `data_path`
- `description`
- column metadata

Each column should include:

- `name`
- `type`
- `description`
- optional `business_terms`
- optional `examples`
- optional `sensitive`
- optional `redaction_strategy`

Supported redaction strategies:

- `omit`: remove the sensitive column from Response Agent OpenAI sample rows and summaries.
- `mask`: include the column but replace values with `***REDACTED***`.
- `hash`: include a deterministic SHA-256 hash value.

Defaults:

```python
sensitive=False
redaction_strategy="omit"
```

For identifiers such as `booking_id`, `client_id`, `customer_id`, reservation IDs, loyalty IDs, or account IDs, start with:

```python
sensitive=True
redaction_strategy="omit"
```

## Sales Bookings Example

Do not add this table to the active catalog until `data/sales/sales_bookings.parquet` exists.

A copy-ready example is available at:

```text
docs/catalog_examples/sales_bookings_catalog_entry.py
```

The example table is `sales_bookings` with these columns:

- `booking_date`
- `departure_date`
- `route`
- `ship`
- `market`
- `sales_channel`
- `passenger_count`
- `net_sales`
- `booking_id` marked `sensitive=True`, `redaction_strategy="omit"`
- `client_id` marked `sensitive=True`, `redaction_strategy="omit"`

It intentionally does not include customer names, emails, phone numbers, addresses, or free-text comments.

## Column Descriptions

Write descriptions for business users, not database engineers.

Good:

```python
ColumnDefinition(
    name="net_sales",
    type="DECIMAL",
    description="Net sales amount for the booking after discounts and exclusions.",
    business_terms=("sales", "revenue", "net revenue"),
)
```

Weak:

```python
ColumnDefinition(
    name="net_sales",
    type="DECIMAL",
    description="Decimal column.",
)
```

## Relationships

Add relationships when joins are expected.

Example:

```python
RelationshipDefinition(
    left_table="sales_bookings",
    left_column="route",
    right_table="route_targets",
    right_column="route",
    relationship_type="many_to_one",
    description="Each booking can join to one route target by route.",
)
```

Start with one table first. Add joins only after each table has been tested independently.

## Example Questions And SQL

Add example questions that reflect real business language:

```python
example_questions=(
    "What was passenger volume by route last month?",
    "Which sales channels generated the most net sales?",
    "Show booking trends by market and departure month.",
)
```

Add example SQL that uses safe DuckDB SQL and catalog table names:

```python
example_sql=(
    "SELECT route, SUM(passenger_count) AS passengers FROM sales_bookings GROUP BY route ORDER BY passengers DESC LIMIT 10",
    "SELECT sales_channel, SUM(net_sales) AS net_sales FROM sales_bookings GROUP BY sales_channel ORDER BY net_sales DESC LIMIT 10",
)
```

## Test One Table First

1. Put the Parquet file under `data/sales/sales_bookings.parquet`.
2. Run the inspection helper.
3. Add the table metadata to `backend/app/catalog.py`.
4. Keep relationships empty at first.
5. Add one or two example questions and example SQL statements.
6. Run backend tests.
7. Ask one simple Swagger question, such as:

```json
{
  "question": "Show passenger volume by route"
}
```

## Test Joins Later

After the first table works:

1. Add the second Parquet file.
2. Inspect it with `scripts/inspect_parquet.py`.
3. Add its table metadata.
4. Add one relationship.
5. Add one join example SQL.
6. Test the join through `run_query(sql)` or Swagger.

Do not bypass the application query runner for app validation. User SQL must still go through `sql_validator.py`.

## Validation Commands

Run backend tests:

```powershell
cd backend
C:\Users\durmuyu\AppData\Local\anaconda3\python.exe -m pytest
```

Run the frontend build if API response types or frontend files changed:

```powershell
cd frontend
npm run build
```

Inspect a Parquet file:

```powershell
C:\Users\durmuyu\AppData\Local\anaconda3\python.exe scripts\inspect_parquet.py data\sales\sales_bookings.parquet
```

From the repo root, test a simple catalog query after adding the table:

```powershell
cd backend
C:\Users\durmuyu\AppData\Local\anaconda3\python.exe -c "from app.duckdb_layer.query_runner import run_query; print(run_query('SELECT route, SUM(passenger_count) AS passengers FROM sales_bookings GROUP BY route LIMIT 10'))"
```
