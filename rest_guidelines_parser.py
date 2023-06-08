#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from bs4 import BeautifulSoup
import json
import markdown_it
import re
import sys
from typing import List, Optional, Tuple

# Create a new MarkdownIt instance
md = markdown_it.MarkdownIt()

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

ICON_PATTERN = r'^:[a-z_]+: '
ICON_REPLACE = ''

# Parse the markdown file
def parse_markdown(file) -> List[dict]:
    with open(file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    entries = []
    html = md.render(md_text)
    soup = BeautifulSoup(html, features="html.parser")

    for item in soup.find_all():
        if item.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            category = item.text
        # Skip the explanations of rule types in introduction section
        if category == 'Prescriptive Guidance':
            continue
        if item.name == 'p':
            id = extract_id(item)
            text = extract_text(item.text)
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
            items = [li.text for li in item.find_all('li')]
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
def extract_text(text) -> str:
    text = re.sub(MAY_PATTERN, MAY_REPLACE, text)
    text = re.sub(MUST_DO_PATTERN, MUST_DO_REPLACE, text)
    text = re.sub(MUST_NO_ID_PATTERN, MUST_DO_REPLACE, text)
    text = re.sub(MUST_NOT_PATTERN, MUST_NOT_REPLACE, text)
    text = re.sub(SHOULD_PATTERN, SHOULD_REPLACE, text)
    text = re.sub(SHOULD_NO_ID_PATTERN, SHOULD_REPLACE, text)
    text = re.sub(SHOULD_NOT_PATTERN, SHOULD_NOT_REPLACE, text)
    text = re.sub(ICON_PATTERN, ICON_REPLACE, text)
    return text

# Extract the id from the inline text
def extract_id(item) -> Optional[str]:
    id = re.search(r'id="([a-zA-Z0-9_-]+)"', item.text)
    if id:
        return id.group(1)
    try:
        id = item.next_element.attrs['name']
    except:
        id = None
    return id

if __name__ == "__main__":
    try:
        file_path = sys.argv[1]
    except IndexError:
        print("Please provide a file path")
        sys.exit(1)

    results = parse_markdown(file_path)
    json_str = json.dumps(results, indent=2)
    outfile_path = file_path.replace('.md', '.json')
    with open(outfile_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
