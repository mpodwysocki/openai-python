#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

import dotenv
from bs4 import BeautifulSoup
import json
import markdown_it
import os
import re
import sys
from typing import List, Optional, Tuple

dotenv.load_dotenv()

# Create a new MarkdownIt instance
md = markdown_it.MarkdownIt()

# API Doc Constants
MAY_PATTERN = r'{% include requirement/MAY\s*id=\\?"[a-zA-Z0-9_-]+\\?" %}'
MAY_REPLACE = 'YOU MAY'
MUST_DO_PATTERN = r'{% include requirement/MUST\s*id=\\?"[a-zA-Z0-9_-]+\\?" %}'
MUST_NO_ID_PATTERN = r'{% include requirement/MUST %}'
MUST_DO_REPLACE = 'DO'
MUST_NOT_PATTERN = r'{% include requirement/MUSTNOT\s*id=\\?"[a-zA-Z0-9_-]+\\?" %}'
MUST_NOT_REPLACE = 'DO NOT'
SHOULD_PATTERN = r'{% include requirement/SHOULD\s*id=\\?"[a-zA-Z0-9_-]+\\?" %}'
SHOULD_NO_ID_PATTERN = r'{% include requirement/SHOULD %}'
SHOULD_REPLACE = 'YOU SHOULD'
SHOULD_NOT_PATTERN = r'{% include requirement/SHOULDNOT\s*id=\\?"[a-zA-Z0-9_-]+\\?" %}'
SHOULD_NOT_REPLACE = 'YOU SHOULD NOT'
INCLUDE_PATTERN = r'{%\s*(include|include_relative)\s*([^\s%}]+)\s*%}'

ICON_PATTERN = r'^:[a-z_]+: '
ICON_REPLACE = ''


def add_links(text, item):
    """Find any links associated with the text and add them in format: text (link)
    """
    links = [link for link in item.find_all("a") if link.get("href", "").startswith("http")]
    if not links:
        return text

    for link in links:
        index = text.find(link.text)
        if index == -1:
            continue
        text = f"{text[:index]}{link.text} ({link['href']}) {text[len(link.text)+1 + index:]}"
    return text


