from collections.abc import Sequence

from openai import APITimeoutError, OpenAI, OpenAIError

from app.config import ConfigurationError, get_settings


class OpenAIClientError(RuntimeError):
    pass


class OpenAIClientTimeoutError(OpenAIClientError):
    pass


def create_chat_completion(messages: Sequence[dict[str, str]]) -> str:
    settings = get_settings()

    if not settings.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY is required for OpenAI calls.")

    client = OpenAI(api_key=settings.openai_api_key)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=list(messages),
            temperature=0,
            timeout=30,
        )
    except APITimeoutError as error:
        raise OpenAIClientTimeoutError("OpenAI request timed out.") from error
    except OpenAIError as error:
        raise OpenAIClientError(f"OpenAI request failed: {error}") from error

    content = response.choices[0].message.content

    if not content:
        raise OpenAIClientError("OpenAI returned an empty response.")

    return content
