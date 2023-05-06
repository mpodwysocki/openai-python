
from dotenv import load_dotenv
import markdown_it
import os
import openai
import re

# Load from the environment
load_dotenv()

# Create a new MarkdownIt instance
md = markdown_it.MarkdownIt()

organization = os.environ['OPENAI_API_ORGANIZATION']
api_key = os.environ['OPENAI_API_KEY']

openai.organization = organization
openai.api_key = api_key

# API Doc Constants
MAY_PATTERN = r'{% include requirement/MAY id="[a-zA-Z0-9_-]+" %}'
MAY_REPLACE = 'YOU MAY'
MUST_DO_PATTERN = r'{% include requirement/MUST id="[a-zA-Z0-9_-]+" %}'
MUST_NO_ID_PATTERN = r'{% include requirement/MUST %}'
MUST_DO_REPLACE = 'DO'
MUST_NOT_PATTERN = r'{% include requirement/MUSTNOT id="[a-zA-Z0-9_-]+" %}'
MUST_NOT_REPLACE = 'DO NOT'
SHOULD_PATTERN = r'{% include requirement/SHOULD id="[a-zA-Z0-9_-]+" %}'
SHOULD_NO_ID_PATTERN = r'{% include requirement/SHOULD %}'
SHOULD_REPLACE = 'YOU SHOULD'
SHOULD_NOT_PATTERN = r'{% include requirement/SHOULDNOT id="[a-zA-Z0-9_-]+" %}'
SHOULD_NOT_REPLACE = 'YOU SHOULD NOT'

# Parse the markdown file
def parse_markdown(file):
    with open(file, 'r') as f:
        md_text = f.read()
    ast = md.parse(md_text)

    paragraphs = []
    current_paragraph = ''
    in_link = False
    for node in ast:
        if node.type == 'paragraph_open':
            current_paragraph = ''
        elif node.type == 'inline':
            extracted_text = fix_tags(node, in_link)
            current_paragraph += extracted_text
        elif node.type == 'paragraph_close':
            paragraphs.append(current_paragraph)
        elif node.type == "link_open":
            in_link = True
        elif node.type == "link_close":
            in_link = False
    return paragraphs

# Remove the tags and replace them with the correct text
def fix_tags(node, in_link):
    extracted_text = extract_text_from_inline(node, in_link)
    extracted_text = re.sub(MAY_PATTERN, MAY_REPLACE, extracted_text)
    extracted_text = re.sub(MUST_DO_PATTERN, MUST_DO_REPLACE, extracted_text)
    extracted_text = re.sub(MUST_NO_ID_PATTERN, MUST_DO_REPLACE, extracted_text)
    extracted_text = re.sub(MUST_NOT_PATTERN, MUST_NOT_REPLACE, extracted_text)
    extracted_text = re.sub(SHOULD_PATTERN, SHOULD_REPLACE, extracted_text)
    extracted_text = re.sub(SHOULD_NO_ID_PATTERN, SHOULD_REPLACE, extracted_text)
    extracted_text = re.sub(SHOULD_NOT_PATTERN, SHOULD_NOT_REPLACE, extracted_text)
    return extracted_text

type_of_elements = {}

# Extract inline text from a node
def extract_text_from_inline(node, in_link):
    text = ''
    for child in node.children:
        type_of_elements[child.type] = type_of_elements.get(child.type, 0) + 1
        print(node.type + ': ' + child.type + ': ' + child.content)
        if child.type == 'text':
            text += child.content
        elif child.type == 'code_inline':
            text += child.content
        elif child.type == 'html_inline':
            text += child.content
        elif child.type == 'softbreak':
            text += ' \n'
        elif child.type == 'inline':
            text += extract_text_from_inline(child, in_link)
        elif child.type == 'link_open':
            in_link = True
        elif child.type == 'link_close':
            in_link = False
    if in_link:
        return ""
    else:
        return text


paragraphs = parse_markdown('docs/typescript/design.md')
#print(type_of_elements)
for paragraph in paragraphs:
    print(paragraph + '\n')

