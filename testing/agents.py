from sqlalchemy import create_engine, MetaData, select, Table
from sqlalchemy.orm import sessionmaker

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents import AgentType
from langchain.prompts import PromptTemplate
# from langchain.output_parsers import SQLResultOutputParser

from langchain_ollama import OllamaLLM
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

db = SQLDatabase(engine, include_tables=["inventory", "supplies"], sample_rows_in_table_info=2)

# Define a dynamic query using a PromptTemplate
correcting_prompt_content = """

Answer the question only based on the context
Your task is to match as closely as possible, the medication from the input to an item from the context

Your output should only consist of:
the original input but replace the medication name with "inventory.supply_id 'id of medication""

### Example:

**User Input:** "How much Benadril do we have in stock?"
**Transformed Output:** "How many inventory.supply_id: 2 do we have in stock?"

context: {context}

Input: {input}
Assistant:

"""
data_prompt_content = """
Only Answer using the context and data from the database

Context:
Never return SQL statements.
Return quantities as "*quantity from inventory* / *quantity_in_pack from supplies*"
Only use IDs when selecting from tables.

Medication information (name, dosage, etc.) is in the supplies table
Tracking info (quantity, supply ID, location, etc.) is in the inventory table.
When User ID is present, it is considered deleted.

### Example:

**User Input:** "How many inventory.supply_id: 2 do we have in stock?"
**Database Lookup:** "SELECT quantity FROM inventory WHERE supply_id = 2;" → (Returns '[{quantity: 3}, {quantity: 5}, {quantity: 4}]')
**Database Lookup:** "SELECT name, quantity_in_pack FROM supplies WHERE id = 2;" → (Returns '[{"name": "Diphenhydramine (Benadryl)","quantity_in_pack": "60 capsule"}]')
**Transformed Output:** "There is 12 / 60 capsules of benadryl in stock?"

Input: {input}
tools: {tools}
tool_names: {tool_names}
agent_scratchpad: {agent_scratchpad}
Assistant:
"""


# Initialize PromptTemplate with the correct variable
correcting_prompt_template = PromptTemplate(
    input_variables=["input", "context"],
    template=correcting_prompt_content
)
data_prompt_template = PromptTemplate(
    input_variables=["input"],
    template=data_prompt_content
)

# initialize llm and sql agent
llm = OllamaLLM(model="qwen2.5:3b", temperature=0.5, verbose=True)
spell_check = correcting_prompt_template | llm
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
    prompt=data_prompt_template,
    tools = [SQLDatabase(engine)],
    tool_names = ["SQLDatabase"]
)
# query = prompt_template.format(input="how much Benadryl do I have?")

supplies_table = metadata.tables["supplies"]
inventory_table = metadata.tables["inventory"]

def get_supplies_string():
    with engine.connect() as conn:
        stmt = select(supplies_table.c.name, supplies_table.c.id)
        result = conn.execute(stmt).fetchall()
        return ", ".join([f"{row.name}:{row.id}" for row in result])

query = "how much Zoloft do I have?"

# Now invoke the agent with the formatted query
reformatted_question = spell_check.invoke({"input": query, "context": get_supplies_string()})
print(reformatted_question)
response = sql_agent.invoke({"input":reformatted_question})

# Print the response
print(response)
