import uuid
from typing import Any, Callable, Dict

import httpx
import pytest


def random_suffix() -> str:
    return uuid.uuid4().hex[:6]


def random_sku(name: str = "") -> str:
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name: str = "") -> str:
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name: str = "") -> str:
    return f"order-{name}-{random_suffix()}"


@pytest.mark.usefixtures("mock_config_get_session")
def test_api_returns_allocation(
    client: httpx.Client, add_stock: Callable[..., None]
) -> None:
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref("1")
    laterbatch = random_batchref("2")
    otherbatch = random_batchref("3")
    add_stock(
        [
            (laterbatch, sku, 100, "2011-01-02"),
            (earlybatch, sku, 100, "2011-01-01"),
            (otherbatch, othersku, 100, None),
        ],
    )

    data = {"order_id": random_orderid(), "sku": sku, "qty": 3}
    result = client.post("/api/allocate/", json=data)
    result_data: Dict[str, Any] = result.json()

    assert result.status_code == 201
    assert result_data.get("batch_ref") == earlybatch


@pytest.mark.usefixtures("mock_config_get_session")
def test_unhappy_path_returns_400_and_error_message(client: httpx.Client) -> None:
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"order_id": orderid, "sku": unknown_sku, "qty": 20}
    result = client.post("/api/allocate/", json=data)
    result_data: Dict[str, Any] = result.json()

    assert result.status_code == 400
    assert result_data.get("detail") == f"Invalid sku {unknown_sku}"
