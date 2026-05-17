from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agents.openai_client import OpenAIClientError, OpenAIClientTimeoutError
from app.agents.query_agent import QueryAgentLowConfidenceError, QueryAgentResponseError
from app.config import ConfigurationError, get_settings
from app.duckdb_layer.query_runner import (
    EmptyQueryResultError,
    InvalidQueryError,
    MissingDataFileError,
)
from app.ask_service import (
    DestructiveIntentError,
    answer_question,
)
from app.schemas.api import AskRequest, AskResponse, HealthResponse

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        app_name=settings.app_name,
        status="ok",
        environment=settings.app_env,
    )


@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    try:
        return answer_question(request)
    except MissingDataFileError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except EmptyQueryResultError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidQueryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except QueryAgentLowConfidenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except QueryAgentResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except OpenAIClientTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except OpenAIClientError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ConfigurationError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except DestructiveIntentError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
