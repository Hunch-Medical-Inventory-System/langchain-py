from sql import get_supplies_string, select_from_table
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

# Initialize llm
llm = OllamaLLM(model="qwen2.5:3b", temperature=0.5, verbose=True)

# Initialize prompt contents
id_converter_prompt_content = """
Answer the question only based on the context.
Your task is to match as closely as possible, the medication from the input to an item from the context.
The id should be the number next to the medication name in the context.

Your output should only consist of the id number.
If the medication is not found in the context, return "0".

### Example:
**User Input:** "How much Benadril do we have in stock?"
**Transformed Output:** "2"

Context: {context}

Input: {input}
Assistant:
"""

inventory_prompt_content = """
Only Answer using the context and data from the database.

Use quantity for quantity.
Use length for amount of packages.

Use location for location.
Use type for type
Use quantity_in_pack for cap.
Use name for corrected name
Use strength_or_volume for strength/volume
Use route for route
Use possible_side_effect for possible side effects

Context:
{context}

### Example:
**User Input:** "How much Benadril do we have in stock?"
**Output:** "There is 69 capsules over 2 packages with a cap of 60 capsules per package of Diphenhydramine (Benadryl) in stock?"

Input: {input}
Assistant:
"""

# Initialize prompt templates
id_converter_prompt_template = PromptTemplate(template=id_converter_prompt_content, input_variables=["input", "context"])
inventory_prompt_template = PromptTemplate(template=inventory_prompt_content, input_variables=["input", "context"])

# Initialize chains
id_converter_chain = id_converter_prompt_template | llm
inventory_chain = inventory_prompt_template | llm


"""
This function takes a question about the quantity of a medication, uses the id converter to get the supply id, and then uses the supply id to get the quantity of the medication from the inventory table.

Parameters:
    question (object): string containing the question

Returns:
    str: string containing information about the medication based on question
"""
def get_inventory_information(question: object) -> str:
    supplies_table = get_supplies_string()
    supply_id = int(id_converter_chain.invoke({"input": question, "context": supplies_table}))
    if supply_id == 0:
        return "Please Try Again. No Medication Found."
    supply_row = select_from_table("id", supply_id, "supplies", columns=["type", "name", "strength_or_volume", "route_of_use", "quantity_in_pack", "possible_side_effects", "location"])
    inventory_rows = select_from_table("supply_id", supply_id, "inventory", columns=["quantity"])
    total_quantity = sum(item['quantity'] for item in inventory_rows)
    context = {
        "quantity": total_quantity,
        "length": len(inventory_rows),
        "type": supply_row[0]["type"],
        "name": supply_row[0]["name"],
        "strength_or_volume": supply_row[0]["strength_or_volume"],
        "route": supply_row[0]["route_of_use"],
        "cap": supply_row[0]["quantity_in_pack"],
        "possible_side_effect": supply_row[0]["possible_side_effects"],
        "location": supply_row[0]["location"]
    }
    return inventory_chain.invoke({"input": question, "context": context})
