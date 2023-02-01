from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Date, func, Integer, CheckConstraint, text, String, update, delete, select, desc, tuple_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Result
from sqlalchemy.orm import relationship, sessionmaker, joinedload

from tgbot.models.base import TimedBaseModel, FinanceInteger, column_list
from tgbot.models.erp_dict import ERPEmployee, ERPActivity, ERPMaterial, ERPProduct
from tgbot.models.erp_shift_product_material import ERPShiftMaterialIntake, ERPShiftProduction
from tgbot.models.erp_shift_staff_activity import ERPShiftStaff, ERPShiftActivity


class ERPShift(TimedBaseModel):
    __tablename__ = "erp_shift"

    date = Column(Date(), primary_key=True, server_default=func.date('now', 'localtime'))
    number = Column(Integer, CheckConstraint("number IN (1, 2, 3)", name="check_number"), primary_key=True)
    duration = Column(FinanceInteger, server_default=text("800"), nullable=False)
    comment = Column(String(length=128), nullable=True)
    shift_staff = relationship("ERPShiftStaff", back_populates="shift")
    shift_activity = relationship("ERPShiftActivity", back_populates="shift")
    shift_material_intake = relationship("ERPShiftMaterialIntake", back_populates="shift")
    shift_production = relationship("ERPShiftProduction", back_populates="shift")


async def shift_create(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if not (kwargs.get('date') or kwargs.get('number')):
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


async def shift_update(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if not (kwargs.get('date') or kwargs.get('number')):
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
    if not (kwargs.get('date') or kwargs.get('number')):
        return

    statement = delete(ERPShift).where(ERPShift.date == kwargs['date'],
                                       ERPShift.number == kwargs['number'])
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def shift_list_full(Session: sessionmaker, **kwargs) -> Optional[List[ERPShift]]:
    statement = select(ERPShift)
    if kwargs.get('date'):
        statement = statement.where(ERPShift.date == kwargs['date'])
    if not kwargs.get('reverse'):
        statement = statement.order_by(ERPShift.date, ERPShift.number)
    else:
        statement = statement.order_by(desc(ERPShift.date), desc(ERPShift.number))
    if kwargs.get('limit', None) is not None:
        statement = statement.limit(kwargs['limit'])
    async with Session() as session:
        result = await session.execute(statement)
    return result.scalars().all()


async def shift_navigator(Session: sessionmaker, direction: str = 'prev', **kwargs) -> Optional[List[ERPShift]]:
    if not (kwargs.get('date') or kwargs.get('number')):
        return
    shift_date = kwargs['date']
    shift_number = kwargs['number']
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
    async with Session() as session:
        result = await session.execute(statement)
    return result.scalars().all()


async def get_shift_row_number_on_date(Session: sessionmaker, shift_date: datetime.date) -> Optional[Result]:
    # WITH max_date AS (select MAX(date) as shift_date
    #                   FROM erp_shift
    #                   WHERE date <= '2023-01-06'),
    # numbered_shift AS (SELECT ROW_NUMBER() OVER(ORDER BY date, number) AS row_number, date
    #                    FROM erp_shift)
    # select numbered_shift.row_number
    # FROM numbered_shift, max_date
    # WHERE DATE =  max_date.shift_date
    max_date = select(func.max(ERPShift.date).label("shift_date")).where(ERPShift.date <= shift_date).cte("max_date")
    numbered_shift = select(func.row_number().over(order_by=tuple_(ERPShift.date,
                                                                   ERPShift.number)).label("row_number"),
                            ERPShift.date).cte("numbered_shift")
    statement = select(numbered_shift.c.row_number,
                       max_date.c.shift_date).where(numbered_shift.c.date == max_date.c.shift_date)
    async with Session() as session:
        result = await session.execute(statement)
        return result


async def shift_read(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if not (kwargs.get('date') or kwargs.get('number')):
        return
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShift)}
    statement = select(ERPShift).where(ERPShift.date == kwargs['date'], ERPShift.number == kwargs['number'])
    statement = statement.options(joinedload(ERPShift.shift_staff
                                             ).joinedload(
        ERPShiftStaff.employee).joinedload(
        ERPEmployee.erp_shift_staff))
    statement = statement.options(joinedload(ERPShift.shift_activity,
                                             ).joinedload(
        ERPShiftActivity.activity).joinedload(
        ERPActivity.erp_shift_activity))
    # statement = statement.options(joinedload(ERPShiftActivity.activity,
    #                                          innerjoin=False).joinedload(ERPActivity))
    statement = statement.options(joinedload(ERPShift.shift_material_intake
                                             ).joinedload(
        ERPShiftMaterialIntake.material).joinedload(
        ERPMaterial.material_intake))
    statement = statement.options(joinedload(ERPShift.shift_production).joinedload(
        ERPShiftProduction.product).joinedload(
        ERPProduct.product_shift_report))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()