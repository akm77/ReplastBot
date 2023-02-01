from datetime import datetime
from typing import Optional, List

from sqlalchemy import func, Column, Integer, String, Date, ForeignKey, text, select, delete, desc, \
    ForeignKeyConstraint, CheckConstraint, update, tuple_, case, literal, union_all, and_, asc
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Result
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload

from tgbot.models.base import TimedBaseModel, column_list, FinanceInteger
from tgbot.models.erp_dict import ERPActivity, ERPMaterial, ERPProduct, ERPEmployee
from tgbot.models.erp_shift_product_material import ERPShiftMaterialIntake, ERPShiftProduction


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


async def upsert_shift_staff(Session: sessionmaker, **kwargs):
    if not (kwargs.get('shift_date') or kwargs.get('shift_number') or kwargs.get('hours_worked')):
        return
    shift_date = kwargs.get('shift_date')
    shift_number = kwargs.get('shift_number')
    hours_worked = kwargs.get('hours_worked')
    staff_for_add = s if (s := kwargs.get('staff_for_add')) else []
    staff_for_delete = s if (s := kwargs.get('staff_for_delete')) else []
    if not (len(staff_for_add) or len(staff_for_delete)):
        return
    delete_statement = delete(ERPShiftStaff).where(ERPShiftStaff.shift_date == shift_date,
                                                   ERPShiftStaff.shift_number == shift_number,
                                                   ERPShiftStaff.employee_id.in_(staff_for_delete))
    values = [{"shift_date": shift_date,
               "shift_number": shift_number,
               "employee_id": e,
               "hours_worked": hours_worked} for e in staff_for_add]
    insert_statement = insert(ERPShiftStaff).values(values)
    update_statement = insert_statement.on_conflict_do_update(
        index_elements=["shift_date", "shift_number", "employee_id"],
        set_=dict(hours_worked=insert_statement.excluded.hours_worked)
    )
    async with Session() as session:
        if len(staff_for_delete):
            await session.execute(delete_statement)
        if len(staff_for_add):
            await session.execute(update_statement)
        await session.commit()


async def get_shift_staff_member(Session: sessionmaker, **kwargs) -> Optional[ERPShiftStaff]:
    if not (kwargs.get('shift_date') or kwargs.get('shift_number') or kwargs.get('employee_id')):
        return
    shift_date = kwargs.get('shift_date')
    shift_number = kwargs.get('shift_number')
    employee_id = kwargs.get('employee_id')
    select_statement = select(ERPShiftStaff).where(ERPShiftStaff.shift_date == shift_date,
                                                   ERPShiftStaff.shift_number == shift_number,
                                                   ERPShiftStaff.employee_id == employee_id)
    select_statement = select_statement.options(joinedload(ERPShiftStaff.employee))
    async with Session() as session:
        result = await session.execute(select_statement)
    return result.scalar()


async def shift_read(Session: sessionmaker, **kwargs) -> Optional[ERPShift]:
    if not (kwargs.get('date') or kwargs.get('number')):
        return
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShift)}
    statement = select(ERPShift).where(ERPShift.date == kwargs['date'], ERPShift.number == kwargs['number'])
    statement = statement.options(joinedload(ERPShift.shift_staff,
                                             innerjoin=False
                                             ).joinedload(
        ERPShiftStaff.employee).joinedload(
        ERPEmployee.erp_shift_staff, innerjoin=False))
    statement = statement.options(joinedload(ERPShift.shift_activity,
                                             innerjoin=False
                                             ).joinedload(
        ERPShiftActivity.activity).joinedload(
        ERPActivity.erp_shift_activity, innerjoin=False))
    # statement = statement.options(joinedload(ERPShiftActivity.activity,
    #                                          innerjoin=False).joinedload(ERPActivity))
    statement = statement.options(joinedload(ERPShift.shift_material_intake,
                                             innerjoin=False
                                             ).joinedload(
        ERPShiftMaterialIntake.material).joinedload(
        ERPMaterial.material_intake, innerjoin=False))
    statement = statement.options(joinedload(ERPShift.shift_production,
                                             innerjoin=False
                                             ).joinedload(
        ERPShiftProduction.product).joinedload(
        ERPProduct.product_shift_report, innerjoin=False))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


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


async def shift_staff_list(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftStaff]]:
    if not (kwargs.get('shift_date') or kwargs.get('shift_number')):
        return
    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    statement = select(ERPShiftStaff).where(ERPShiftStaff.shift_date == shift_date,
                                            ERPShiftStaff.shift_number == shift_number)
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


