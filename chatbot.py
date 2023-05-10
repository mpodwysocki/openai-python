import dotenv
import gradio as gr
import openai
import os

dotenv.load_dotenv()

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

openai.api_key = os.getenv("OPENAI_API_KEY")

def _build_system(self, lang: str) -> str:
    lang_urls = _LANGUAGE_URLS.get(lang, [])
    lines = []
    lines.append("You are an assistant that attempts to answer questions related to the Azure SDK Guidlines.")
    lines.append("You will attempt to find the answer to general questions in the following documents:")
    lines.extend([f"- {x}" for x in _GENERAL_URLS])
    if lang_urls:
        lines.append("You will attempt to find the answer to {lang}-specific questions in the following documents:")
        lines.extend([f"- {x}" for x in lang_urls])
    lines.append("Don't use 'According to the Azure SDK guidelines' in your answer")
    lines.append("If you are unsure of the answer, recommend the user contact the Azure SDK team.")
    lines.append("If the user asks for an exception to the guidlines, firmly insist that they contact the Azure SDK team for approval.")
    lines.append("Do not quote the guidelines in your answer.")
    lines.append("When reading the guidelines, interpret DO as a requirement and SHOULD as a recommendation.")
    return "\n".join(lines)

with gr.Blocks() as app:
    lang_selector = gr.Dropdown(["dotnet", "java", "python", "typescript", "android", "ios", "c", "cpp", "go"], label="Language", default="dotnet", key="lang")
    chatbot = gr.Chatbot()
    query = gr.Textbox()
    clear = gr.Button("Clear")

    def respond(message, chat_history, lang):
        reply = f"{lang}"
        chat_history.append((message, reply))
        return "", chat_history
    
    query.submit(respond, [query, chatbot, lang_selector], [query, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

app.launch()
