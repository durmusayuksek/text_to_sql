from app.catalog import ColumnDefinition, TableDefinition


# Copy this table into DATA_CATALOG.tables only after the Parquet file exists.
# Suggested path: data/sales/sales_bookings.parquet
SALES_BOOKINGS_TABLE = TableDefinition(
    table_name="sales_bookings",
    data_path="data/sales/sales_bookings.parquet",
    description=(
        "Booking-level sales records by booking date, departure date, route, "
        "ship, market, and sales channel. One row represents one booking."
    ),
    columns=(
        ColumnDefinition(
            name="booking_date",
            type="DATE",
            description="Date when the booking was created.",
            business_terms=("booking date", "sale date", "created date"),
        ),
        ColumnDefinition(
            name="departure_date",
            type="DATE",
            description="Scheduled departure date for the booked sailing.",
            business_terms=("sailing date", "travel date", "departure"),
        ),
        ColumnDefinition(
            name="route",
            type="VARCHAR",
            description="Commercial route for the booked sailing.",
            business_terms=("line", "route"),
        ),
        ColumnDefinition(
            name="ship",
            type="VARCHAR",
            description="Ship assigned to the booked sailing.",
            business_terms=("vessel", "ship"),
        ),
        ColumnDefinition(
            name="market",
            type="VARCHAR",
            description="Sales market or country grouping for the booking.",
            business_terms=("market", "country", "source market"),
        ),
        ColumnDefinition(
            name="sales_channel",
            type="VARCHAR",
            description="Channel where the booking was sold.",
            business_terms=("channel", "booking channel", "distribution channel"),
        ),
        ColumnDefinition(
            name="passenger_count",
            type="INTEGER",
            description="Number of passengers included in the booking.",
            business_terms=("passengers", "pax", "passenger volume"),
        ),
        ColumnDefinition(
            name="net_sales",
            type="DECIMAL",
            description="Net sales amount for the booking after discounts and exclusions.",
            business_terms=("sales", "revenue", "net revenue"),
        ),
        ColumnDefinition(
            name="booking_id",
            type="VARCHAR",
            description="Internal booking identifier. Sensitive and excluded from OpenAI payloads.",
            business_terms=("booking id", "reservation id"),
            sensitive=True,
            redaction_strategy="omit",
        ),
        ColumnDefinition(
            name="client_id",
            type="VARCHAR",
            description="Internal client identifier. Sensitive and excluded from OpenAI payloads.",
            business_terms=("customer id", "client id"),
            sensitive=True,
            redaction_strategy="omit",
        ),
    ),
)
