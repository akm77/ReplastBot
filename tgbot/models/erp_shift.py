from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Date, func, Integer, CheckConstraint, text, String, update, delete, select, desc, tuple_, \
    ForeignKeyConstraint, ForeignKey, Boolean, insert, literal, union_all, and_, case
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import Result
from sqlalchemy.orm import relationship, sessionmaker, joinedload, backref
from sqlalchemy.sql import expression

from tgbot.misc.utils import value_to_decimal
from tgbot.models.base import TimedBaseModel, FinanceInteger, column_list, BaseModel
from tgbot.models.erp_dict import ERPEmployee, ERPActivity, ERPMaterial, ERPProduct


class ERPShift(TimedBaseModel):
    __tablename__ = "erp_shift"

    date = Column(Date(), primary_key=True, server_default=func.date('now', 'localtime'))
    number = Column(Integer, CheckConstraint("number IN (1, 2, 3)", name="check_number"), primary_key=True)
    duration = Column(FinanceInteger, server_default=text("800"), nullable=False)
    comment = Column(String(length=128), nullable=True)
    shift_staff = relationship("ERPShiftStaff", back_populates="shift")
    shift_activities = relationship("ERPShiftActivity", back_populates="shift")
    shift_materials = relationship("ERPShiftMaterial", back_populates="shift")
    shift_products = relationship("ERPShiftProduct", back_populates="shift")


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
    employee = relationship("ERPEmployee", backref=backref("shift_staff_member", uselist=False))


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
    line_number = Column(Integer, primary_key=True)
    activity_id = Column(Integer,
                         ForeignKey('erp_activity.id', ondelete="RESTRICT", onupdate="CASCADE"),
                         primary_key=True)
    comment = Column(String(length=128), nullable=True)
    shift = relationship("ERPShift", back_populates="shift_activities")
    activity = relationship("ERPActivity", backref=backref("shift_activity", uselist=False))


class ERPShiftMaterial(BaseModel):
    __tablename__ = "erp_shift_material"

    __table_args__ = (
        ForeignKeyConstraint(
            ('shift_date', 'shift_number'),
            ['erp_shift.date', 'erp_shift.number'],
            ondelete="RESTRICT", onupdate="CASCADE"
        ),
    )

    shift_date = Column(Date(), server_default=func.date('now', 'localtime'), primary_key=True)
    shift_number = Column(Integer, CheckConstraint("shift_number IN (1, 2, 3)", name="check_number"), primary_key=True)
    line_number = Column(Integer, primary_key=True)
    material_id = Column(Integer,
                         ForeignKey('erp_material.id', ondelete="RESTRICT", onupdate="CASCADE"),
                         primary_key=True)
    quantity = Column(FinanceInteger, nullable=False, server_default=text("0"))
    is_processed = Column(Boolean, nullable=False, server_default=expression.false())
    comment = Column(String(length=128), nullable=True)
    material = relationship("ERPMaterial", backref=backref("shift_material", uselist=False))
    shift = relationship("ERPShift", back_populates="shift_materials")


class ERPShiftProduct(BaseModel):
    __tablename__ = "erp_shift_producti"

    __table_args__ = (
        ForeignKeyConstraint(
            ('shift_date', 'shift_number'),
            ['erp_shift.date', 'erp_shift.number'],
            ondelete="RESTRICT", onupdate="CASCADE"
        ),
    )
    shift_date = Column(Date(), server_default=func.date('now', 'localtime'), primary_key=True)
    shift_number = Column(Integer, CheckConstraint("shift_number IN (1, 2, 3)", name="check_number"), primary_key=True)
    line_number = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('erp_product.id', ondelete="RESTRICT", onupdate="CASCADE"))
    quantity = Column(FinanceInteger, nullable=False, server_default=text("0"))
    state = Column(String(length=4), CheckConstraint("state IN ('ok', 'todo', 'back')",
                                                     name="check_shift_product_state"),
                   server_default=text("todo"))
    comment = Column(String(length=128), nullable=True)
    shift = relationship("ERPShift", back_populates="shift_products")
    product = relationship("ERPProduct", backref=backref("shift_product", uselist=False))


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
        ERPEmployee.shift_staff_member))
    statement = statement.options(joinedload(ERPShift.shift_activities,
                                             ).joinedload(
        ERPShiftActivity.activity).joinedload(
        ERPActivity.shift_activity))
    # statement = statement.options(joinedload(ERPShiftActivity.activity,
    #                                          innerjoin=False).joinedload(ERPActivity))
    statement = statement.options(joinedload(ERPShift.shift_materials
                                             ).joinedload(
        ERPShiftMaterial.material).joinedload(
        ERPMaterial.shift_material))
    statement = statement.options(joinedload(ERPShift.shift_products).joinedload(
        ERPShiftProduct.product).joinedload(
        ERPProduct.shift_product))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def select_day_shift_numbers(Session: sessionmaker, **kwargs) -> Optional[List[ERPShift]]:
    if not kwargs.get('date'):
        return
    statement = select(ERPShift).where(ERPShift.date == kwargs['date'])
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalars().all()


