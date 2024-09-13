import re

from core.domain_rules import domain_rules


class CpfValidator:
    def __init__(self, cpf: str) -> None:
        self.cpf = cpf
        self.verified_cpf = self.validate()

    @property
    def cpf(self):
        return self._cpf

    @cpf.setter
    def cpf(self, cpf):
        cpf = "".join(list(map(lambda i: i if i.isnumeric() else "", cpf)))
        self._cpf = cpf

    def calculate_first_digit(self) -> str:
        """Calcula o primeiro digito do cpf

        Returns:
            str: reultado do calculo do primeiro digito.
        """
        result, m = 0, 10
        for c in self.cpf[:-2]:
            calc = int(c) * m
            result += calc
            m -= 1

        final_result = str(11 - result % 11)
        return final_result if int(final_result) <= 9 else "0"

    def calculate_second_digit(self) -> str:
        """Calcula o segundo digito do cpf

        Returns:
            str: resultado do calculo do segundo digito.
        """
        m, ac = 11, 0
        for i in self.cpf[:-2] + self.calculate_first_digit():
            calc = int(i) * m
            ac += calc
            m -= 1

        final_result = str(11 - ac % 11)
        return final_result if int(final_result) <= 9 else "0"

    def validate(self) -> str:
        """Faz verificação de comprimento e sequencia, execulta os calculos do
        primeiro e segundo digito, e forma o cpf para validação.

        Returns:
            str: cpf com calculo do primeiro e segundo digito para validar
        """
        if self.is_sequence() or not self.has_valid_length():
            return ""
        base = self.cpf[:-2]
        first_digit = self.calculate_first_digit()
        second_digit = self.calculate_second_digit()
        cpf_to_validation = base + first_digit + second_digit
        return cpf_to_validation

    def is_valid(self) -> bool:
        """verifica se o cpf enviado é valido

        Returns:
            bool: True se o cpf é valido ou False se não é valido.
        """
        return True if self.cpf == self.verified_cpf else False

    def is_sequence(self) -> bool:
        """Verifica se o cpf enviado é uma sequencia Ex; 000.000.000-00

        Returns:
            bool: True se for uma sequencia de digitos, False se não for
        """
        verify = self.cpf[0] * 11
        return True if verify == self.cpf else False

    def has_valid_length(self) -> bool:
        """Verifica se o comprimento do cpf enviado é valido.

        Returns:
            bool: True se o comprimento for valido ou False se não é valido.
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
    digits and any of @#$&*! symbols

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
