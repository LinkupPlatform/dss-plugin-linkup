# -*- coding: utf-8 -*-
import dataiku
from typing import Optional
from dataiku.customrecipe import (
    get_output_names_for_role,
    get_recipe_config,
    get_input_names_for_role,
)
from linkup import LinkupClient


def _get_client(api_key: Optional[str]) -> LinkupClient:
    if api_key:
        return LinkupClient(api_key=api_key)
    return LinkupClient()


def _call_client_for_query(client: LinkupClient, query: str, depth: str):
    try:
        response = client.search(
            query=query,
            depth=depth,
            output_type="sourcedAnswer",
        )

        return response.answer
    except Exception:
        return None
    return None


input_dataset = dataiku.Dataset(get_input_names_for_role("input_dataset")[0])
output_dataset = dataiku.Dataset(get_output_names_for_role("output_dataset")[0])

config = get_recipe_config()
depth = config.get("depth", "standard")
query_column = config.get("query_column", "query")
api_key = (config.get("api_key") or "").strip() or None

client = _get_client(api_key)

df = input_dataset.get_dataframe()

if query_column not in df.columns:
    raise ValueError(f"Query column '{query_column}' not found in input dataset")

answers = []
for q in df[query_column].fillna(""):
    try:
        result = _call_client_for_query(client, str(q), depth)
        answers.append("" if result is None else str(result))
    except Exception:
        answers.append("")

output_df = df.copy()
output_df["answer"] = answers

output_dataset.write_with_schema(output_df)
