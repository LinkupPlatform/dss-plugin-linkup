# -*- coding: utf-8 -*-
import dataiku
from typing import Optional
from dataiku.customrecipe import (
    get_output_names_for_role,
    get_recipe_config,
    get_input_names_for_role,
)
from linkup import LinkupClient


def get_client(api_key: Optional[str]) -> LinkupClient:
    if api_key:
        return LinkupClient(api_key=api_key)
    return LinkupClient()


def call_client_for_query(
    client: LinkupClient,
    query: str,
    depth: str,
    output_type: str,
    structured_output_schema: str,
):
    try:
        response = client.search(
            query=query,
            depth=depth,
            output_type=output_type,
            structured_output_schema=structured_output_schema,
        )

        return response if output_type == "structured" else response.answer
    except Exception:
        return None


# ==============================================================================
# SETUP
# ==============================================================================
api_key = get_recipe_config().get("api_key")

if api_key is None or api_key == {}:
    raise ValueError("Please specify an API configuration preset")

depth = get_recipe_config().get("depth", "standard")
query_column = get_recipe_config().get("query_column", "query")
output_type = get_recipe_config().get("output_type", "sourcedAnswer")
structured_output_format = (
    ""
    if output_type == "sourcedAnswer"
    else get_recipe_config().get("structured_output_format", "")
)

input_dataset = dataiku.Dataset(get_input_names_for_role("input_dataset")[0])
output_dataset = dataiku.Dataset(get_output_names_for_role("output_dataset")[0])

df = input_dataset.get_dataframe()

if query_column not in df.columns:
    raise ValueError(f"Query column '{query_column}' not found in input dataset")

# Initialize the Linkup client
client = get_client(api_key)

# ==============================================================================
# RUN
# ==============================================================================

answers = []
for q in df[query_column].fillna(""):
    try:
        result = call_client_for_query(
            client, str(q), depth, output_type, structured_output_format
        )
        answers.append("" if result is None else str(result))
    except Exception:
        answers.append("")

output_df = df.copy()
output_df["answer"] = answers

output_dataset.write_with_schema(output_df)