async def material_intake_create(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftMaterial]]:
    """
    Create list of materials that did intake. kwargs must have the following attributes:

        *shift_date  Shift date  - mandatory

        *shift_number Shift number - mandatory

        *materials    list of dictionaries {'id': material_id, 'quantity': material_quantity} - mandatory

        *is_processed   Boolean	Indicated that is draft data - optional

        *start_line Number of first line in newly added materials

    :param Session: DB session object
    :param kwargs:
    :return:
    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None or \
            kwargs.get('materials', None) is None:
        return
    start_line = 1 if kwargs.get('start_line', None) is None else kwargs['start_line']
    materials = kwargs['materials']
    if not isinstance(materials, dict):
        return
    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    values = [{"shift_date": shift_date,
               "shift_number": shift_number,
               "line_number": line_number,
               "material_id": int(material),
               "quantity": value_to_decimal(materials[material]["weight"], decimal_places=2)}
              for line_number, material in enumerate(materials, start=start_line)]
    async with Session() as session:
        statement = insert(ERPShiftMaterial).values(values)
        await session.execute(statement)
        await session.commit()
        result = await material_intake_read_shift(Session=Session, shift_date=shift_date, shift_number=shift_number)
        return result


async def material_intake_read_line(Session: sessionmaker, **kwargs) -> Optional[ERPShiftMaterial]:
    """
    Read ERPMaterialIntake object form database. kwargs must have the following attributes:

        *shift_date  Shift date - mandatory

        *shift_number Shift number - mandatory

        *line_number  Sequence number in material intake - mandatory

        *material_id Material ID from ERPMaterial - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:
    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None or \
            kwargs.get('line_number', None) is None or \
            kwargs.get('material_id', None) is None:
        return

    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    line_number = kwargs['line_number']
    material_id = kwargs['material_id']
    statement = select(ERPShiftMaterial).where(ERPShiftMaterial.shift_date == shift_date,
                                               ERPShiftMaterial.shift_number == shift_number,
                                               ERPShiftMaterial.material_id == line_number,
                                               ERPShiftMaterial.line_number == material_id). \
        options(joinedload(ERPShiftMaterial.material))

    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def material_intake_read_shift(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftMaterial]]:
    """
    Read ERPMaterialIntake object form database. kwargs must have the following attributes:

        *shift_date  Shift date - mandatory

        *shift_number Shift number - mandatory

        *limit Number of records to read - optional

        *desc Descending order of records - optional


    :param Session: DB session object
    :param kwargs:
    :return:
    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None:
        return

    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    statement = select(ERPShiftMaterial).where(ERPShiftMaterial.shift_date == shift_date,
                                               ERPShiftMaterial.shift_number == shift_number)
    if kwargs.get('desc', None) is not None:
        statement = statement.order_by(desc(ERPShiftMaterial.line_number))
    else:
        statement = statement.order_by(ERPShiftMaterial.line_number)

    if kwargs.get('limit', None) is not None:
        statement = statement.limit(kwargs['limit'])

    statement = statement.options(joinedload(ERPShiftMaterial.material).joinedload(ERPMaterial.material_type))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalars().all()


async def material_intake_update_line(Session: sessionmaker, **kwargs) -> Optional[ERPShiftMaterial]:
    """
    Update CERPMaterialIntake in database. kwargs may have the following attributes:

        *shift_date  Shift date - mandatory

        *shift_number Shift number - mandatory

        *line_number  Sequence number in material intake - mandatory

        *material_id Material ID from ERPMaterial - mandatory

        *quantity Weight of material in Kg  - optional

        *is_processed   Boolean	Indicated that is draft data - optional

    :param Session: DB session object
    :param kwargs:
    :return:
    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None or \
            kwargs.get('line_number', None) is None or \
            kwargs.get('material_id', None) is None:
        return

    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    line_number = kwargs['line_number']
    material_id = kwargs['material_id']
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShiftMaterial)}

    statement = update(ERPShiftMaterial).where(ERPShiftMaterial.shift_date == shift_date,
                                               ERPShiftMaterial.shift_number == shift_number,
                                               ERPShiftMaterial.line_number == line_number,
                                               ERPShiftMaterial.line_number == material_id).values(values)
    async with Session() as session:
        await session.execute(statement)
        await session.commit()
        result = await material_intake_read_line(Session, shift_date=shift_date, shift_number=shift_number,
                                                 line_number=line_number, material_id=material_id)
        return result


