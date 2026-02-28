"""DynamoDB CRUD operations for all entities."""

import uuid
from datetime import UTC, datetime, timedelta

from app.db.dynamodb import get_table
from app.models.schemas import (
    AlertState,
    RemittanceProfile,
    Transfer,
    User,
    UserPreferences,
)


# ──── User ────


async def create_user(telegram_chat_id: str, language: str = "en") -> User:
    user = User(
        user_id=str(uuid.uuid4()),
        telegram_chat_id=telegram_chat_id,
        language=language,
    )
    table = get_table("users")
    table.put_item(Item=_serialize(user))
    return user


async def get_user_by_telegram_id(chat_id: str) -> User | None:
    table = get_table("users")
    resp = table.query(
        IndexName="telegram_chat_id-index",
        KeyConditionExpression="telegram_chat_id = :cid",
        ExpressionAttributeValues={":cid": chat_id},
    )
    items = resp.get("Items", [])
    return User(**items[0]) if items else None


async def get_user(user_id: str) -> User | None:
    table = get_table("users")
    resp = table.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    return User(**item) if item else None


async def update_user(user: User) -> None:
    table = get_table("users")
    table.put_item(Item=_serialize(user))


# ──── RemittanceProfile ────


async def create_profile(user_id: str) -> RemittanceProfile:
    profile = RemittanceProfile(
        profile_id=str(uuid.uuid4()),
        user_id=user_id,
    )
    table = get_table("remittance_profiles")
    table.put_item(Item=_serialize(profile))
    return profile


async def get_profile_by_user(user_id: str) -> RemittanceProfile | None:
    table = get_table("remittance_profiles")
    resp = table.query(
        IndexName="user_id-index",
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    items = resp.get("Items", [])
    return RemittanceProfile(**items[0]) if items else None


async def update_profile(profile: RemittanceProfile) -> None:
    table = get_table("remittance_profiles")
    table.put_item(Item=_serialize(profile))


async def delete_profile(profile_id: str) -> None:
    """Delete a remittance profile by its ID."""
    table = get_table("remittance_profiles")
    table.delete_item(Key={"profile_id": profile_id})


# ──── UserPreferences ────


async def create_preferences(user_id: str) -> UserPreferences:
    prefs = UserPreferences(user_id=user_id)
    table = get_table("user_preferences")
    table.put_item(Item=_serialize(prefs))
    return prefs


async def get_preferences(user_id: str) -> UserPreferences | None:
    table = get_table("user_preferences")
    resp = table.get_item(Key={"user_id": user_id})
    item = resp.get("Item")
    return UserPreferences(**item) if item else None


async def update_preferences(prefs: UserPreferences) -> None:
    table = get_table("user_preferences")
    table.put_item(Item=_serialize(prefs))


async def delete_preferences(user_id: str) -> None:
    """Delete user preferences by user ID."""
    table = get_table("user_preferences")
    table.delete_item(Key={"user_id": user_id})


# ──── RateSnapshot ────


async def store_rate_snapshot(snapshot_data: dict) -> str:
    snapshot_id = str(uuid.uuid4())
    snapshot_data["snapshot_id"] = snapshot_id
    snapshot_data["timestamp"] = datetime.now(UTC).isoformat()
    table = get_table("rate_snapshots")
    table.put_item(Item=snapshot_data)
    return snapshot_id


async def get_rate_snapshots(corridor: str, days: int = 14) -> list[dict]:
    table = get_table("rate_snapshots")
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    resp = table.query(
        IndexName="corridor-timestamp-index",
        KeyConditionExpression="corridor = :c AND #ts >= :cutoff",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={":c": corridor, ":cutoff": cutoff},
    )
    return resp.get("Items", [])


# ──── Transfer ────


async def create_transfer(transfer: Transfer) -> None:
    table = get_table("transfers")
    table.put_item(Item=_serialize(transfer))


async def get_transfer(transfer_id: str) -> Transfer | None:
    table = get_table("transfers")
    resp = table.get_item(Key={"transfer_id": transfer_id})
    item = resp.get("Item")
    return Transfer(**item) if item else None


async def update_transfer(transfer: Transfer) -> None:
    table = get_table("transfers")
    table.put_item(Item=_serialize(transfer))


async def get_user_transfers(user_id: str) -> list[Transfer]:
    table = get_table("transfers")
    resp = table.query(
        IndexName="user_id-created_at-index",
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    return [Transfer(**item) for item in resp.get("Items", [])]


# ──── SavingsRecord ────


async def store_savings_record(record: dict) -> None:
    table = get_table("savings_records")
    table.put_item(Item=record)


async def get_user_savings(user_id: str) -> list[dict]:
    table = get_table("savings_records")
    resp = table.query(
        IndexName="user_id-index",
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    return resp.get("Items", [])


# ──── AlertState ────


async def get_alert_state(user_id: str, corridor: str) -> AlertState | None:
    table = get_table("alert_states")
    resp = table.get_item(Key={"user_id": user_id, "corridor": corridor})
    item = resp.get("Item")
    return AlertState(**item) if item else None


async def update_alert_state(state: AlertState) -> None:
    table = get_table("alert_states")
    table.put_item(Item=_serialize(state))


async def delete_alert_states(user_id: str) -> None:
    """Delete all alert states for a user."""
    table = get_table("alert_states")
    resp = table.scan(
        FilterExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    for item in resp.get("Items", []):
        table.delete_item(Key={"user_id": item["user_id"], "corridor": item["corridor"]})


async def mark_user_interaction(user_id: str) -> None:
    """Mark that the user has interacted, resetting alert cadence for all corridors."""
    table = get_table("alert_states")
    # Scan for all alert states for this user
    resp = table.scan(
        FilterExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    for item in resp.get("Items", []):
        state = AlertState(**item)
        state.user_interacted_since_alert = True
        table.put_item(Item=_serialize(state))


# ──── Active Corridors ────


async def get_all_active_corridors() -> list[dict]:
    """Get all active user corridors for rate monitoring."""
    table = get_table("remittance_profiles")
    resp = table.scan()
    profiles = resp.get("Items", [])
    corridors = {}
    for p in profiles:
        corridor = p.get("corridor")
        if corridor and corridor not in corridors:
            corridors[corridor] = {
                "corridor": corridor,
                "sender_country": p.get("sender_country", ""),
                "recipient_country": p.get("recipient_country", ""),
                "average_amount": float(p.get("average_amount", 0)),
            }
    return list(corridors.values())


# ──── Helpers ────


def _serialize(model) -> dict:
    """Convert Pydantic model to DynamoDB-safe dict."""
    data = model.model_dump()
    for key, val in data.items():
        if isinstance(val, datetime):
            data[key] = val.isoformat()
        elif isinstance(val, float):
            data[key] = str(val)  # DynamoDB prefers Decimal, use string for simplicity
    return data
