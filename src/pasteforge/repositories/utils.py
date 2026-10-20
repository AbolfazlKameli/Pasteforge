from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


async def get_or_create(db: AsyncSession, model, defaults: dict | None = None, **kwargs):
    try:
        stmt = await db.execute(select(model).filter_by(**kwargs))
        return stmt.scalar_one(), False
    except NoResultFound:
        if defaults is not None:
            kwargs.update(defaults)
        try:
            instance = model(**kwargs)
            db.add(instance)
            await db.commit()
            await db.refresh(instance)
            return instance, True
        except IntegrityError:
            stmt = await db.scalars(select(model).filter_by(**kwargs))
            return stmt.first(), False
