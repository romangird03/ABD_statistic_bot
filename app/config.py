import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str


@dataclass
class ApiConfig:
    base_url: str
    user: str
    password: str


@dataclass
class Config:
    bot: BotConfig
    api: ApiConfig


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is missing in .env")

    api_user = os.getenv("API_USER")
    api_pass = os.getenv("API_PASS")
    if not api_user or not api_pass:
        raise ValueError("API_USER/API_PASS are missing in .env")

    api_url = os.getenv(
        "API_URL",
        "https://api.hse.panfilov.app/channel-stats",
    )

    return Config(
        bot=BotConfig(token=bot_token),
        api=ApiConfig(
            base_url=api_url,
            user=api_user,
            password=api_pass,
        ),
    )
