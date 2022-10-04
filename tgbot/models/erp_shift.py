import datetime
from typing import Optional, List

from sqlalchemy import func, Column, Integer, String, Date, ForeignKey, text, insert, select, delete, desc, \
    ForeignKeyConstraint, CheckConstraint, update, tuple_
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload

from tgbot.models.base import TimedBaseModel, column_list, FinanceInteger


class ERPShift(TimedBaseModel):
    __tablename__ = "erp_shift"

    date = Column(Date(), primary_key=True, server_default=func.date('now', 'localtime'))
    number = Column(Integer, CheckConstraint("number IN (1, 2, 3)", name="check_number"), primary_key=True)
    duration = Column(FinanceInteger, server_default=text("800"), nullable=False)
    comment = Column(String(length=128), nullable=True)
    shift_staff = relationship("ERPShiftStaff", back_populates="shift")
    shift_activity = relationship("ERPShiftActivity", back_populates="shift")


class ERPShiftStaff(TimedBaseModel):
    __tablename__ = "erp_shift_staff"
    __table_args__ = (
        ForeignKeyConstraint(
            ('shift_date', 'shift_number'),
            ['erp_shift.date', 'erp_shift.number'],
            ondelete="RESTRICT", onupdate="CASCADE"
        ),
    )

    shift_date = Column(Date(), primary_key=True, server_default=func.date('now', 'localtime'))
    shift_number = Column(Integer, CheckConstraint("shift_number IN (1, 2, 3)", name="check_number"), primary_key=True)
    employee_id = Column(Integer,
                         ForeignKey('erp_employee.id', ondelete="RESTRICT", onupdate="CASCADE"),
                         primary_key=True)
    hours_worked = Column(FinanceInteger, server_default=text("800"), nullable=False)
    shift = relationship("ERPShift", back_populates="shift_staff")
    employee = relationship("ERPEmployee", backref=backref("erp_shift_staff", uselist=False))


class ERPShiftActivity(TimedBaseModel):
    __tablename__ = "erp_shift_activity"
    __table_args__ = (
        ForeignKeyConstraint(
            ('shift_date', 'shift_number'),
            ['erp_shift.date', 'erp_shift.number'],
            ondelete="RESTRICT", onupdate="CASCADE"
        ),
    )

    shift_date = Column(Date(), primary_key=True, server_default=func.date('now', 'localtime'))
    shift_number = Column(Integer, CheckConstraint("shift_number IN (1, 2, 3)", name="check_number"), primary_key=True)
    activity_id = Column(Integer,
                         ForeignKey('erp_activity.id', ondelete="RESTRICT", onupdate="CASCADE"),
                         primary_key=True)
    shift = relationship("ERPShift", back_populates="shift_activity")
    activity = relationship("ERPActivity", backref=backref("erp_shift_activity", uselist=False))


async def shift_create(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if kwargs.get('date', None) is None or kwargs.get('number', None) is None:
        return
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShift)}
    async with Session() as session:
        statement = insert(ERPShift).values(**values)
        result = await session.execute(statement)
        shift_date, shift_number = result.inserted_primary_key
        if kwargs.get('staff_list', None) is not None:
            staff_list = kwargs['staff_list']
            values = [{"shift_date": shift_date,
                       "shift_number": shift_number,
                       "employee_id": int(employee_id),
                       "hours_worked": int(staff_list[employee_id]["hour"])} for employee_id in staff_list]
            statement = insert(ERPShiftStaff).values(values)
            await session.execute(statement)
        if kwargs.get('activity_list', None) is not None:
            activity_list = kwargs['activity_list']
            values = [{"shift_date": shift_date,
                       "shift_number": shift_number,
                       "activity_id": activity} for activity in activity_list]
            statement = insert(ERPShiftActivity).values(values)
            await session.execute(statement)
        await session.commit()
        result = await shift_read(Session, date=shift_date, number=shift_number)
    return result


async def shift_read(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if kwargs.get('date', None) is None or kwargs.get('number', None) is None:
        return
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShift)}
    statement = select(ERPShift).where(ERPShift.date == kwargs['date'], ERPShift.number == kwargs['number'])
    statement = statement.options(joinedload(ERPShift.shift_staff,
                                             innerjoin=False).joinedload(ERPShiftStaff.employee))
    statement = statement.options(joinedload(ERPShift.shift_activity,
                                             innerjoin=False).joinedload(ERPShiftActivity.activity))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def shift_update(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if kwargs.get('date', None) is None or kwargs.get('number', None) is None:
        return
    # id = Column(String(length=11), primary_key=True)
    # shift_date = Column(Date(), server_default=func.date('now', 'localtime'))
    # duration = Column(FinanceInteger, server_default=text("800"), nullable=False)
    # comment = Column(String(length=128), nullable=True)
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShift)}
    statement = update(ERPShift).where(ERPShift.date == kwargs['date'],
                                       ERPShift.number == kwargs['number']).values(values)
    async with Session() as session:
        await session.execute(statement)
        await session.commit()
        result = await shift_read(Session, date=kwargs['date'], number=kwargs['number'])
        return result


async def shift_delete(Session: sessionmaker, **kwargs) -> Optional[bool]:
    if kwargs.get('date', None) is None or kwargs.get('number', None) is None:
        return

    statement = delete(ERPShift).where(ERPShift.date == kwargs['date'],
                                       ERPShift.number == kwargs['number'])
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def shift_list_full(Session: sessionmaker, **kwargs) -> Optional[List[ERPShift]]:
    async with Session() as session:
        statement = select(ERPShift)
        if kwargs.get('date', None) is not None:
            statement = statement.where(ERPShift.date == kwargs['date'])
        statement = statement.order_by(desc(ERPShift.date), desc(ERPShift.number))
        if kwargs.get('limit', None) is not None:
            statement = statement.limit(kwargs['limit'])
        result = await session.execute(statement)
        return result.scalars().all()


async def shift_navigator(Session: sessionmaker, direction: str = 'prev', **kwargs) -> Optional[List[ERPShift]]:
    if kwargs.get('date', None) is None or kwargs.get('number', None) is None:
        return
    shift_date = kwargs['date']
    shift_number = kwargs['number']
    async with Session() as session:
        statement = select(ERPShift)
        if direction == "prev":
            statement = statement.where(tuple_(ERPShift.date, ERPShift.number) <
                                        tuple_(shift_date, shift_number))
            statement = statement.order_by(desc(ERPShift.date), desc(ERPShift.number))
    if direction == "next":
        statement = statement.where(tuple_(ERPShift.date, ERPShift.number) >
                                    tuple_(shift_date, shift_number))
        statement = statement.order_by(ERPShift.date, ERPShift.number)
    if kwargs.get('limit', None):
        statement = statement.limit(kwargs['limit'])
    result = await session.execute(statement)
    return result.scalars().all()
