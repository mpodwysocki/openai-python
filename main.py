#!/usr/bin/env python3

# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from openai_trainer import check_code_against_guidelines, check_for_breaking_changes, explain_code_deltas

# Paths of documents
design_url = 'https://azure.github.io/azure-sdk/typescript_design.html'

# Get the paragraphs from the markdown files

code_snippet = '''
class ExampleClient {
  constructor (connectionString: string, options: ExampleClientOptions);
  constructor (url: string, options: ExampleClientOptions);
  constructor (urlOrCS: string, options: ExampleClientOptions) {
    // have to dig into the first parameter to see whether its
    // a url or a connection string. Not ideal.
  }
}
'''

response = check_code_against_guidelines('TypeScript', code_snippet, design_url)
print(response)

before_code_snippet = '''
class ExampleClient {
  constructor (connectionString: string, options: ExampleClientOptions);
  constructor (url: string, options: ExampleClientOptions);
  constructor (urlOrCS: string, options: ExampleClientOptions) {
    // have to dig into the first parameter to see whether its
    // a url or a connection string. Not ideal.
  }
}
'''

after_code_snippet = '''
class ExampleClient {
  constructor (url: string, options: ExampleClientOptions) {

  }

  static fromConnectionString(connectionString: string, options: ExampleClientOptions) {

  }
}
'''

response = check_for_breaking_changes(after_code_snippet, before_code_snippet)
print(response)

response = explain_code_deltas(after_code_snippet, before_code_snippet)
print(response)
