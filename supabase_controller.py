from supabase import create_client

class SupabaseController:
  def __init__(self, url: str, key):
    self.supabase = create_client(url, key)

  def get_data_from_table(self, table_name, column_names=None):
    """
    Retrieves data from a given table in the Supabase database.

    Args:
      table_name (str): The name of the table to retrieve data from.
      column_names (list[str], optional): The names of the columns to retrieve. Defaults to ["*"].

    Returns:
      list[dict]: A list of dictionaries, each containing the retrieved column values.
    """
    if column_names is None:
      column_names = ["*"]
    response = self.supabase.table(table_name).select(",".join(column_names)).execute()
    return response.data

  def get_data_from_table_where(self, table_name: str, value: str, column_name: str = "id", column_names: list = None):
    """
    Retrieves data from a specified table in the Supabase database where a column matches a given value.

    Args:
      table_name (str): The name of the table to retrieve data from.
      value (str): The value to match in the specified column.
      column_name (str, optional): The name of the column to apply the equality condition. Defaults to "id".
      column_names (list, optional): The names of the columns to retrieve. Defaults to ["*"].

    Returns:
      list[dict]: A list of dictionaries, each containing the retrieved column values where the condition is met.
    """
    if column_names is None:
      column_names = ["*"]
    response = self.supabase.table(table_name).select(",".join(column_names)).eq(column_name, value).execute()
    return response.data