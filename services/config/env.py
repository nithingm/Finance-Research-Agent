from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class SECConfig:
    user_agent: str


def get_sec_config() -> SECConfig:
    ua = os.getenv("SEC_USER_AGENT", "FinanceResearchAgent/0.1 (contact@example.com)")
    return SECConfig(user_agent=ua)


@dataclass(frozen=True)
class MarketConfig:
    alpha_vantage_key: str | None = None


def get_market_config() -> MarketConfig:
    return MarketConfig(alpha_vantage_key=os.getenv("ALPHAVANTAGE_API_KEY"))


@dataclass(frozen=True)
class FXConfig:
    base_url: str = "https://api.exchangerate.host"


def get_fx_config() -> FXConfig:
    return FXConfig()