# Parse the markdown file
def parse_markdown(file, root_path) -> List[dict]:
    with open(file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    entries = []
    html = md.render(md_text)
    soup = BeautifulSoup(html, features="html.parser")
    category = None

    for item in soup.find_all():
        if item.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            category = item.text
        # Skip the explanations of rule types in introduction section
        if category == 'Prescriptive Guidance':
            continue

        if item.name == 'p':
            text, id = split_tags(item)
            text = add_links(text, item)
            text = expand_include_tags(text, root_path, os.path.dirname(file))

            if id:
                entries.append({
                    'id': id,
                    'category': category,
                    'text': text,
                })
            else:
                try:
                    entries[-1]['text'] += '\n\n' + text
                except IndexError:
                    continue
        elif item.name in ['ol', 'ul']:
            items = [add_links(li.text, li) for li in item.find_all('li')]
            try:
                entries[-1]['text'] += '\n' + '\n'.join(items)
            except IndexError:
                continue
        elif item.name == "pre":
            raw_html = ''.join(str(tag) for tag in item.contents)
            markdown_text = convert_code_tag_to_markdown(raw_html)
            try:
                entries[-1]['text'] += '\n\n' + markdown_text
            except IndexError:
                continue
        else:
            continue
    return entries


def expand_include_tags(text, root_path, rel_path) -> str:
    matches = re.findall(INCLUDE_PATTERN, text)
    if not matches:
        return text
    for match in matches:
        include_tag = match[0]
        include_path = match[1]
        if include_tag == 'include_relative':
            include_path = os.path.join(rel_path, include_path)
            with open(include_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            include_path = os.path.join(root_path, "_includes", include_path)
            with open(include_path, 'r', encoding='utf-8') as f:
                text = f.read()
    # if text looks like html, convert it to markdown
    if text.startswith('<'):
        return convert_html_to_markdown(text)
    else:
        return text

def convert_html_to_markdown(html) -> str:
    # convert HTML text to markdown
    markdown = md.render(html)
    return markdown

def convert_code_tag_to_markdown(html):
    # Define the regular expression to match the code tag
    code_tag_pattern = r'<code class="language-(.+)">([\s\S]*?)</code>'

    match = re.search(code_tag_pattern, html)
    if match:
        language = match[1]
        code = match[2]
        markdown = f'```{language}\n{code}\n```'
        return markdown
    else:
        return html
 
# Split the tag from the ID
def split_tags(item) -> Tuple[str, Optional[str]]:
    text = item.text
    id = extract_id_from_inline(item)
    text = re.sub(MAY_PATTERN, MAY_REPLACE, text)
    text = re.sub(MUST_DO_PATTERN, MUST_DO_REPLACE, text)
    text = re.sub(MUST_NO_ID_PATTERN, MUST_DO_REPLACE, text)
    text = re.sub(MUST_NOT_PATTERN, MUST_NOT_REPLACE, text)
    text = re.sub(SHOULD_PATTERN, SHOULD_REPLACE, text)
    text = re.sub(SHOULD_NO_ID_PATTERN, SHOULD_REPLACE, text)
    text = re.sub(SHOULD_NOT_PATTERN, SHOULD_NOT_REPLACE, text)
    text = re.sub(ICON_PATTERN, ICON_REPLACE, text)
    return text, id

# Extract the id from the inline text
def extract_id_from_inline(item):
    id = re.search(r'id="([a-zA-Z0-9_-]+)"', item.text)
    if id:
        return id.group(1)
    try:
        id = item.next_element.attrs["name"]
    except:
        id = None
    return id


def clean_text(results):
    for result in results:
        result["text"] = result["text"].replace("\n", " ").replace("TODO", "").replace("  ", " ")
    return results


if __name__ == "__main__":

    azure_sdk_path = os.getenv('AZURE_SDK_REPO_PATH')
    rest_api_guidelines_path = os.getenv('REST_API_GUIDELINES_PATH')
    if not azure_sdk_path:
        raise Exception('Please set the AZURE_SDK_REPO_PATH environment variable manually or in your .env file.')
    if not rest_api_guidelines_path:
        raise Exception('Please set the REST_API_GUIDELINES_PATH environment variable manually or in your .env file.')
    
    repo_root = os.path.dirname(os.path.abspath(__file__))
    
    # Generate Azure SDK JSON
    sdk_folders_to_parse = ["android", "clang", "cpp", "dotnet", "general", "golang", "ios", "java", "python", "typescript"]
    files_to_parse = ["design.md", "implementation.md", "introduction.md", "azurecore.md", "compatibility.md", "documentation.md", "spring.md"]
    for folder in sdk_folders_to_parse:
        for root, dirs, files in os.walk(os.path.join(azure_sdk_path, "docs", folder)):
            for file in files:
                if file in files_to_parse:
                    file_path = os.path.join(root, file)
                    results = parse_markdown(file_path, azure_sdk_path)
                    results = clean_text(results)
                    json_str = json.dumps(results, indent=2)
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    json_filename = filename + ".json"                
                    json_path = os.path.join(repo_root, "docs", folder, json_filename)
                    os.makedirs(os.path.dirname(json_path), exist_ok=True)
                    with open(json_path, 'w') as f:
                        f.write(json_str)
    # Generate the REST API Guidelines JSON
    guidelines_path = os.path.join(rest_api_guidelines_path, "azure", "Guidelines.md")
    results = parse_markdown(guidelines_path, rest_api_guidelines_path)
    results = clean_text(results)
    json_path = os.path.join(repo_root, "docs", "rest", "guidelines.json")
    json_str = json.dumps(results, indent=2)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w') as f:
        f.write(json_str)
