import dotenv
import gradio as gr
import openai
import os
from typing import List, Dict

dotenv.load_dotenv()

class SeedQuery:
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer
    
    def to_prompt(self) -> List[Dict]:
        return [
            {
                "role": "user",
                "content": self.question
            },
            {
                "role": "system",
                "content": self.answer
            }
        ]

_GENERAL_URLS = [
    "https://azure.github.io/azure-sdk/general_introduction.html",
    "https://azure.github.io/azure-sdk/general_terminology.html",
    "https://azure.github.io/azure-sdk/general_design.html",
    "https://azure.github.io/azure-sdk/general_implementation.html",
    "https://azure.github.io/azure-sdk/general_documentation.html",
    "https://azure.github.io/azure-sdk/general_azurecore.html",
    "https://azure.github.io/azure-sdk/policies_opensource.html",
]

_LANGUAGE_URLS = {
    'dotnet': [
        "https://azure.github.io/azure-sdk/dotnet_introduction.html",
        "https://azure.github.io/azure-sdk/dotnet_implementation.html",
    ],
    'java': [
        "https://azure.github.io/azure-sdk/java_introduction.html",
        "https://azure.github.io/azure-sdk/java_implementation.html",
        "https://azure.github.io/azure-sdk/java_spring.html",
    ],
    'python': [
        "https://azure.github.io/azure-sdk/python_design.html",
        "https://azure.github.io/azure-sdk/python_implementation.html",
        "https://azure.github.io/azure-sdk/python_documentation.html",
    ],
    'typescript': [
        "https://azure.github.io/azure-sdk/typescript_introduction.html",
        "https://azure.github.io/azure-sdk/typescript_design.html",
        "https://azure.github.io/azure-sdk/typescript_implementation.html",
        "https://azure.github.io/azure-sdk/typescript_documentation.html",
    ],
    'android': [
        "https://azure.github.io/azure-sdk/android_design.html",
        "https://azure.github.io/azure-sdk/android_implementation.html",
    ],
    'ios': [
        "https://azure.github.io/azure-sdk/ios_design.html",
        "https://azure.github.io/azure-sdk/ios_implementation.html",
    ],
    'c': [
        "https://azure.github.io/azure-sdk/clang_design.html",
        "https://azure.github.io/azure-sdk/clang_implementation.html",
    ],
    'cpp': [
        "https://azure.github.io/azure-sdk/cpp_introduction.html",
        "https://azure.github.io/azure-sdk/cpp_implementation.html",
    ],
    'go': [
       "https://azure.github.io/azure-sdk/golang_introduction.html",
        "https://azure.github.io/azure-sdk/golang_implementation.html",
    ],
}

_LANGUAGE_PROMPTS = {
    'dotnet': [],
    "java": [],
    "python": [],
    "typescript": [],
    "android": [],
    "ios": [],
    "c": [],
    "cpp": [],
    "go": [],
}

openai.api_key = os.getenv("OPENAI_API_KEY")

def _query_openai(prompt: str, lang: str):
    input = []

    # add any seed queries for the language
    for seed in _LANGUAGE_PROMPTS.get(lang, []):
        input.extend(seed.to_prompt())

    # add the base system prompt
    input.append({
        "role": "system",
        "content": _build_system(lang)
    })

    # add actual query last
    input.append({
        "role": "user",
        "content": f"According to the Azure SDK for {lang} guidelines... {prompt}"
    })

    response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=input,
            temperature=0.8,
            presence_penalty=0,
            frequency_penalty=0,
            stream=True,
        )
    return response

def _build_system(lang: str) -> str:
    lang_urls = _LANGUAGE_URLS.get(lang, [])
    lines = []
    lines.append("You are an assistant that attempts to answer questions related to the Azure SDK Guidelines.")
    lines.append("You will attempt to find the answer to general questions in the following documents:")
    lines.extend([f"- {x}" for x in _GENERAL_URLS])
    if lang_urls:
        lines.append("You will attempt to find the answer to {lang}-specific questions in the following documents:")
        lines.extend([f"- {x}" for x in lang_urls])
    lines.append("Don't use 'According to the Azure SDK guidelines' in your answer")
    lines.append("If you are unsure of the answer, recommend the user contact the Azure SDK team.")
    lines.append("If the user asks for an exception to the guidelines, firmly insist that they contact the Azure SDK team for approval.")
    lines.append("Provide direct links to the guideline referenced, when possible.")
    lines.append("When reading the guidelines, interpret DO as a requirement and SHOULD as a recommendation.")
    return "\n".join(lines)

with gr.Blocks() as app:
    lang_selector = gr.Dropdown(["dotnet", "java", "python", "typescript", "android", "ios", "c", "cpp", "go"], label="Language")
    chatbot = gr.Chatbot()
    query = gr.Textbox()
    clear = gr.Button("Clear")

    def update_user(message, chat_history):
        return "", chat_history + [[message, None]]

    def update_bot(message, chat_history, lang):
        message = chat_history[-1][0]
        response = _query_openai(message, lang)
        for chunk in response:
            delta = chunk.choices[0].delta
            content = delta.get("content", None)
            if content:
                curr_response = chat_history[-1][1] or ""
                chat_history[-1][1] = curr_response + content
                yield chat_history

    query.submit(update_user, [query, chatbot], [query, chatbot], queue=False).then(
        update_bot, [query, chatbot, lang_selector], [chatbot]
    )
    clear.click(lambda: None, None, chatbot, queue=False)

app.queue()
app.launch(share=True)
