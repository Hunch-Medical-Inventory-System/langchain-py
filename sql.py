from sqlalchemy import create_engine, MetaData, Table, select
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()
USER = os.getenv("db_user")
PASSWORD = os.getenv("db_password")
HOST = os.getenv("db_host")
PORT = os.getenv("db_port")
DBNAME = os.getenv("db_name")

# initialize database engine
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
engine = create_engine(DATABASE_URL)

metadata = MetaData()
metadata.reflect(bind=engine)

supplies_table = metadata.tables["supplies"]
inventory_table = metadata.tables["inventory"]

# initialize database functions
def get_supplies_string():
    with engine.connect() as conn:
        stmt = select(supplies_table.c.name, supplies_table.c.id)
        result = conn.execute(stmt).fetchall()
        return ", ".join([f"{row.name}:{row.id}" for row in result])

from sqlalchemy import select

def select_from_table(column, value, table_name, columns=None):
    """
    Function to select specific columns from a table where a specific column equals a value.

    Args:
        column (str): The column name to filter by.
        value (str/int): The value to search for in the specified column.
        table_name (str): The name of the table to query.
        columns (list, optional): List of column names to retrieve. Defaults to all columns.

    Returns:
        list[dict]: A list of rows as key-value pairs.
    """
    # Reflect the table structure from the database
    table = Table(table_name, metadata, autoload_with=engine)

    # Select all columns if none specified
    selected_columns = [table.c[col] for col in columns] if columns else table.c

    # Build the query
    stmt = select(*selected_columns).where(getattr(table.c, column) == value)

    # Execute the query and fetch the results
    with engine.connect() as conn:
        result = conn.execute(stmt)
        rows = [dict(row) for row in result.mappings()]  # Convert to key-value pairs

    return rows