async def shift_activity_list(Session: sessionmaker) -> Optional[Result]:
    # SELECT esa.shift_date, ea.name, COUNT() AS 'Кол-во'
    # FROM erp_shift_activity esa
    # JOIN erp_activity ea ON esa.activity_id = ea.id
    # GROUP BY esa.shift_date, ea.name
    statement = select(ERPShiftActivity.shift_date,
                       ERPActivity.name,
                       func.count().label("quantity"))
    statement = statement.join(ERPShiftActivity.activity)
    statement = statement.group_by(ERPShiftActivity.shift_date,
                                   ERPActivity.name)
    async with Session() as session:
        result = await session.execute(statement)
        return result


async def get_cte_shift_dates(Session: sessionmaker):
    shift_min_max_dates = select(func.min(ERPShift.date).label('min_date'),
                                 func.max(ERPShift.date).label('max_date'))
    async with Session() as session:
        result = await session.execute(shift_min_max_dates)
    min_date, max_date = result.one_or_none()
    if not (min_date and max_date):
        return
    else:
        min_date = min_date.replace(day=1)

    cte_dates = select(literal(min_date, type_=Date()).label("date")).cte("dates")
    cte_dates = cte_dates.union_all(select(func.date(cte_dates.c.date, '+1 day')).where(cte_dates.c.date <= max_date))
    return cte_dates


def get_cte_day_shifts():
    return union_all(select(literal(1).label("shift_number")),
                     select(literal(2).label("shift_number")),
                     select(literal(3).label("shift_number"))).cte("shift")


def get_cte_product_states():
    return union_all(select(literal("todo").label("state")),
                     select(literal("ok").label("state")),
                     select(literal("back").label("state"))).cte("states")


async def shift_bags_list(Session: sessionmaker) -> Optional[Result]:
    # WITH dates(date) AS (VALUES('2022-12-01')
    #                      UNION ALL
    #                      SELECT date(date, '+1 day')
    #                      FROM dates
    #                      WHERE date < '2032-12-31'),
    # shift(shift_number) AS (VALUES (1), (2), (3)),
    # date_range AS (SELECT date, shift_number
    #                FROM dates
    #                CROSS JOIN shift)
    # select dr.date, dr.shift_number, count(esp.id) as bag_num
    # FROM date_range dr
    # LEFT JOIN erp_shift_production esp ON dr.date = esp.shift_date AND dr.shift_number = esp.shift_number
    # group by dr.date, dr.shift_number
    # order by dr.date, dr.shift_number
    cte_dates = await get_cte_shift_dates(Session)
    cte_shift = get_cte_day_shifts()
    cte_date_range = select(cte_dates.c.date, cte_shift.c.shift_number).cte("date_range")
    statement = select(cte_date_range.c.date.label("shift_date"),
                       cte_date_range.c.shift_number,
                       func.count(ERPShiftProduction.id).label("bag_num")
                       ).join(ERPShiftProduction,
                              and_(cte_date_range.c.date == ERPShiftProduction.shift_date,
                                   cte_date_range.c.shift_number == ERPShiftProduction.shift_number),
                              isouter=True).group_by(cte_date_range.c.date,
                                                     cte_date_range.c.shift_number)
    async with Session() as session:
        result = await session.execute(statement)
    return result


async def shift_material_intake_list(Session: sessionmaker) -> Optional[Result]:
    #     select esm.shift_date, em.name,
    #        CASE esm.is_processed
    #            WHEN 0 THEN 'Не принят'
    #            WHEN 1 THEN 'Склад'
    #        END AS state,
    #        SUM(esm.quantity/100) as quantity
    # FROM erp_shift_material_intake esm
    # JOIN erp_material em ON esm.material_id = em.id
    # group by esm.shift_date, em.name, esm.is_processed
    statement = select(ERPShiftMaterialIntake.shift_date,
                       ERPMaterial.name,
                       case(
                           (ERPShiftMaterialIntake.is_processed == 0, 'Не принят'),
                           (ERPShiftMaterialIntake.is_processed == 1, 'Склад'),
                       ).label('state'),
                       func.sum(ERPShiftMaterialIntake.quantity).label("quantity")
                       )
    statement = statement.join(ERPShiftMaterialIntake.material)
    statement = statement.group_by(ERPShiftMaterialIntake.shift_date,
                                   ERPMaterial.name,
                                   ERPShiftMaterialIntake.is_processed)
    async with Session() as session:
        result = await session.execute(statement)
        return result


