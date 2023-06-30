"""
Due to token limitations, we can't send all the APIView code at once and evaluate it against all the language guidelines (at the moment).

The idea here would be that we have generated embeddings for every guideline with a code example already and have this info static in our redis vector database.
When an APIView is created, we chunk that into relevant parts (maybe classes) and generate embeddings on each chunk.
We use redis to perform a cosine similarity search on each chunk, looking for code patterns in the guidelines that match.
We take the top X results or everything above a confidence threshold and then just send the relevant pieces (code example / guideline) to GPT
and ask if it violates the guideline.
"""

import json
import os
import openai
import uuid
import numpy as np
import redis
from redis.commands.search.indexDefinition import (
    IndexDefinition,
    IndexType
)
from redis.commands.search.field import (
    TextField,
    VectorField,
)
from redis.commands.search.query import Query


def get_embedding(text, deployment_id):
    return openai.Embedding.create(input=text, deployment_id=deployment_id)['data'][0]['embedding']


# ----- CONFIG -----
openai.api_type = "azure"
openai.api_base = os.environ["OPENAI_API_BASE"]
openai.api_version = "2023-05-15"
openai.api_key = os.environ["OPENAI_API_KEY"]

INDEX_NAME = "doc-guidelines"
INDEX_PREFIX = "doc"
REDIS_HOST =  "localhost"
REDIS_PASSWORD = "" # default for passwordless Redis
REDIS_PORT = "6379"
EMBEDDINGS_MODEL = "text-embedding-ada-002"
GENERATIVE_MODEL = "gpt-4"
EMBEDDING_DIMENSION = 1536
DISTANCE_METRIC = "COSINE"


redis_index = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD
)

id = TextField(name="id")
guideline = TextField(name="guideline")
category = TextField(name="category")
text = TextField(name="text")
code_example = TextField(name="code_example")
embedding = VectorField("embedding",
    "FLAT", {
        "TYPE": "FLOAT32",
        "DIM": EMBEDDING_DIMENSION,
        "DISTANCE_METRIC": DISTANCE_METRIC,
    }
)
fields = [id, guideline, category, text, code_example, embedding]

try:
    redis_index.ft(INDEX_NAME).info()
    print("Index already exists")
except:
    redis_index.ft(INDEX_NAME).create_index(
        fields = fields,
        definition = IndexDefinition(prefix=INDEX_PREFIX, index_type=IndexType.HASH)
)

guidelines_path = os.path.join(os.path.dirname(__file__), "eventgrid.txt")
with open(guidelines_path, "r", encoding="utf-8") as fd:
    guidelines = json.loads(fd.read())

for guideline in guidelines:
    embeddings = get_embedding(guideline["code_example"], EMBEDDINGS_MODEL)
    guideline["embedding"] = np.array(embeddings).astype(dtype=np.float32).tobytes()
    redis_index.hset(INDEX_PREFIX + str(uuid.uuid4()), mapping=guideline)


# code that answer.txt uses
# code = \
# """
# class azure.eventgrid.EventGridClientSync(EventGridClientOperationsMixin): implements ContextManager

#     def __init__(
#             self,
#             **kwargs: Any
#         ) -> None
# """

apiview_path = os.path.join(os.path.dirname(__file__), "eventgrid.txt")
with open(apiview_path, "r") as f:
    apiview = f.read()

# split/chunk the APIView by class
# Note: not sure if this is the best way to chunk it
# Also this strategy is very error-prone, don't use it :)
classes = [cls for cls in apiview.split("class ") if cls.startswith("azure")]

for num, code in enumerate(classes):
    code_embedding = get_embedding(code, EMBEDDINGS_MODEL)

    TOP_K = 5

    fields = ["id", "guideline", "category", "text", "code_example", "embedding", "score"]

    base_query = f'*=>[KNN {TOP_K} @embedding $vector AS score]'
    query = (
        Query(base_query)
        .return_fields(*fields)
        .sort_by("score")
        .dialect(2)
    )
    params_dict = {"vector": np.array(code_embedding).astype(dtype=np.float32).tobytes()}
    results = redis_index.ft(INDEX_NAME).search(query, query_params=params_dict)
    # TODO we could only consider guidelines above a certain score threshold if we want

    captured_guidelines = []
    for idx, result in enumerate(results.docs):
        guideline_text = f"{idx+1}. {result['text']}\n"
        captured_guidelines.append(guideline_text)

    question = f"\n\nCODE:\n{code}\n\n####\n\nGuidelines:{''.join(captured_guidelines)}\n\n####\n\n"

    messages = [
        {
            "role": "system",
            "content": f"Given the code sample and numbered guidelines with code examples, answer if the code sample violates each guideline." \
            f"The input will be in the following format:\n\nCODE:\n<code example>\n\n####\n\nGuidelines: <guidelines>\n\n####\n\nAnswer: <answer if code sample violates guideline or \"I couldn't find the answer to that question\">\n\n" \
            f"If the code violates a guideline, suggest a way to fix the code based on what the guideline states."
        }
    ]
    messages.append({"role": "user", "content": f"{question}Answer:"})
    response = openai.ChatCompletion.create(
        messages=messages,
        deployment_id=GENERATIVE_MODEL,
        max_tokens=1000,
        temperature=0,
    )

    choices = response["choices"]
    answer = choices[0].message.content.strip()
    print(answer)
    with open(f"answer{str(num+1)}.txt", "w+") as fd:
        fd.write(answer)
