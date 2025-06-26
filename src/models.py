from datetime import datetime, timezone
from typing import List

from sqlalchemy import Column, DateTime, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase): ...


control_associations = Table(
    "control_associations",
    Base.metadata,
    Column("control_id", ForeignKey("controls.id")),
    Column("category_id", ForeignKey("categories.id")),
)


class BasicInfo(Base):
    __tablename__ = "basicinfo"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str]
    value: Mapped[str]


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    display_controls: Mapped[str]
    runners: Mapped[List["Runner"]] = relationship(back_populates="category")
    controls: Mapped[List["Control"]] = relationship(
        secondary=control_associations, back_populates="categories"
    )


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    code: Mapped[int]
    mandatory: Mapped[bool]
    spectator: Mapped[bool]
    categories: Mapped[List["Category"]] = relationship(
        secondary=control_associations, back_populates="controls"
    )


class Runner(Base):
    __tablename__ = "runners"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    club: Mapped[str]
    si: Mapped[int]
    reg: Mapped[str]
    call: Mapped[str]
    startlist_time: Mapped[datetime | None]
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="runners")
    ocheck_processed: Mapped[bool] = mapped_column(default=False)
    manual_dns: Mapped[bool] = mapped_column(default=False)
    manual_disk: Mapped[bool] = mapped_column(default=False)


class Punch(Base):
    __tablename__ = "punches"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int]  # 1000 = start, 1001 = finish, 1002 = OCheckList
    si: Mapped[int]
    time: Mapped[datetime]
