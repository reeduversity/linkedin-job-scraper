from __future__ import annotations

from datetime import timedelta
from typing import Any

import requests
from apify_client import ApifyClient as ApifySDKClient
from apify_client.errors import ApifyApiError, ApifyClientError, RateLimitError, UnauthorizedError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings
from app.config_validator import ConfigurationError


class ApifyConfigurationError(ConfigurationError):
    """Raised when the Apify configuration is invalid."""


class ApifyAuthenticationError(ApifyConfigurationError):
    """Raised when the Apify token cannot authenticate the request."""


class ApifyRuntimeError(RuntimeError):
    """Raised when the Apify actor request fails."""


class ApifyTimeoutError(ApifyRuntimeError):
    """Raised when the Apify call exceeds the configured timeout."""


class ApifyNetworkError(ApifyRuntimeError):
    """Raised when the network layer fails while calling Apify."""


class ApifyRateLimitError(ApifyRuntimeError):
    """Raised when Apify responds with a rate-limit error."""


class ApifyUnexpectedError(ApifyRuntimeError):
    """Raised when an unexpected error is returned by Apify."""


class ApifyClient:
    """Reusable client wrapper around the Apify SDK."""

    def __init__(self, token: str | None = None, actor_id: str | None = None) -> None:
        self.token = token or settings.apify_api_token
        self.actor_id = actor_id or settings.apify_actor_id
        if not self.token:
            raise ApifyConfigurationError("APIFY_TOKEN is required")
        if not self.actor_id:
            raise ApifyConfigurationError("APIFY_ACTOR_ID is required")
        self._client = ApifySDKClient(self.token)

    def verify_token(self) -> None:
        try:
            self._client.user().get()
        except UnauthorizedError as exc:
            raise ApifyAuthenticationError(f"Authentication failed for token: {exc}") from exc
        except (requests.exceptions.Timeout, TimeoutError) as exc:
            raise ApifyTimeoutError(f"Timed out while verifying Apify token: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise ApifyNetworkError(f"Network error while verifying Apify token: {exc}") from exc
        except RateLimitError as exc:
            raise ApifyRateLimitError(f"Apify rate limit exceeded while verifying token: {exc}") from exc
        except ApifyApiError as exc:
            raise ApifyUnexpectedError(f"Unexpected Apify API error while verifying token: {exc}") from exc
        except ApifyClientError as exc:
            raise ApifyUnexpectedError(f"Unexpected Apify client error while verifying token: {exc}") from exc

    def verify_actor(self) -> None:
        try:
            actor = self._client.actor(self.actor_id).get()
        except UnauthorizedError as exc:
            raise ApifyAuthenticationError(f"Authentication failed for actor '{self.actor_id}': {exc}") from exc
        except (requests.exceptions.Timeout, TimeoutError) as exc:
            raise ApifyTimeoutError(f"Timed out while verifying actor '{self.actor_id}': {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise ApifyNetworkError(f"Network error while verifying actor '{self.actor_id}': {exc}") from exc
        except RateLimitError as exc:
            raise ApifyRateLimitError(f"Apify rate limit exceeded while verifying actor '{self.actor_id}': {exc}") from exc
        except ApifyApiError as exc:
            raise ApifyUnexpectedError(f"Unexpected Apify API error while verifying actor '{self.actor_id}': {exc}") from exc
        except ApifyClientError as exc:
            raise ApifyUnexpectedError(f"Unexpected Apify client error while verifying actor '{self.actor_id}': {exc}") from exc
        if actor is None:
            raise ApifyConfigurationError(f"Actor '{self.actor_id}' could not be resolved")

    @retry(
        retry=retry_if_exception(lambda exc: isinstance(exc, (ApifyTimeoutError, ApifyNetworkError, ApifyRateLimitError))),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def run_actor(self, input_data: dict[str, Any] | None = None, *, timeout: int | None = None) -> list[dict[str, Any]]:
        self.verify_token()
        self.verify_actor()
        try:
            timeout_seconds = timeout if timeout is not None else 120
            run = self._client.actor(self.actor_id).call(run_input=input_data or {}, timeout=timedelta(seconds=timeout_seconds))
            dataset_id = self._get_dataset_id(run)
            if not dataset_id:
                raise ApifyUnexpectedError("Apify actor returned no dataset identifier")
            items = list(self._client.dataset(dataset_id).iterate_items())
            return items
        except UnauthorizedError as exc:
            raise ApifyAuthenticationError(f"Authentication failed while running actor '{self.actor_id}': {exc}") from exc
        except (requests.exceptions.Timeout, TimeoutError) as exc:
            raise ApifyTimeoutError(f"Timed out while running actor '{self.actor_id}': {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise ApifyNetworkError(f"Network error while running actor '{self.actor_id}': {exc}") from exc
        except RateLimitError as exc:
            raise ApifyRateLimitError(f"Apify rate limit exceeded while running actor '{self.actor_id}': {exc}") from exc
        except ApifyApiError as exc:
            raise ApifyUnexpectedError(f"Unexpected Apify API error while running actor '{self.actor_id}': {exc}") from exc
        except ApifyClientError as exc:
            raise ApifyUnexpectedError(f"Unexpected Apify client error while running actor '{self.actor_id}': {exc}") from exc

    def _get_dataset_id(self, run: Any) -> str | None:
        if isinstance(run, dict):
            for key in ("defaultDatasetId", "defaultDatasetID", "default_dataset_id", "datasetId"):
                value = run.get(key)
                if value:
                    return str(value)
            return None
        for key in ("defaultDatasetId", "defaultDatasetID", "default_dataset_id", "datasetId"):
            value = getattr(run, key, None)
            if value:
                return str(value)
        return None
