from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from math import isclose

import pytest
from sqlalchemy import and_, select

from core.transactions.models import TransactionType
from core.exceptions import TransactionException
from core.domain_rules import domain_rules


async def test_deposit(five_dumb_accounts, transaction_ctrl, accounts_ctrl):
    account = await accounts_ctrl.get("id", 1)
    value = Decimal("10.00")
    type = TransactionType.deposit

    created = await transaction_ctrl.new(
        account,
        account,
        value,
        type,
        accounts_ctrl,
    )

    stmt = select(transaction_ctrl.model).where(
        and_(
            transaction_ctrl.model.from_account_id == account.id,
            transaction_ctrl.model.to_account_id == account.id,
            transaction_ctrl.model.type == type,
            transaction_ctrl.model.value == value,
        )
    )
    result = await transaction_ctrl.query(stmt)
    assert created
    assert result
    assert isclose(
        result[0].time.timestamp(), datetime.now().timestamp(), rel_tol=0.001
    )


@pytest.mark.parametrize(
    "from_,to,value,detail",
    [
        (1, 1, "0", "Invalid deposit value"),
        (1, 1, "-0.10", "Invalid deposit value"),
        (1, 2, "1", "you can only to deposit on your account"),
    ],
)
async def test_deposit_fail(
    five_dumb_accounts, accounts_ctrl, transaction_ctrl, from_, to, value, detail
):
    account_from = await accounts_ctrl.get("id", from_)
    account_to = await accounts_ctrl.get("id", to)

    value = Decimal(value)
    type = TransactionType.deposit

    with pytest.raises(TransactionException) as e:
        await transaction_ctrl.new(
            account_from,
            account_to,
            value,
            type,
            accounts_ctrl,
        )

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == detail


async def test_withdraw_success(dumb_account_10amount, transaction_ctrl, accounts_ctrl):
    value = Decimal("10")
    account = dumb_account_10amount

    created = await transaction_ctrl.new(
        account, account, value, TransactionType.withdraw, accounts_ctrl
    )
    new_ = await accounts_ctrl.get("id", account.id)

    assert created
    assert new_.amount == Decimal("0")


@pytest.mark.parametrize(
    "value,from_,to,msg",
    [
        (
            Decimal("10.01"),
            1,
            1,
            "Insufficient funds to withdraw.",
        ),
        (
            Decimal("3"),
            1,
            2,
            "You can't withdraw to other account.",
        ),
        (
            domain_rules.transaction_rules.MIN_DEPOSIT_VALUE - Decimal(".01"),
            1,
            2,
            "Invalid withdraw value.",
        ),
        (
            domain_rules.transaction_rules.MAX_DEPOSIT_VALUE + Decimal(".01"),
            1,
            2,
            "Invalid withdraw value.",
        ),
    ],
)
async def test_withdraw_fail(
    two_dumb_accounts_10amount, transaction_ctrl, accounts_ctrl, from_, to, value, msg
):
    from_acc = await accounts_ctrl.get("id", from_)
    to_acc = await accounts_ctrl.get("id", to)
    val = value

    with pytest.raises(TransactionException) as e:
        await transaction_ctrl.new(
            from_acc, to_acc, val, TransactionType.withdraw, accounts_ctrl
        )

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == msg


async def test_transference_success(
    two_dumb_accounts_10amount, transaction_ctrl, accounts_ctrl
):
    id_from, id_to = 1, 2

    from_ = await accounts_ctrl.get("id", id_from)
    to = await accounts_ctrl.get("id", id_to)
    value = Decimal("10")
    type = TransactionType.transference

    await transaction_ctrl.new(from_, to, value, type, accounts_ctrl)

    new_from = await accounts_ctrl.get("id", id_from)
    new_to = await accounts_ctrl.get("id", id_to)

    assert new_from.amount == Decimal("0")
    assert new_to.amount == Decimal("20")


min_, max_ = (
    domain_rules.transaction_rules.MIN_TRANSFER_VALUE,
    domain_rules.transaction_rules.MAX_TRANSFER_VALUE,
)


@pytest.mark.parametrize(
    "id_from,id_to,value,msg",
    [
        (1, 1, Decimal("10"), "you can't make a transfer to yourself"),
        (1, 2, Decimal("0"), f"Invalid transference value. (min: {min_}, max: {max_})"),
        (
            1,
            2,
            Decimal("-0.01"),
            f"Invalid transference value. (min: {min_}, max: {max_})",
        ),
        (1, 2, Decimal("10.01"), "Insufficient funds."),
    ],
)
async def test_transference_fail(
    two_dumb_accounts_10amount, transaction_ctrl, accounts_ctrl, id_from, id_to, value, msg
):
    await accounts_ctrl.update_(id_from, amount=Decimal("10"))
    await accounts_ctrl.update_(id_to, amount=Decimal("10"))

    from_ = await accounts_ctrl.get("id", id_from)
    to = await accounts_ctrl.get("id", id_to)
    type = TransactionType.transference

    with pytest.raises(TransactionException) as e:
        await transaction_ctrl.new(from_, to, value, type, accounts_ctrl)

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == msg


async def test_new_with_invalid_transaction_type(
    two_dumb_accounts_10amount, transaction_ctrl, accounts_ctrl
):
    account = await accounts_ctrl.get("id", 1)
    value = Decimal("10.00")
    type = "invalid"

    with pytest.raises(TransactionException) as e:
        await transaction_ctrl.new(
            account,
            account,
            value,
            type,
            accounts_ctrl,
        )

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == "Invalid transaction type."