async def shift_production_list(Session: sessionmaker) -> Optional[Result]:
    # WITH dates(DATE) AS (VALUES('2023-01-01')
    #                      UNION ALL
    #                      SELECT DATE(DATE, '+1 day')
    #                      FROM dates
    #                      WHERE DATE <= '2023-01-07'),
    # report_state(state) AS (VALUES ('to_do'), ('ok'), ('back')),
    # date_range AS (SELECT DATE, state
    #                FROM dates
    #                CROSS JOIN report_state)
    #
    # SELECT date_range.date AS shift_date,
    #        ifnull(erp_product.name, 'я') AS name,
    #        CASE WHEN (date_range.state = 'to_do') THEN 'Не принят'
    #             WHEN (date_range.state= 'ok') THEN 'Склад'
    #             WHEN (date_range.state = 'back') THEN 'Возврат'
    #        END AS state,
    #        count(erp_shift_production.id) AS bag_num,
    #        sum(erp_shift_production.quantity) AS quantity
    # FROM date_range
    # LEFT JOIN erp_shift_production ON date_range.date = erp_shift_production.shift_date AND date_range.state = erp_shift_production.report_state
    # LEFT JOIN erp_product ON erp_product.id = erp_shift_production.product_id
    # GROUP BY date_range.date, erp_product.name, date_range.state

    cte_dates = await get_cte_shift_dates(Session)
    cte_product_states = get_cte_product_states()
    cte_date_range = select(cte_dates.c.date, cte_product_states.c.state).cte("date_range")
    statement = select(cte_date_range.c.date.label("shift_date"),
                       func.ifnull(ERPProduct.name, "я").label("name"),
                       case(
                           (cte_date_range.c.state == 'todo', 'Не принят'),
                           (cte_date_range.c.state == 'ok', 'Склад'),
                           (cte_date_range.c.state == 'back', 'Возврат'),
                       ).label('state'),
                       func.count(ERPShiftProduction.id).label('bag_num'),
                       func.sum(ERPShiftProduction.quantity).label('quantity')
                       )
    statement = statement.join(ERPShiftProduction, and_(cte_date_range.c.date == ERPShiftProduction.shift_date,
                                                        cte_date_range.c.state == ERPShiftProduction.report_state),
                               isouter=True)
    statement = statement.join(ERPProduct, ERPProduct.id == ERPShiftProduction.product_id,
                               isouter=True)
    statement = statement.group_by(cte_date_range.c.date,
                                   ERPProduct.name,
                                   cte_date_range.c.state)
    async with Session() as session:
        result = await session.execute(statement)
        return result


async def staff_time_sheet(Session: sessionmaker) -> Optional[Result]:
    #     WITH dates(date) AS (VALUES('2022-12-01')
    #                      UNION ALL
    #                      SELECT date(date, '+1 day')
    #                      FROM dates
    #                      WHERE date < '2032-12-31'),
    # shift(shift_number) AS (VALUES (1), (2), (3)),
    # date_range AS (SELECT date, shift_number
    #                FROM dates
    #                CROSS JOIN shift)
    # SELECT IFNULL(e.name, "я") AS name, date_range.date, date_range.shift_number, shift.duration, staff.hours_worked / 100 AS hours_worked
    # FROM date_range
    # LEFT JOIN erp_shift shift ON date_range.date = "shift"."date" AND date_range.shift_number = "shift"."number"
    # LEFT JOIN erp_shift_staff staff ON "shift"."date" = staff.shift_date AND "shift"."number" = staff.shift_number
    # LEFT join erp_employee e ON staff.employee_id = e.id
    # order by date_range.date, date_range.shift_number, e.name;
    cte_dates = await get_cte_shift_dates(Session)
    cte_shift = get_cte_day_shifts()
    cte_date_range = select(cte_dates.c.date, cte_shift.c.shift_number).cte("date_range")
    statement = select(func.ifnull(ERPEmployee.name, "я").label("name"),
                       cte_date_range.c.date.label("shift_date"),
                       cte_date_range.c.shift_number,
                       ERPShift.duration,
                       ERPShiftStaff.hours_worked)
    statement = statement.join(ERPShift, and_(cte_date_range.c.date == ERPShift.date,
                                              cte_date_range.c.shift_number == ERPShift.number),
                               isouter=True)
    statement = statement.join(ERPShiftStaff, and_(cte_date_range.c.date == ERPShiftStaff.shift_date,
                                                   cte_date_range.c.shift_number == ERPShiftStaff.shift_number),
                               isouter=True)
    statement = statement.join(ERPEmployee, ERPShiftStaff.employee_id == ERPEmployee.id, isouter=True)
    statement = statement.order_by(cte_date_range.c.date,
                                   cte_date_range.c.shift_number,
                                   literal(1))
    async with Session() as session:
        result = await session.execute(statement)
    return result
