from typing import Optional, List

from sqlalchemy import Column, Integer, Date, CheckConstraint, func, ForeignKeyConstraint, ForeignKey, text, String, \
    Boolean, insert, select, update, delete, desc
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload
from sqlalchemy.sql import expression

from tgbot.misc.utils import value_to_decimal
from tgbot.models.base import BaseModel, FinanceInteger, column_list
from tgbot.models.erp_dict import ERPMaterial, ERPProduct


class ERPShiftMaterialIntake(BaseModel):
    __tablename__ = "erp_shift_material_intake"

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
    material = relationship("ERPMaterial", backref=backref("material_intake", uselist=False))
    quantity = Column(FinanceInteger, nullable=False, server_default=text("0"))
    is_processed = Column(Boolean, nullable=False, server_default=expression.false())


class ERPShiftProduction(BaseModel):
    __tablename__ = "erp_shift_production"

    __table_args__ = (
        ForeignKeyConstraint(
            ('shift_date', 'shift_number'),
            ['erp_shift.date', 'erp_shift.number'],
            ondelete="RESTRICT", onupdate="CASCADE"
        ),
    )
    id = Column(Integer, primary_key=True)  # Номер мещка
    shift_date = Column(Date(), server_default=func.date('now', 'localtime'))
    shift_number = Column(Integer, CheckConstraint("shift_number IN (1, 2, 3)", name="check_number"))
    product_id = Column(Integer, ForeignKey('erp_product.id', ondelete="RESTRICT", onupdate="CASCADE"))
    product = relationship("ERPProduct", backref=backref("product_shift_report", uselist=False))
    report_state = Column(String(length=4), CheckConstraint("report_state IN ('ok', 'todo', 'back')",
                                                            name="check_shift_report_state"),
                          server_default=text("todo"))
    quantity = Column(FinanceInteger, nullable=False, server_default=text("0"))


async def material_intake_create(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftMaterialIntake]]:
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
        statement = insert(ERPShiftMaterialIntake).values(values)
        await session.execute(statement)
        await session.commit()
        result = await material_intake_read_shift(Session=Session, shift_date=shift_date, shift_number=shift_number)
        return result


async def material_intake_read_line(Session: sessionmaker, **kwargs) -> Optional[ERPShiftMaterialIntake]:
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
    statement = select(ERPShiftMaterialIntake).where(ERPShiftMaterialIntake.shift_date == shift_date,
                                                     ERPShiftMaterialIntake.shift_number == shift_number,
                                                     ERPShiftMaterialIntake.material_id == line_number,
                                                     ERPShiftMaterialIntake.line_number == material_id). \
        options(joinedload(ERPShiftMaterialIntake.material))

    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def material_intake_read_shift(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftMaterialIntake]]:
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
    statement = select(ERPShiftMaterialIntake).where(ERPShiftMaterialIntake.shift_date == shift_date,
                                                     ERPShiftMaterialIntake.shift_number == shift_number)
    if kwargs.get('desc', None) is not None:
        statement = statement.order_by(desc(ERPShiftMaterialIntake.line_number))
    else:
        statement = statement.order_by(ERPShiftMaterialIntake.line_number)

    if kwargs.get('limit', None) is not None:
        statement = statement.limit(kwargs['limit'])

    statement = statement.options(joinedload(ERPShiftMaterialIntake.material).joinedload(ERPMaterial.material_type))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalars().all()


async def material_intake_update_line(Session: sessionmaker, **kwargs) -> Optional[ERPShiftMaterialIntake]:
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
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShiftMaterialIntake)}

    statement = update(ERPShiftMaterialIntake).where(ERPShiftMaterialIntake.shift_date == shift_date,
                                                     ERPShiftMaterialIntake.shift_number == shift_number,
                                                     ERPShiftMaterialIntake.line_number == line_number,
                                                     ERPShiftMaterialIntake.line_number == material_id).values(values)
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
    statement = delete(ERPShiftMaterialIntake).where(ERPShiftMaterialIntake.shift_date == shift_date,
                                                     ERPShiftMaterialIntake.shift_number == shift_number,
                                                     ERPShiftMaterialIntake.line_number == line_number,
                                                     ERPShiftMaterialIntake.material_id == material_id)
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
    statement = delete(ERPShiftMaterialIntake).where(ERPShiftMaterialIntake.shift_date == shift_date,
                                                     ERPShiftMaterialIntake.shift_number == shift_number)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def shift_report_create(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftProduction]]:
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
    statement = insert(ERPShiftProduction).values(values)
    async with Session() as session:
        await session.execute(statement)
        await session.commit()
        result = await shift_report_read_shift(Session=Session, shift_date=shift_date, shift_number=shift_number)
        return result


async def shift_report_read_shift(Session: sessionmaker, **kwargs) -> Optional[List[ERPShiftProduction]]:
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
    statement = select(ERPShiftProduction).where(ERPShiftProduction.shift_date == shift_date,
                                                 ERPShiftProduction.shift_number == shift_number)
    statement = statement.order_by(ERPShiftProduction.id)
    statement = statement.options(joinedload(ERPShiftProduction.product).joinedload(ERPProduct.material_type))
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
    statement = delete(ERPShiftProduction).where(ERPShiftProduction.shift_date == shift_date,
                                                 ERPShiftProduction.shift_number == shift_number)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False


async def shift_report_read_bag(Session: sessionmaker, **kwargs) -> Optional[ERPShiftProduction]:
    """
    Read product that were made in given shift. kwargs must have the following attributes:

        *id Bag number - mandatory

    :param Session: DB session object
    :param kwargs:
    :return:    """
    if kwargs.get('id', None) is None:
        return

    bag_number = kwargs['id']
    statement = select(ERPShiftProduction).where(ERPShiftProduction.id == bag_number)
    statement = statement.options(joinedload(ERPShiftProduction.product).joinedload(ERPProduct.material_type))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def shift_report_update_bag(Session: sessionmaker, **kwargs) -> Optional[ERPShiftProduction]:
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
    values = {k: v for k, v in kwargs.items() if k in column_list(ERPShiftProduction)}
    bag_number = kwargs['id']
    statement = update(ERPShiftProduction).where(ERPShiftProduction.id == bag_number).values(values)
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
    statement = delete(ERPShiftProduction).where(ERPShiftProduction.id == bag_number)
    async with Session() as session:
        result = await session.execute(statement)
        await session.commit()
        return True if result.rowcount else False
