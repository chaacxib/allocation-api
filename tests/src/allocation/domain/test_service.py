from unittest.mock import Mock, patch

import pytest


@patch("sqlalchemy.orm.Session.commit")
def test_add_batch(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    from src.allocation.domain import service
    from src.allocation.domain.model import dto
    from src.allocation.repositories import sqlalchemy_repository

    repo = sqlalchemy_repository.FakeRepository(set())

    service.add_batch(
        repo=repo,
        session=Session(),
        dto=dto.BatchInput(ref="b1", sku="CRUNCHY-ARMCHAIR", qty=100, eta=None),
    )
    assert repo.get("b1") is not None
    mock_session_commit.assert_called_once


@patch("sqlalchemy.orm.Session.commit")
def test_allocate_returns_allocation(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    from src.allocation.domain import service
    from src.allocation.domain.model import dto
    from src.allocation.repositories import sqlalchemy_repository

    repo = sqlalchemy_repository.FakeRepository(set())
    service.add_batch(
        repo=repo,
        session=Session(),
        dto=dto.BatchInput(ref="batch1", sku="COMPLICATED-LAMP", qty=100, eta=None),
    )

    result = service.allocate(
        repo=repo,
        session=Session(),
        dto=dto.OrderLineInput(sku="COMPLICATED-LAMP", order_id="o1", qty=10),
    )
    assert result == "batch1"


@patch("sqlalchemy.orm.Session.commit")
def test_allocate_errors_for_invalid_sku(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    from src.allocation.domain import service
    from src.allocation.domain.model import dto
    from src.allocation.repositories import sqlalchemy_repository

    repo = sqlalchemy_repository.FakeRepository(set())
    service.add_batch(
        repo=repo,
        session=Session(),
        dto=dto.BatchInput(ref="b1", sku="AREALSKU", qty=100, eta=None),
    )

    with pytest.raises(
        service.InvalidSkuException, match="Invalid sku NONEXISTENTSKU"
    ):
        service.allocate(
            repo=repo,
            session=Session(),
            dto=dto.OrderLineInput(sku="NONEXISTENTSKU", order_id="o1", qty=10),
        )


@patch("sqlalchemy.orm.Session.commit")
def test_commits(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    from src.allocation.domain import service
    from src.allocation.domain.model import dto
    from src.allocation.repositories import sqlalchemy_repository

    repo = sqlalchemy_repository.FakeRepository(set())

    service.add_batch(
        repo=repo,
        session=Session(),
        dto=dto.BatchInput(ref="b1", sku="OMINOUS-MIRROR", qty=100, eta=None),
    )
    service.allocate(
        repo=repo,
        session=Session(),
        dto=dto.OrderLineInput(sku="OMINOUS-MIRROR", order_id="o1", qty=10),
    )

    mock_session_commit.assert_called_once
