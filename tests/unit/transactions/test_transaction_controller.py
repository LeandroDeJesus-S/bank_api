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
    "from_,to,value,code,detail",
    [
        (1, 1, "0", HTTPStatus.UNPROCESSABLE_ENTITY, "Invalid deposit value"),
        (1, 1, "-0.10", HTTPStatus.UNPROCESSABLE_ENTITY, "Invalid deposit value"),
        (
            1,
            2,
            "1",
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "you can only to deposit on your account",
        ),
    ],
)
async def test_deposit_fail(
    five_dumb_accounts, accounts_ctrl, transaction_ctrl, from_, to, value, code, detail
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

    assert e.value.code == code
    assert e.value.detail == detail


async def test_withdraw_success(dumb_account, transaction_ctrl, accounts_ctrl):
    value = Decimal("1")
    await accounts_ctrl.update_(dumb_account.id, amount=Decimal("3"))
    account = await accounts_ctrl.get("id", dumb_account.id)

    created = await transaction_ctrl.new(
        account, account, value, TransactionType.withdraw, accounts_ctrl
    )
    new_ = await accounts_ctrl.get("id", account.id)

    assert created
    assert new_.amount == Decimal("2")


@pytest.mark.parametrize(
    "value,from_,to,msg",
    [
        ("3.01", 1, 1, "Insufficient funds to withdraw."),
        ("3", 1, 2, "You can't withdraw to other account."),
    ],
)
async def test_withdraw_fail(
    five_dumb_accounts, transaction_ctrl, accounts_ctrl, from_, to, value, msg
):
    from_acc = await accounts_ctrl.get("id", from_)
    to_acc = await accounts_ctrl.get("id", to)
    val = Decimal(value)

    await accounts_ctrl.update_(from_acc.id, amount=Decimal("3"))

    with pytest.raises(TransactionException) as e:
        await transaction_ctrl.new(
            from_acc, to_acc, val, TransactionType.withdraw, accounts_ctrl
        )

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == msg


async def test_transference_success(five_dumb_accounts, transaction_ctrl, accounts_ctrl):
    id_from, id_to = 1, 2
    await accounts_ctrl.update_(id_from, amount=Decimal('10'))
    await accounts_ctrl.update_(id_to, amount=Decimal('10'))
    
    from_ = await accounts_ctrl.get('id', id_from)
    to = await accounts_ctrl.get('id', id_to)
    value = Decimal('10')
    type = TransactionType.transference

    await transaction_ctrl.new(from_, to, value, type, accounts_ctrl)

    new_from = await accounts_ctrl.get('id', id_from)
    new_to = await accounts_ctrl.get('id', id_to)

    assert new_from.amount == Decimal('0')
    assert new_to.amount == Decimal('20')


min_, max_ = domain_rules.transaction_rules.MIN_TRANSFER_VALUE, domain_rules.transaction_rules.MAX_TRANSFER_VALUE
@pytest.mark.parametrize('id_from,id_to,value,msg', [
    (1, 1, Decimal('10'), "you can't make a transfer to yourself"),
    (1, 2, Decimal('0'), f"Invalid transference value. (min: {min_}, max: {max_})"),
    (1, 2, Decimal('-0.01'), f"Invalid transference value. (min: {min_}, max: {max_})"),
    (1, 2, Decimal('10.01'), "Insufficient funds."),
])
async def test_transference_fail(five_dumb_accounts, transaction_ctrl, accounts_ctrl, id_from, id_to, value, msg):
    await accounts_ctrl.update_(id_from, amount=Decimal('10'))
    await accounts_ctrl.update_(id_to, amount=Decimal('10'))
    
    from_ = await accounts_ctrl.get('id', id_from)
    to = await accounts_ctrl.get('id', id_to)
    type = TransactionType.transference

    with pytest.raises(TransactionException) as e:
        await transaction_ctrl.new(from_, to, value, type, accounts_ctrl)
    
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == msg
