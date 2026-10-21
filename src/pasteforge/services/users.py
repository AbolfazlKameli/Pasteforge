from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.pasteforge.models import User


async def register_user(db: AsyncSession, email: str, password: str | None = None) -> User:
    user = User(email=email)

    if password is None:
        user.set_unusable_password()
    elif password is not None:
        user.set_password(password)

    try:
        db.add(user)
        await db.flush()
        await db.refresh(user)
    except IntegrityError as e:
        await db.rollback()
        raise ValueError('Duplicate entry or constraint violated') from e
    except SQLAlchemyError as e:
        await db.rollback()
        raise RuntimeError('Database operation failed') from e
    return user
