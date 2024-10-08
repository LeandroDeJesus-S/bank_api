from decimal import Decimal

from core import exceptions, validators
from core.database.controller import DatabaseController
from core.domain_rules import domain_rules

from .models import Transaction, TransactionType

TRANSACTION_RULES = domain_rules.transaction_rules


class TransactionController(DatabaseController):
    """the controller to manage the transactions"""
    def __init__(self) -> None:
        super().__init__(model=Transaction)

    async def new(
        self,
        from_account,
        to_account,
        value: Decimal,
        type: TransactionType,
        accounts_controller,
    ):
        """creates a new transaction

        Args:
            from_account (Account): the sender account model instance.
            to_account (Account): the receiver account model instance.
            value (Decimal): the value of the transaction.
            type (TransactionType): the type of the transaction
            accounts_controller (AccountController): the accounts controller instance.

        Raises:
            exceptions.TransactionException: an invalid transaction type was given

        Returns:
            bool: True if rows are affected
        """
        async with self._db.transaction():
            self.validate(from_account, to_account, value, type)

            created = await self.create(
                from_account_id=from_account.id,
                to_account_id=to_account.id,
                value=value,  # type: ignore
                type=type,  # type: ignore
            )

            if type == TransactionType.deposit:
                amount = from_account.amount + value
                await accounts_controller.update_(
                    from_account.id,
                    amount=amount,
                )

            elif type == TransactionType.withdraw:
                amount = from_account.amount - value
                await accounts_controller.update_(
                    from_account.id,
                    amount=amount,
                )

            elif type == TransactionType.transference:
                from_account_amount = from_account.amount - value
                to_account_amount = to_account.amount + value

                await accounts_controller.update_(
                    from_account.id,
                    amount=from_account_amount,
                )
                await accounts_controller.update_(
                    to_account.id,
                    amount=to_account_amount,
                )

            else:
                raise exceptions.TransactionException("Invalid transaction type.")

        return bool(created)

    def validate(self, from_account, to_account, value, type):
        """template method to call the validation methods. If some validation
        fail raises TransactionException else returns None.

        Args:
            from_account (Account): the sender account instance.
            to_account (Account): the receiver account instance.
            value (Decimal): the value of the transaction.
            type (TransactionType): the transaction type.
        """
        self.validate_deposit(type, value, from_account, to_account)
        self.validate_withdraw(type, value, to_account, from_account)
        self.validate_transference(type, value, from_account, to_account)

    def validate_deposit(self, type, value, account_from, account_to):
        """makes the validation of a deposit transaction

        Args:
            type (TransactionType): the type of the transaction.
            value (Decimal): the value of the transaction.
            account_from (Account): the instance of the sender of the transaction.
            account_to (Account): the instance of the receiver account.

        Raises:
            exceptions.TransactionException: the value of the deposit is invalid.
            exceptions.TransactionException: the sender is different of the receiver.
        """
        if type != TransactionType.deposit:
            return

        valid_value = validators.min_max_validator(
            TRANSACTION_RULES.MIN_DEPOSIT_VALUE,
            TRANSACTION_RULES.MAX_DEPOSIT_VALUE,
            value,
        )
        if not valid_value:
            raise exceptions.TransactionException("Invalid deposit value")

        if account_from.id != account_to.id:
            raise exceptions.TransactionException(
                "you can only to deposit on your account"
            )

    def validate_withdraw(self, type, value, to_account, from_account):
        """makes the validation of a withdraw transaction

        Args:
            type (TransactionType): the type of the transaction.
            value (Decimal): the value of the transaction.
            account_from (Account): the instance of the sender of the transaction.
            account_to (Account): the instance of the receiver account.

        Raises:
            exceptions.TransactionException: the value of the withdraw is invalid.
            exceptions.TransactionException: the sender is different of the receiver.
            exceptions.TransactionException: funds insufficient to withdraw.
        """
        if type != TransactionType.withdraw:
            return

        is_valid_value = validators.min_max_validator(
            TRANSACTION_RULES.MIN_WITHDRAW_VALUE,
            TRANSACTION_RULES.MAX_WITHDRAW_VALUE,
            value,
        )
        if not is_valid_value:
            raise exceptions.TransactionException("Invalid withdraw value.")

        if from_account.id != to_account.id:
            raise exceptions.TransactionException(
                "You can't withdraw to other account."
            )

        if value > from_account.amount:
            raise exceptions.TransactionException("Insufficient funds to withdraw.")

    def validate_transference(self, type, value, from_account, to_account):
        """makes the validation of a transference transaction

        Args:
            type (TransactionType): the type of the transaction.
            value (Decimal): the value of the transaction.
            account_from (Account): the instance of the sender of the transaction.
            account_to (Account): the instance of the receiver account.

        Raises:
            exceptions.TransactionException: the sender is making a transference to himself.
            exceptions.TransactionException: the value of the transference is invalid.
            exceptions.TransactionException: the sender is different of the receiver.
        """
        if type != TransactionType.transference:
            return

        if from_account.id == to_account.id:
            raise exceptions.TransactionException(
                "you can't make a transfer to yourself"
            )

        is_valid_value = validators.min_max_validator(
            TRANSACTION_RULES.MIN_TRANSFER_VALUE,
            TRANSACTION_RULES.MAX_TRANSFER_VALUE,
            value,
        )
        if not is_valid_value:
            min_, max_ = (
                TRANSACTION_RULES.MIN_TRANSFER_VALUE,
                TRANSACTION_RULES.MAX_TRANSFER_VALUE,
            )
            raise exceptions.TransactionException(
                f"Invalid transference value. (min: {min_}, max: {max_})"
            )

        if from_account.amount < value:
            raise exceptions.TransactionException("Insufficient funds.")
