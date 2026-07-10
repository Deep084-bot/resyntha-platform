from __future__ import annotations

from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

    @classmethod
    def from_string(cls, value: str) -> Environment:
        for member in cls:
            if member.value == value.lower():
                return member
            if member.name.lower() == value.lower():
                return member
        return cls.DEVELOPMENT

    @property
    def is_development(self) -> bool:
        return self is Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self is Environment.TESTING

    @property
    def is_production(self) -> bool:
        return self is Environment.PRODUCTION
