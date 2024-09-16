from decimal import Decimal
from http import HTTPStatus

import pytest

from core.domain_rules import domain_rules


async def test_create_transaction_deposit_success(
    client, five_dumb_accounts, accounts_ctrl
):
    data = {"from_account_id": 1, "to_account_id": 1, "value": 10, "type": "deposit"}

    response = await client.post("/transactions/", json=data)

    assert response.status_code == HTTPStatus.CREATED


@pytest.mark.parametrize(
    "from_id,to_id,value",
    [
        (1, 2, 10),
        (
            1,
            1,
            float(domain_rules.transaction_rules.MIN_DEPOSIT_VALUE - Decimal(".01")),
        ),
        (1, 1, -0.01),
        (
            1,
            1,
            float(domain_rules.transaction_rules.MAX_DEPOSIT_VALUE + Decimal(".01")),
        ),
    ],
)
async def test_create_transaction_deposit_fail(
    client, five_dumb_accounts, accounts_ctrl, from_id, to_id, value
):
    data = {
        "from_account_id": from_id,
        "to_account_id": to_id,
        "value": value,
        "type": "deposit",
    }

    response = await client.post("/transactions/", json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert (
        resp_data["detail"]
        in [
            "Invalid deposit value",
            "you can only to deposit on your account",
            "the sender or receiver account id does not exists.",
        ]
        or resp_data["detail"][0]["msg"] == "Input should be greater than 0"
    )


async def test_create_transaction_withdraw_success(
    client, dumb_account_10amount, accounts_ctrl
):
    data = {
        "from_account_id": dumb_account_10amount.id,
        "to_account_id": dumb_account_10amount.id,
        "value": 10,
        "type": "withdraw",
    }

    response = await client.post("/transactions/", json=data)

    acc = await accounts_ctrl.get("id", dumb_account_10amount.id)

    assert response.status_code == HTTPStatus.CREATED
    assert acc.amount == Decimal("0")


@pytest.mark.parametrize(
    "from_id,to_id,value",
    [
        (1, 2, 10),
        (1, 2, 11),
        (
            1,
            1,
            float(domain_rules.transaction_rules.MIN_WITHDRAW_VALUE - Decimal(".01")),
        ),
        (1, 1, -0.01),
        (
            1,
            1,
            float(domain_rules.transaction_rules.MAX_WITHDRAW_VALUE + Decimal(".01")),
        ),
    ],
)
async def test_create_transaction_withdraw_fail(
    client, two_dumb_accounts_10amount, accounts_ctrl, from_id, to_id, value
):
    data = {
        "from_account_id": from_id,
        "to_account_id": to_id,
        "value": value,
        "type": "withdraw",
    }

    response = await client.post("/transactions/", json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert (
        resp_data["detail"]
        in [
            "Invalid withdraw value.",
            "You can't withdraw to other account.",
            "the sender or receiver account id does not exists.",
        ]
        or resp_data["detail"][0]["msg"] == "Input should be greater than 0"
    )


async def test_create_transaction_transference_success(
    client, two_dumb_accounts_10amount, accounts_ctrl
):
    from_id, to_id = 1, 2

    data = {
        "from_account_id": from_id,
        "to_account_id": to_id,
        "value": 10,
        "type": "transference",
    }

    response = await client.post("/transactions/", json=data)
    from_ = await accounts_ctrl.get("id", from_id)
    to = await accounts_ctrl.get("id", to_id)

    assert response.status_code == HTTPStatus.CREATED
    assert from_.amount == Decimal("0")
    assert to.amount == Decimal("20")


@pytest.mark.parametrize(
    "from_id,to_id,value",
    [
        (1, 1, 10),
        (1, 2, 11),
        (1, 999, 10),
        (
            1,
            2,
            float(domain_rules.transaction_rules.MIN_TRANSFER_VALUE - Decimal(".01")),
        ),
        (1, 2, -0.01),
        (
            1,
            2,
            float(domain_rules.transaction_rules.MAX_TRANSFER_VALUE + Decimal(".01")),
        ),
    ],
)
async def test_create_transaction_transference_fail(
    client, two_dumb_accounts_10amount, accounts_ctrl, from_id, to_id, value
):
    data = {
        "from_account_id": from_id,
        "to_account_id": to_id,
        "value": value,
        "type": "transference",
    }

    response = await client.post("/transactions/", json=data)
    resp_detail = response.json()["detail"]
    print(resp_detail, from_id, to_id, value)

    from_ = await accounts_ctrl.get("id", from_id)
    to = await accounts_ctrl.get("id", to_id)
    min_, max_ = (
        domain_rules.transaction_rules.MIN_TRANSFER_VALUE,
        domain_rules.transaction_rules.MAX_TRANSFER_VALUE,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert (
        resp_detail
        in [
            "you can't make a transfer to yourself",
            f"Invalid transference value. (min: {min_}, max: {max_})",
            "Insufficient funds.",
            "the sender or receiver account id does not exists."
        ]
        or resp_detail[0]["msg"] == "Input should be greater than 0"
    )
    assert (from_.amount == Decimal("10")) if from_ is not None else True
    assert (to.amount == Decimal("10")) if to is not None else True


@pytest.mark.parametrize("limit,offset,expect_len", [(100, 2, 3), (2, 0, 2),])
async def test_list_accounts_success(client, five_dumb_transactions, limit, offset, expect_len, transaction_ctrl):
    print('executou test_list_accounts_success')
    response = await client.get(
        "/transactions/",
        params={"limit": limit, "offset": offset},
    )
    resp_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(resp_data) == expect_len
