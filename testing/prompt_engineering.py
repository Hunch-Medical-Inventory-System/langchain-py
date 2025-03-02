from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.memory import ConversationBufferMemory
from supabase_controller import SupabaseController

# sql agent

# Load environment variables
import os
from dotenv import load_dotenv

load_dotenv()
env_url: str = os.environ.get("DATABASE_SUPABASE_URL")
env_anon_key: str = os.environ.get("DATABASE_SUPABASE_ANON_API_KEY")


class OllamaLLMInitializer():
    def __init__(self, model: str, database_controller, **kwargs: dict):
        self.database_controller = database_controller

        # llm setup
        self.llm = OllamaLLM(model=model, **kwargs)

        # prompt contents
        self.base_prompt_content = """

      You are a helpful assistant.

      Question: 
      {question}

      Answer:

    """

        supabase_table_picker_prompt_content = """

      Answer the user's questions based only on the following context.
      Your answer should only consist of a string of the table name.
      If the answer can not be gotten with the functions provided reply with "An error occurred. Please try again."

      User: {input}
      Assistant:

    """

        self.database_data_converter_prompt_content = """

      Keep responses breif when possible
      Answer the user 's questions based only on the following context. 
      Give answers based on the inventory table, substitute the supply id with the name of the item from the supply table.
      When analyzing combine all quantities with the same supply_id.
      If the supply id is not in the inventory table assume there is none.
      If the answer can not be gotten with the information provided reply with why it can not be gotten.

      Context:
      {context}

      User: {input}
      Assistant:

    """

        self.basic_prompt = PromptTemplate(template=self.base_prompt_content, input_variables=["question"])
        self.supabase_table_picker_prompt = PromptTemplate(template=supabase_table_picker_prompt_content,
                                                           input_variables=["input"])
        self.supabase_data_converter_prompt = PromptTemplate(template=self.database_data_converter_prompt_content,
                                                             input_variables=["input"])

        self.supabase_table_picker_llm_chain = {"context": RunnablePassthrough(),
                                                "input": RunnablePassthrough()} | self.supabase_table_picker_prompt | self.llm
        self.supabase_data_converter_llm_chain = {"context": RunnablePassthrough(),
                                                  "input": RunnablePassthrough()} | self.supabase_data_converter_prompt | self.llm

    def answer_question_with_data(self, question):
        supplies = self.database_controller.get_data_from_table("supplies", ["id", "name"])
        inventory = self.database_controller.get_data_from_table("inventory", ["id", "supply_id", "quantity"])

        formatted_supplies = " \n".join([f"{supply['id']}: {supply['name']}" for supply in supplies])
        formatted_inventory = " \n".join(
            [f"{inventory['id']}: {inventory['supply_id']}: {inventory['quantity']}" for inventory in inventory])

        # print(formatted_supplies)
        # print(formatted_inventory)

        context = f"Supplies:\n{formatted_supplies}\n\nInventory:\n{formatted_inventory}"

        response = self.supabase_data_converter_llm_chain.invoke({"input": question, "context": context})
        return response


def main():
    supabase_controller = SupabaseController(env_url, env_anon_key)
    ollama = OllamaLLMInitializer(model="qwen2.5:0.5b", database_controller=supabase_controller, )

    print("Welcome to the Ollama chat! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        response = ollama.answer_question_with_data(user_input)
        print("Ollama:", response)

    print("Goodbye!")


if __name__ == "__main__":
    main()