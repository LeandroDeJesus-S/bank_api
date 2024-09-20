async def test_check_role_success(user_role_controller, dumb_user, dumb_role, dumb_user_role):
    has_role = await user_role_controller.check_role(dumb_user, dumb_role)
    assert has_role

async def test_check_role_fail(user_role_controller, dumb_user, admin_role):
    has_role = await user_role_controller.check_role(dumb_user, admin_role)
    assert not has_role
