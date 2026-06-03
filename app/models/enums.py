from enum import Enum

from sqlalchemy import Enum as SQLEnum


def pg_enum(enum_class: type[Enum], name: str):
    """PostgreSQL enum with lowercase values (not Python member names)."""
    return SQLEnum(
        enum_class,
        name=name,
        values_callable=lambda x: [e.value for e in x],
    )