async def material_intake_delete_line(Session: sessionmaker, **kwargs) -> Optional[bool]:
    """
    Update CERPMaterialIntake in database. kwargs may have the following attributes:

        *shift_date  Shift date - mandatory

        *shift_number Shift number - mandatory

        *line_number  Sequence number in material intake - mandatory

        *material_id Material ID from ERPMaterial - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:
    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None or \
            kwargs.get('line_number', None) is None or \
            kwargs.get('material_id', None) is None:
        return

    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    line_number = kwargs['line_number']
    material_id = kwargs['material_id']
    statement = delete(ERPShiftMaterial).where(ERPShiftMaterial.shift_date == shift_date,
                                               ERPShiftMaterial.shift_number == shift_number,
                                               ERPShiftMaterial.line_number == line_number,
                                               ERPShiftMaterial.material_id == material_id)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def material_intake_delete_shift(Session: sessionmaker, **kwargs) -> Optional[bool]:
    """
    Update CERPMaterialIntake in database. kwargs may have the following attributes:

        *shift_date  Shift date - mandatory

        *shift_number Shift number - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:
    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None:
        return
    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    statement = delete(ERPShiftMaterial).where(ERPShiftMaterial.shift_date == shift_date,
                                               ERPShiftMaterial.shift_number == shift_number)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def shift_report_create(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftProduct]]:
    """
    Create list of products that were made in given shift. kwargs must have the following attributes:

        *id Bag number - mandatory

        *shift_date  Shift date  - mandatory

        *shift_number Shift number - mandatory

        *products    list of dictionaries {'id': product_id, 'quantity': product_quantity} - mandatory

        *report_state   Report state from the list ('ok', 'to_do', 'back')" - optional

    :param Session: DB session object
    :param kwargs:
    :return:    """
    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None or \
            kwargs.get('products', None) is None:
        return
    products = kwargs['products']
    if not isinstance(products, dict):
        return
    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    values = [{"id": int(products[product]["bag_number"]),
               "shift_date": shift_date,
               "shift_number": shift_number,
               "product_id": int(product),
               "quantity": value_to_decimal(products[product]["weight"], decimal_places=2)}
              for product in products]
    statement = insert(ERPShiftProduct).values(values)
    async with Session() as session:
        await session.execute(statement)
        await session.commit()
        result = await shift_report_read_shift(Session=Session, shift_date=shift_date, shift_number=shift_number)
        return result


async def shift_report_read_shift(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftProduct]]:
    """
    Read list of products that were made in given shift. kwargs must have the following attributes:

        *shift_date  Shift date  - mandatory

        *shift_number Shift number - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:  List of ERPShiftReport  """
    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None:
        return

    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    statement = select(ERPShiftProduct).where(ERPShiftProduct.shift_date == shift_date,
                                              ERPShiftProduct.shift_number == shift_number)
    statement = statement.order_by(ERPShiftProduct.id)
    statement = statement.options(joinedload(ERPShiftProduct.product).joinedload(ERPProduct.product_type))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalars().all()


