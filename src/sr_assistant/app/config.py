from __future__ import annotations

import functools
import typing as t

import streamlit as st
from pydantic import (
    Field,
)
from pydantic.networks import EmailStr, PostgresDsn  # noqa: TC002
from pydantic.types import SecretStr  # noqa: TC002
from pydantic_settings import BaseSettings, SettingsConfigDict

import sr_assistant.app.utils as ut
from sr_assistant.core.types import LogLevel


class Settings(BaseSettings):
    """Application settings.

    These are loaded from environment variables. Can be prefixed with SRA_ or sra_.

    # TODO: add types and defaults
    Attributes:
        OPENAI_API_KEY (str): OpenAI API key, from OPENAI_API_KEY env var or APIKEY
        ANTHROPIC_API_KEY (str): Anthropic API key
        SUPABASE_URL (str): Supabase URL
        SUPABASE_KEY (str): Supabase service role key
        DATABASE_URL (PostgresDsn): Database URL
        IN_STREAMLIT (bool, optional): Whether we're executed via streamlit run or not.
            Defaults to checking st context of main thread.
        NCBI_EMAIL (str): NCBI email
        NCBI_API_KEY (str): NCBI API key
        LOG_LEVEL (str): Log level
        env: t.Literal["local", "test", "prototype"] = Field(
            default="prototype",
            validation_alias="environment",
            description="Environment to run in (local, test, prototype). test is for integration tests and uses test SupaBase DB.",
        )
        debug: bool = Field(default=False, validation_alias="debug")
    """

    model_config: t.ClassVar[SettingsConfigDict] = {
        "env_prefix": "sra_",
        "env_file": (
            ".env",
            ".env.local",  # takes priority over .env
        ),
        "extra": "ignore",
    }

    OPENAI_API_KEY: SecretStr = Field(validation_alias="openai_api_key")

    ANTHROPIC_API_KEY: SecretStr = Field(  # pyright: ignore [reportAssignmentType]
        default="",
        validation_alias="anthropic_api_key",
        description="Optional Anthropic API key, not used in proto ATM",
    )
    """Not used."""

    SUPABASE_URL: str = Field(validation_alias="sra_supabase_url")
    SUPABASE_KEY: SecretStr = Field(
        validation_alias="sra_supabase_service_role_key"
    )  # TODO: only for local proto, this should never be exposed client side
    SUPABASE_DIRECT_URL: PostgresDsn = Field(
        default="postgresql://postgres:postgres@127.0.0.1:54322/postgres",  # pyright: ignore [reportAssignmentType]
        validation_alias="sra_supabase_direct_url",
    )
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://postgres:postgres@127.0.0.1:54322/postgres",  # pyright: ignore [reportAssignmentType]
        description="For test and prototype envs this should be a `postgresql+psycopg:// useing pooled SupaBase DSN.",
        validation_alias="database_url",
    )
    """For test and prototype envs this should be a `postgresql+psycopg:// useing pooled SupaBase DSN."""

    NCBI_EMAIL: EmailStr = Field(validation_alias="ncbi_email")
    """NCBI email. From NCBI_EMAIL env var."""
    NCBI_API_KEY: SecretStr = Field(validation_alias="ncbi_api_key")
    """NCBI API key. From NCBI_API_KEY env var."""

    IN_STREAMLIT: bool = Field(
        description="Whether we're executed via streamlit run or not.",
        default_factory=ut.in_streamlit,
        validation_alias="in_streamlit",
    )
    """Whether we're executed via streamlit run or not."""

    # TODO: implement debug logging
    debug: bool = Field(
        default=False,
        description="Enable debug mode in app and asyncio, LangChain, etc. NOTE: logs variable values, do not use in production.",
    )
    """Currently doesn't do anything, just a placeholder for future use."""

    log_level: LogLevel = Field(default=LogLevel.DEBUG)

    env: t.Literal["local", "test", "prototype"] = Field(
        default="prototype",
        validation_alias="environment",
        description="Environment to run in (local, test, prototype). test is for integration tests and uses test SupaBase DB.",
    )
    """Read from SRA_ENV or ENVIRONMENT environment variable."""


_cache_fn = st.cache_data if ut.in_streamlit() else functools.cache


@_cache_fn
def get_settings() -> Settings:
    return Settings()  # pyright: ignore [reportCallIssue]
