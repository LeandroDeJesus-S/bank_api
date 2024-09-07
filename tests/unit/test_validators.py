import pytest
from core import validators

valid_cpfs = ['15278053011', '64497369099', '979.820.400-04']


@pytest.mark.parametrize('cpf', valid_cpfs)
def test_cpf_valid(cpf):
    """test if the cpf validator works as expected with valid CPFs"""
    cpf_validator = validators.CpfValidator(cpf)
    assert cpf_validator.is_valid()


invalid_cpfs = ['25278053011', '6a497369099', '979.820.400-05']


@pytest.mark.parametrize('cpf', invalid_cpfs)
def test_cpf_invalid(cpf):
    """test if the cpf validator works as expected with invalid CPFs"""
    cpf_validator = validators.CpfValidator(cpf)
    assert not cpf_validator.is_valid()


def test_min_max_validator_with_valid_value():
    """test if min_max_validator function works as expected in success case"""
    min_val = 5
    max_val = 10
    value = 7

    result = validators.min_max_validator(min_val, max_val, value)
    assert result

def test_min_max_validator_with_invalid_value():
    """test if min_max_validator function works as expected in fail case"""
    min_val = 5
    max_val = 10
    value = 11

    result = validators.min_max_validator(min_val, max_val, value)
    assert not result


def test_regex_validator_with_valid_string():
    """test if the regex_validator matches as expected with a valid string"""
    string = 'test_string123'
    pattern = '^[a-z]{4}_[a-z]{6}[1-3]{3}$'
    
    result = validators.regex_validator(pattern, string)
    assert result


def test_regex_validator_with_invalid_string():
    """test if the regex_validator don't match as expected with a invalid string"""
    string = 'teststring123'
    pattern = '^[a-z]{4}_[a-z]{6}[1-3]{3}$'
    
    result = validators.regex_validator(pattern, string)
    assert not result


strong_passwords = [
    'StrongPassword@123',
    '2C270a3@05c11E49',
    '8bc5fa9df07DD22f1$d2'
]


@pytest.mark.parametrize('password', strong_passwords)
def test_strong_password_validator_with_strong_password(password):
    """test if the strong_password_validator returns true with a strong password"""
    result = validators.strong_password_validator(password)
    assert result


weak_passwords = [
    'Without@numbers',
    'WithoutS1mb0ls',
    'without@upperc4s3',
    'WITHOUT@LOWERC4S3',
    'Wk@size',
    'BiggestSize@1' * 3, 
]


@pytest.mark.parametrize('pw', weak_passwords)
def test_strong_password_validator_with_weak_password(pw):
    """test if the strong_password_validator returns false with a weak password"""
    result = validators.strong_password_validator(pw)
    assert not result
