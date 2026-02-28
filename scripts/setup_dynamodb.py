"""Provision all DynamoDB tables required by RemitAgent.

Run with:
    python -m scripts.setup_dynamodb
"""

import boto3
from botocore.exceptions import ClientError

from app.config import settings

# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------
# Each entry defines the table's logical name, key schema, attribute
# definitions, and optional GSIs.  All tables use PAY_PER_REQUEST billing.
# ---------------------------------------------------------------------------

TABLE_DEFINITIONS: list[dict] = [
    {
        "name": "users",
        "key_schema": [
            {"AttributeName": "user_id", "KeyType": "HASH"},
        ],
        "attribute_definitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "telegram_chat_id", "AttributeType": "S"},
        ],
        "gsis": [
            {
                "IndexName": "telegram_chat_id-index",
                "KeySchema": [
                    {"AttributeName": "telegram_chat_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "remittance_profiles",
        "key_schema": [
            {"AttributeName": "profile_id", "KeyType": "HASH"},
        ],
        "attribute_definitions": [
            {"AttributeName": "profile_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "gsis": [
            {
                "IndexName": "user_id-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "user_preferences",
        "key_schema": [
            {"AttributeName": "user_id", "KeyType": "HASH"},
        ],
        "attribute_definitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "gsis": [],
    },
    {
        "name": "rate_snapshots",
        "key_schema": [
            {"AttributeName": "snapshot_id", "KeyType": "HASH"},
        ],
        "attribute_definitions": [
            {"AttributeName": "snapshot_id", "AttributeType": "S"},
            {"AttributeName": "corridor", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "S"},
        ],
        "gsis": [
            {
                "IndexName": "corridor-timestamp-index",
                "KeySchema": [
                    {"AttributeName": "corridor", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "transfers",
        "key_schema": [
            {"AttributeName": "transfer_id", "KeyType": "HASH"},
        ],
        "attribute_definitions": [
            {"AttributeName": "transfer_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        "gsis": [
            {
                "IndexName": "user_id-created_at-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "savings_records",
        "key_schema": [
            {"AttributeName": "transfer_id", "KeyType": "HASH"},
        ],
        "attribute_definitions": [
            {"AttributeName": "transfer_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        "gsis": [
            {
                "IndexName": "user_id-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
    {
        "name": "alert_states",
        "key_schema": [
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "corridor", "KeyType": "RANGE"},
        ],
        "attribute_definitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "corridor", "AttributeType": "S"},
        ],
        "gsis": [],
    },
]


def _get_dynamodb_client():
    """Return a low-level DynamoDB client respecting local dev settings."""
    kwargs: dict = {"region_name": settings.aws_region}
    if settings.dynamodb_endpoint_url:
        kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    return boto3.client("dynamodb", **kwargs)


def create_table(client, table_def: dict) -> None:
    """Create a single DynamoDB table from its definition dict."""
    table_name = settings.table_name(table_def["name"])

    create_kwargs: dict = {
        "TableName": table_name,
        "KeySchema": table_def["key_schema"],
        "AttributeDefinitions": table_def["attribute_definitions"],
        "BillingMode": "PAY_PER_REQUEST",
    }

    if table_def.get("gsis"):
        create_kwargs["GlobalSecondaryIndexes"] = table_def["gsis"]

    try:
        client.create_table(**create_kwargs)
        print(f"  [CREATED]  {table_name}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  [EXISTS]   {table_name}")
        else:
            raise


def main() -> None:
    """Provision all RemitAgent DynamoDB tables."""
    print("Provisioning DynamoDB tables ...")
    print(f"  Region:   {settings.aws_region}")
    print(f"  Endpoint: {settings.dynamodb_endpoint_url or '(default AWS)'}")
    print(f"  Prefix:   {settings.dynamodb_table_prefix}")
    print()

    client = _get_dynamodb_client()

    for table_def in TABLE_DEFINITIONS:
        create_table(client, table_def)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
