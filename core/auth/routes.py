from fastapi import APIRouter

from .schemas import AuthSchema

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/token')
def authenticate(auth_data: AuthSchema):
    ...
