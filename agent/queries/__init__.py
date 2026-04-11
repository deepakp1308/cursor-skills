"""BigQuery SQL query modules for the MC Everywhere Analyzer Agent."""

from google.cloud import bigquery


def run_query(sql: str, client: bigquery.Client | None = None) -> list[dict]:
    if client is None:
        client = bigquery.Client()
    rows = client.query(sql).result()
    return [dict(row) for row in rows]
