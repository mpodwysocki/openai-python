import dotenv
import json
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import AzureChatOpenAI
from langchain.output_parsers import PydanticOutputParser
import openai
from pprint import pprint
from pydantic import BaseModel, Field
from typing import List

import os
import sys

dotenv.load_dotenv()

openai.api_type = "azure"
openai.api_base = os.environ.get("OPENAI_API_BASE")
openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_API_VERSION = "2023-05-15"

class Violation(BaseModel):
    rule_ids: List[str] = Field(description="unique rule ID or IDs that were violated.")
    bad_code: str = Field(description="the original code that was bad.")
    suggestion: str = Field(description="the suggested fix for the bad code.")
    comment: str = Field(description="a description of what was wrong with the code and how the suggestion fixes it.")

class GuidelinesResult(BaseModel):
    status: str = Field(description="Succeeded if the request completed, or Error if it did not")
    violations: List[Violation] = Field(description="list of violations if any")

class APIViewModel:

    def __init__(self):
        self.llm = AzureChatOpenAI(deployment_name="gpt-4", openai_api_version=OPENAI_API_VERSION)
        self.output_parser = PydanticOutputParser(pydantic_object=GuidelinesResult)
        self.prompt_template = PromptTemplate(
            input_variables=["apiview", "guidelines", "language"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()},
            template="""
    # GUIDELINES
    {guidelines}
    
    # CODE
    ```
    {apiview}
    ```
    
    # INSTRUCTIONS
    - The language you are evaluating is {language}.
    - Ensure that your code suggestions do not conflict with one another.
    
    # FORMAT INSTRUCTIONS
    {format_instructions}
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def get_response(self, apiview, language):
        general_guidelines, language_guidelines = self.retrieve_guidelines(language)
        all_guidelines = general_guidelines + language_guidelines

        # select the guidelines to evaluate
        guidelines = self.select_guidelines(all_guidelines, categories=[
            "Service client",
            "General guidelines",
            "Client configuration",
        ])
        formatted_guidelines = json.dumps(guidelines, indent=2)

        # dump the formatted template to file for debugging
        formatted_template = self.prompt_template.format(apiview=apiview, guidelines=formatted_guidelines, language=language)
        with open(os.path.join(os.path.dirname(__file__), "formatted_template.txt"), "w") as f:
            f.write(formatted_template)

        result = self.chain.run(apiview=apiview, guidelines=guidelines, language=language, temperature=0)
        parsed = self.output_parser.parse(result)
        with open(os.path.join(os.path.dirname(__file__), "output.json"), "w") as f:
            f.write(json.dumps(parsed.dict(), indent=2))

    def select_guidelines(self, all, *, ids=None, categories=None):
        rules = {}
        if ids:
            rules = {guideline["id"]: guideline for guideline in all if guideline["id"] in ids}
        if categories:
            category_rules = {guideline["id"]: guideline for guideline in all if guideline["category"] in categories}
            rules.update(category_rules)
        # numbering the guidelines improves the quality of the output
        for i, key in enumerate(rules):
            rules[key]["number"] = i
        return list(rules.values())
        

    def retrieve_guidelines(self, language):
        general_guidelines = []
        general_guidelines_path = os.path.join(os.path.dirname(__file__), "..", "docs", "general")
        language_guidelines_path = os.path.join(os.path.dirname(__file__), "..", "docs", language)
        for filename in os.listdir(general_guidelines_path):
            with open(os.path.join(general_guidelines_path, filename), "r") as f:
                items = json.loads(f.read())
                general_guidelines.extend(items)

        language_guidelines = []
        for filename in os.listdir(language_guidelines_path):
            with open(os.path.join(language_guidelines_path, filename), "r") as f:
                items = json.loads(f.read())
                language_guidelines.extend(items)
        return general_guidelines, language_guidelines


if __name__ == "__main__":
    api = APIViewModel()
    filename = "eventgrid.txt"
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, "r") as f:
        apiview_text = f.read()
    print(api.get_response(apiview_text, "python"))
