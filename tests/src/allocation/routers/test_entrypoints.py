from typing import Any, Dict, Optional

import httpx

from tests import random_refs


def post_to_add_batch(
    client: httpx.Client, ref: str, sku: str, qty: int, eta: Optional[str]
) -> None:
    result = client.post(
        "/api/batches/", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert result.status_code == 201


def test_happy_path_returns_201_and_allocated_batch(client: httpx.Client) -> None:
    sku, othersku = random_refs.random_sku(), random_refs.random_sku("other")
    earlybatch = random_refs.random_batchref("1")
    laterbatch = random_refs.random_batchref("2")
    otherbatch = random_refs.random_batchref("3")
    post_to_add_batch(
        client=client, ref=laterbatch, sku=sku, qty=100, eta="2011-01-02"
    )
    post_to_add_batch(
        client=client, ref=earlybatch, sku=sku, qty=100, eta="2011-01-01"
    )
    post_to_add_batch(client=client, ref=otherbatch, sku=othersku, qty=100, eta=None)

    data = {"order_id": random_refs.random_orderid(), "sku": sku, "qty": 3}
    result = client.post("/api/batches/allocate/", json=data)
    result_data: Dict[str, Any] = result.json()

    assert result.status_code == 201
    assert result_data.get("batch_ref") == earlybatch


def test_unhappy_path_returns_400_and_error_message(client: httpx.Client) -> None:
    unknown_sku, orderid = random_refs.random_sku(), random_refs.random_orderid()
    data = {"order_id": orderid, "sku": unknown_sku, "qty": 20}
    result = client.post("/api/batches/allocate/", json=data)
    result_data: Dict[str, Any] = result.json()

    assert result.status_code == 400
    assert result_data.get("detail") == f"Invalid sku {unknown_sku}"
