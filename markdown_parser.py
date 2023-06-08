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
def parse_markdown(file) -> List[dict]:
    with open(file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    entries = []
    html = md.render(md_text)
    soup = BeautifulSoup(html, features="html.parser")

    for item in soup.find_all():
        if item.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            category = item.text
        if item.name == 'p':
            text, id = split_tags(item.text)
            text = add_links(text, item)
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
def split_tags(text) -> Tuple[str, Optional[str]]:
    id = extract_id_from_inline(text)
    text = re.sub(MAY_PATTERN, MAY_REPLACE, text)
    text = re.sub(MUST_DO_PATTERN, MUST_DO_REPLACE, text)
    text = re.sub(MUST_NO_ID_PATTERN, MUST_DO_REPLACE, text)
    text = re.sub(MUST_NOT_PATTERN, MUST_NOT_REPLACE, text)
    text = re.sub(SHOULD_PATTERN, SHOULD_REPLACE, text)
    text = re.sub(SHOULD_NO_ID_PATTERN, SHOULD_REPLACE, text)
    text = re.sub(SHOULD_NOT_PATTERN, SHOULD_NOT_REPLACE, text)
    return text, id

# Extract the id from the inline text
def extract_id_from_inline(text):
    id = re.search(r'id="([a-zA-Z0-9_-]+)"', text)
    if id:
        return id.group(1)
    else:
        return None


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
