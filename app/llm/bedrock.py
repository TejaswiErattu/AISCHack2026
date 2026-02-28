"""AWS Bedrock client wrapper for RemitAgent LLM calls."""

import asyncio
import json
import logging

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """Thin wrapper around AWS Bedrock Runtime for Claude model invocations."""

    def __init__(self) -> None:
        client_kwargs: dict = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        self._client = boto3.client("bedrock-runtime", **client_kwargs)
        self._model_id = settings.bedrock_model_id

    def _build_request_body(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Build the Anthropic Messages API request body for Bedrock."""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message},
            ],
        }
        return json.dumps(body)

    def _invoke_sync(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Synchronous Bedrock invoke_model call.

        Separated so it can be dispatched to a thread via asyncio.to_thread.
        """
        body = self._build_request_body(
            system_prompt, user_message, max_tokens, temperature
        )

        response = self._client.invoke_model(
            modelId=self._model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        # Anthropic Messages API returns content as a list of blocks.
        content_blocks = response_body.get("content", [])
        text_parts = [
            block["text"] for block in content_blocks if block.get("type") == "text"
        ]
        return "".join(text_parts)

    async def invoke(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
    ) -> str:
        """Invoke Claude via Bedrock for general-purpose generation.

        Uses asyncio.to_thread because boto3 is synchronous.
        Returns an empty string on any failure so callers can fall back
        to template-based responses.
        """
        try:
            return await asyncio.to_thread(
                self._invoke_sync,
                system_prompt,
                user_message,
                max_tokens,
                temperature=0.7,
            )
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "ThrottlingException":
                logger.warning("Bedrock throttling encountered: %s", exc)
            elif error_code == "ModelTimeoutException":
                logger.warning("Bedrock model timeout: %s", exc)
            else:
                logger.error("Bedrock client error (%s): %s", error_code, exc)
            return ""
        except Exception:
            logger.exception("Unexpected error invoking Bedrock model")
            return ""

    async def extract_structured(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 512,
    ) -> str:
        """Invoke Claude with low temperature for structured data extraction.

        Identical contract to ``invoke`` but uses temperature=0.0 to
        encourage deterministic, parseable output.
        """
        try:
            return await asyncio.to_thread(
                self._invoke_sync,
                system_prompt,
                user_message,
                max_tokens,
                temperature=0.0,
            )
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "ThrottlingException":
                logger.warning("Bedrock throttling (structured extraction): %s", exc)
            elif error_code == "ModelTimeoutException":
                logger.warning("Bedrock timeout (structured extraction): %s", exc)
            else:
                logger.error(
                    "Bedrock client error (structured extraction, %s): %s",
                    error_code,
                    exc,
                )
            return ""
        except Exception:
            logger.exception(
                "Unexpected error during Bedrock structured extraction"
            )
            return ""