async def shift_report_delete_shift(Session: sessionmaker, **kwargs) -> Optional[bool]:
    """
    Delete list of products that were made in given shift. kwargs must have the following attributes:

        *shift_date  Shift date  - mandatory

        *shift_number Shift number - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:    """

    if kwargs.get('shift_date', None) is None or \
            kwargs.get('shift_number', None) is None:
        return

    shift_date = kwargs['shift_date']
    shift_number = kwargs['shift_number']
    statement = delete(ERPShiftProduct).where(ERPShiftProduct.shift_date == shift_date,
                                              ERPShiftProduct.shift_number == shift_number)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def shift_report_read_bag(Session: sessionmaker, **kwargs) -> Optional[ERPShiftProduct]:
    """
    Read product that were made in given shift. kwargs must have the following attributes:

        *id Bag number - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:    """
    if kwargs.get('id', None) is None:
        return

    bag_number = kwargs['id']
    statement = select(ERPShiftProduct).where(ERPShiftProduct.id == bag_number)
    statement = statement.options(joinedload(ERPShiftProduct.product).joinedload(ERPProduct.material_type))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def shift_report_update_bag(Session: sessionmaker, **kwargs) -> Optional[ERPShiftProduct]:
    """
    Update bag product that were made in given shift. kwargs must have the following attributes:

        *id Bag number - mandatory

        *shift_date  Shift date  - optional

        *shift_number Shift number - optional

        *product_id Product ID from ERPProduct - optional

        *report_state   Report state from the list ('ok', 'to_do', 'back')" - optional

        *quantity Weight of product in Kg  - optional

    :param Session: DB session object
    :param kwargs:
    :return:    """
    if kwargs.get('id', None) is None:
        return
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShiftProduct)}
    bag_number = kwargs['id']
    statement = update(ERPShiftProduct).where(ERPShiftProduct.id == bag_number).values(values)
    async with Session() as session:
        await session.execute(statement)
        await session.commit()
        result = await shift_report_read_bag(Session, id=bag_number)
        return result


async def shift_report_delete_bag(Session: sessionmaker, **kwargs) -> Optional[bool]:
    """
    Delete bag product that were made in given shift. kwargs must have the following attributes:

        *id Bag number - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:    """
    if kwargs.get('id', None) is None:
        return

    bag_number = kwargs['id']
    statement = delete(ERPShiftProduct).where(ERPShiftProduct.id == bag_number)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


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
    # LEFT JOIN erp_shift_producti esp ON dr.date = esp.shift_date AND dr.shift_number = esp.shift_number
    # group by dr.date, dr.shift_number
    # order by dr.date, dr.shift_number
    cte_dates = await get_cte_shift_dates(Session)
    cte_shift = get_cte_day_shifts()
    cte_date_range = select(cte_dates.c.date, cte_shift.c.shift_number).cte("date_range")
    statement = select(cte_date_range.c.date.label("shift_date"),
                       cte_date_range.c.shift_number,
                       func.count(ERPShiftProduct.id).label("bag_num")
                       ).join(ERPShiftProduct,
                              and_(cte_date_range.c.date == ERPShiftProduct.shift_date,
                                   cte_date_range.c.shift_number == ERPShiftProduct.shift_number),
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
    # FROM erp_shift_material esm
    # JOIN erp_material em ON esm.material_id = em.id
    # group by esm.shift_date, em.name, esm.is_processed
    statement = select(ERPShiftMaterial.shift_date,
                       ERPMaterial.name,
                       case(
                           (ERPShiftMaterial.is_processed == 0, 'Не принят'),
                           (ERPShiftMaterial.is_processed == 1, 'Склад'),
                       ).label('state'),
                       func.sum(ERPShiftMaterial.quantity).label("quantity")
                       )
    statement = statement.join(ERPShiftMaterial.material)
    statement = statement.group_by(ERPShiftMaterial.shift_date,
                                   ERPMaterial.name,
                                   ERPShiftMaterial.is_processed)
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
    #        count(erp_shift_producti.id) AS bag_num,
    #        sum(erp_shift_producti.quantity) AS quantity
    # FROM date_range
    # LEFT JOIN erp_shift_producti ON date_range.date = erp_shift_producti.shift_date AND date_range.state = erp_shift_producti.report_state
    # LEFT JOIN erp_product ON erp_product.id = erp_shift_producti.product_id
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
                       func.count(ERPShiftProduct.id).label('bag_num'),
                       func.sum(ERPShiftProduct.quantity).label('quantity')
                       )
    statement = statement.join(ERPShiftProduct, and_(cte_date_range.c.date == ERPShiftProduct.shift_date,
                                                     cte_date_range.c.state == ERPShiftProduct.state),
                               isouter=True)
    statement = statement.join(ERPProduct, ERPProduct.id == ERPShiftProduct.product_id,
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
