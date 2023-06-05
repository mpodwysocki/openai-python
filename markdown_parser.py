#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from bs4 import BeautifulSoup
import json
import markdown
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

# Parse the markdown file
def parse_markdown(file) -> List[dict]:
    with open(file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    entries = []

    html = markdown.markdown(md_text)
    soup = BeautifulSoup(html, features="html.parser")
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        category = header.text

        for sibling in header.find_next_siblings(['p', 'ul', 'ol']):
            if sibling.name == 'p':
                text, id = split_tags(sibling.text)
                entries.append({
                    'id': id,
                    'category': category,
                    'text': text,
                })
            else:  # sibling is a list
                items = [li.text for li in sibling.find_all('li')]
                entries[-1]['text'] += '\n' + '\n'.join(items)
    return entries

 
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
