from unittest.mock import Mock, patch

import pytest

from src.allocation.domain import model, service
from src.allocation.repositories import sqlalchemy_repository


@patch("sqlalchemy.orm.Session.commit")
def test_returns_allocation(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    line = model.OrderLine(order_id="o1", sku="COMPLICATED-LAMP", qty=10)
    batch = model.Batch(ref="b1", sku="COMPLICATED-LAMP", qty=100, eta=None)
    repo = sqlalchemy_repository.FakeRepository({batch})

    result = service.allocate(line, repo, Session())
    assert result == "b1"


@patch("sqlalchemy.orm.Session.commit")
def test_error_for_invalid_sku(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    line = model.OrderLine(order_id="o1", sku="NONEXISTENTSKU", qty=10)
    batch = model.Batch(ref="b1", sku="AREALSKU", qty=100, eta=None)
    repo = sqlalchemy_repository.FakeRepository({batch})

    with pytest.raises(
        service.InvalidSkuException, match="Invalid sku NONEXISTENTSKU"
    ):
        service.allocate(line, repo, Session())


@patch("sqlalchemy.orm.Session.commit")
def test_commits(mock_session_commit: Mock) -> None:
    from sqlalchemy.orm import Session

    line = model.OrderLine(order_id="o1", sku="OMINOUS-MIRROR", qty=10)
    batch = model.Batch(ref="b1", sku="OMINOUS-MIRROR", qty=100, eta=None)
    repo = sqlalchemy_repository.FakeRepository({batch})

    service.allocate(line, repo, Session())
    mock_session_commit.assert_called_once
