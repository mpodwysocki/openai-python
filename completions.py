#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

from dotenv import load_dotenv
import os
import openai

# Load from the environment
load_dotenv()

organization = os.environ['OPENAI_API_ORGANIZATION']
api_key = os.environ['OPENAI_API_KEY']

openai.organization = organization
openai.api_key = api_key

def code_snippet_summary(language, code_snippet):
    prompt = f'''
Summarize the following code snippet in {language}:

```
{code_snippet}
```
'''
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.1,
        max_tokens=400,
        n=1,
        stop=None,
    )

    return response

# Check for code snippets against the design guidelines at the following URL
def check_code_against_guidelines(language, code_snippet, url):
    prompt = f"""
Given the {language} design guidelines at this URL: {url}

Does the following code violate any of the rules and which one?  Keep the response under 1,000 characters.

{code_snippet}
"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.1,
        max_tokens=400,
        n=1,
        stop=None,
    )

    return response

def check_for_breaking_changes(code_snippet, previous_code_snippet):
    prompt = f"""
Given the following code:
{code_snippet}

Does the signature break from the previous version of the code here:
{previous_code_snippet}

Please keep the response under 1,000 characters.
"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=1,
        max_tokens=400,
        n=1,
        stop=None,
    )

    return response

def explain_code_deltas(code_snippet, previous_code_snippet):
    prompt = f"""
Given the following code:
{code_snippet}

Explain the differences between this code and the previous version of the code here:
{previous_code_snippet}
"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.1,
        max_tokens=400,
        n=1,
        stop=None,
    )

    return response
