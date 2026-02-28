"""DynamoDB client wrapper and table access for RemitAgent."""

import boto3
from boto3.dynamodb.table import TableResource

from app.config import settings

_dynamodb_resource = None


def get_dynamodb_resource():
    """Return a boto3 DynamoDB resource, reusing a cached instance.

    Supports ``settings.dynamodb_endpoint_url`` so local DynamoDB (e.g.
    DynamoDB Local or LocalStack) works transparently during development.
    """
    global _dynamodb_resource
    if _dynamodb_resource is None:
        kwargs: dict = {"region_name": settings.aws_region}
        if settings.dynamodb_endpoint_url:
            kwargs["endpoint_url"] = settings.dynamodb_endpoint_url
        _dynamodb_resource = boto3.resource("dynamodb", **kwargs)
    return _dynamodb_resource


def get_table(name: str) -> TableResource:
    """Return a DynamoDB Table reference for the given logical table name.

    The physical table name is derived via ``settings.table_name(name)`` which
    applies the configured prefix (e.g. ``remit_users``).
    """
    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(settings.table_name(name))
