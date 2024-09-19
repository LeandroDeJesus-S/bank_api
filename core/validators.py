import re

from core.domain_rules import domain_rules


class CpfValidator:
    def __init__(self, cpf: str) -> None:
        self._cpf = cpf
        self.verified_cpf = self.validate()


    @property
    def cpf(self):
        self._cpf = "".join(list(map(lambda i: i if i.isnumeric() else "", self._cpf)))
        return self._cpf

    def calculate_first_digit(self) -> str:
        """Calculates the first digit of the CPF

        Returns:
            str: result of the calculation of the first digit.
        """
        result, m = 0, 10
        for c in self.cpf[:-2]:
            calc = int(c) * m
            result += calc
            m -= 1

        final_result = str(11 - result % 11)
        return final_result if int(final_result) <= 9 else "0"

    def calculate_second_digit(self) -> str:
        """Calculates the second digit of the CPF

        Returns:
            str: result of the calculation of the second digit.
        """
        m, ac = 11, 0
        for i in self.cpf[:-2] + self.calculate_first_digit():
            calc = int(i) * m
            ac += calc
            m -= 1

        final_result = str(11 - ac % 11)
        return final_result if int(final_result) <= 9 else "0"

    def validate(self) -> str:
        """Performs length and sequence verification, calculates the first and second digits, and forms the CPF for validation.

        Returns:
            str: CPF with the calculation of the first and second digits for validation
        """
        if not self.cpf or self.is_sequence() or not self.has_valid_length():
            return ""
        base = self.cpf[:-2]
        first_digit = self.calculate_first_digit()
        second_digit = self.calculate_second_digit()
        cpf_to_validation = base + first_digit + second_digit
        return cpf_to_validation

    def is_valid(self) -> bool:
        """Checks if the provided CPF is valid

        Returns:
            bool: True if the CPF is valid or False if it is not valid.
        """        
        return True if self.cpf and self.cpf == self.verified_cpf else False

    def is_sequence(self) -> bool:
        """Checks if the provided CPF is a sequence, e.g., 000.000.000-00

        Returns:
            bool: True if it is a sequence of digits, False if it is not.
        """        
        verify = self.cpf[0] * 11
        return True if verify == self.cpf else False

    def has_valid_length(self) -> bool:
        """Checks if the length of the provided CPF is valid.

        Returns:
            bool: True if the length is valid or False if it is not valid.
        """
        return True if len(self.cpf) == 11 else False


def min_max_validator(min_, max_, value) -> bool:
    """validate if a value is inside the range of
    min_ and max_ parameters. (e.g: min <= value <= max)

    Args:
        min_: the min acceptable value
        max_: the max acceptable value
        value: the value to compare

        Returns:
        bool: True if value is in range of min and max values
    """
    return min_ <= value <= max_


def regex_validator(pattern: str, string: str, flags=0, strict=False) -> bool:
    """validates the given string applying the given pattern

    Args:
        pattern (str): regular expression
        string (_type_): the value to apply the regex
        flags (int, optional): regex flags. Defaults to 0.
        strict (bool): if True uses re.match instead re.search

    Returns:
        bool: True if the pattern matches
    """
    regex = re.compile(pattern, flags)
    if strict:
        return re.match(pattern, string, flags) is not None
    return re.search(regex, string) is not None


def strong_password_validator(password: str) -> bool:
    """validates if the password contains upper/lower case letters,
    digits and any of !@#$%^&*()_+ symbols

    Args:
        password (str): the user password

    Returns:
        bool: True if the is strong.
    """
    up = regex_validator(r"[A-Z]", password)
    low = regex_validator(r"[a-z]", password)
    num = regex_validator(r"\d", password)
    sym = regex_validator(r"[\!@#\$%\^&\*\(\)_\+]", password)
    length = min_max_validator(
        domain_rules.user_rules.MIN_PASSWORD_SIZE,
        domain_rules.user_rules.MAX_PASSWORD_SIZE,
        len(password),
    )
    all_true = all((up, low, num, sym, length))
    return all_true
