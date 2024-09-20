def test_password_hash_success(password_controller):
    """test if the password is hashed correctly"""
    pw = 'super_secret'
    hashed = password_controller.hash_password(pw)

    assert hashed.startswith(password_controller._hash_prefix)
    assert password_controller._hasher.ident in hashed


def test_check_password_success(password_controller):
    """test if the check_password matches with the correct pass"""
    pw = 'super_secret'
    hashed = password_controller.hash_password(pw)

    result = password_controller.check_password(pw, hashed)
    assert result


def test_check_password_fail(password_controller):
    """test if the check_password dont matches with a incorrect pass"""
    pw = 'super_secret'
    hashed = password_controller.hash_password(pw)
    wrong_pw = 'wrong!'

    result = password_controller.check_password(wrong_pw, hashed)
    assert not result
