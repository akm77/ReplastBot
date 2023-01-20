from dataclasses import dataclass

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, text, insert, select, update, delete
from sqlalchemy.orm import relationship, backref, sessionmaker, joinedload, declared_attr
from sqlalchemy.sql import expression

from tgbot.models.base import Base, FinanceInteger, column_list


@dataclass(frozen=True)
class DictType:
    SIMPLE: str = 's'
    COMPLEX: str = 'c'


class ERPSimpleDict(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String(length=64), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, server_default=expression.true())
    comment = Column(String(length=64), nullable=True)


class ERPEmployee(ERPSimpleDict):
    __tablename__ = "erp_employee"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.SIMPLE,
                "table_name": "Сотрудники",
                "name_name": "Имя"}


class ERPCity(ERPSimpleDict):
    __tablename__ = "erp_city"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.SIMPLE,
                "table_name": "Города",
                "name_name": "Название"}


class ERPMaterialType(ERPSimpleDict):
    __tablename__ = "erp_material_type"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.SIMPLE,
                "table_name": "Типы сырья",
                "name_name": "Название"}


class ERPProductType(ERPSimpleDict):
    __tablename__ = "erp_product_type"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.SIMPLE,
                "table_name": "Типы продукции",
                "name_name": "Название"}


class ERPUnitOfMeasurement(ERPSimpleDict):
    __tablename__ = "erp_uom"

    code = Column(String(length=5), nullable=False, index=True, unique=True)

    @declared_attr
    def hr_names(self):
        return {"type": DictType.COMPLEX,
                "table_name": "Единицы измерения",
                "name_name": "Название",
                "code_name": "Код"}


class ERPProduct(ERPSimpleDict):
    __tablename__ = "erp_product"

    product_type_id = Column(Integer,
                             ForeignKey('erp_product_type.id', ondelete="RESTRICT", onupdate="CASCADE"))
    uom_code = Column(String(length=5),
                      ForeignKey('erp_uom.code', ondelete="RESTRICT", onupdate="CASCADE"), server_default=text("кг"))
    product_type = relationship("ERPProductType", backref=backref("erp_product", uselist=False))

    @declared_attr
    def hr_names(self):
        return {"type": DictType.COMPLEX,
                "table_name": "Продукция",
                "name_name": "Название",
                "lookup_name": "тип продукции"}


class ERPActivity(ERPSimpleDict):
    __tablename__ = "erp_activity"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.SIMPLE,
                "table_name": "Виды работ",
                "name_name": "Название"}


class ERPMaterial(ERPSimpleDict):
    __tablename__ = "erp_material"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.COMPLEX,
                "table_name": "Сырье",
                "name_name": "Название",
                "lookup_name": "тип сырья"}

    material_type_id = Column(Integer,
                              ForeignKey('erp_material_type.id', ondelete="RESTRICT", onupdate="CASCADE"))
    material_type = relationship("ERPMaterialType", backref=backref("erp_material", uselist=False))
    uom_code = Column(String(length=5),
                      ForeignKey('erp_uom.code', ondelete="RESTRICT", onupdate="CASCADE"), server_default=text("кг"))
    impurity = Column(FinanceInteger, nullable=False, server_default=text("1000"))


class ERPContractor(ERPSimpleDict):
    __tablename__ = "erp_contractor"

    @declared_attr
    def hr_names(self):
        return {"type": DictType.COMPLEX,
                "table_name": "Контрагент",
                "name_name": "Название",
                "lookup_name": "название города"}

    city_id = Column(Integer,
                     ForeignKey('erp_city.id', ondelete="RESTRICT", onupdate="CASCADE"))
    city = relationship("ERPCity", backref=backref("erp_contractor", uselist=False))
    is_provider = Column(Boolean, nullable=False, server_default=expression.true())
    is_buyer = Column(Boolean, nullable=False, server_default=expression.false())


DICT_LIST = [ERPEmployee, ERPCity, ERPMaterialType, ERPProductType, ERPProduct, ERPActivity, ERPMaterial, ERPContractor]


async def dct_create(Session: sessionmaker, table_class: Base, **kwargs):
    values = {k: v for k, v in kwargs.items() if k in column_list(table_class)}
    async with Session() as session:
        statement = insert(table_class).values(**values)
        result = await session.execute(statement)
        result_id = result.inserted_primary_key.id
        await session.commit()
        result = await dct_read(Session, table_class, id=result_id)
    return result


async def dct_read(Session: sessionmaker, table_class: Base, joined_load=None, **kwargs):
    if not kwargs.get('id', None):
        return
    statement = select(table_class).where(table_class.id == kwargs['id'])
    if joined_load is not None:
        statement = statement.options(joinedload(joined_load, innerjoin=True))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()


async def dct_update(Session: sessionmaker, table_class: Base, **kwargs):
    if not kwargs.get('id', None):
        return None

    values = {k: v for k, v in kwargs.items() if k in column_list(table_class)}

    async with Session() as session:
        statement = update(table_class).where(table_class.id == kwargs['id']).values(values)
        await session.execute(statement)
        await session.commit()
        result = await dct_read(Session, table_class, id=kwargs['id'])
        return result


async def dct_delete(Session: sessionmaker, table_class: Base, **kwargs):
    if not kwargs.get('id', None):
        return None
    async with Session() as session:
        statement = delete(table_class).where(table_class.id == kwargs['id'])
        result = await session.execute(statement)
        await session.commit()

    return True if result.rowcount else False


async def dct_list(Session: sessionmaker, table_class: Base, joined_load=None, **kwargs):
    async with Session() as session:
        statement = select(table_class)
        if not (kwargs.get('id', None) is None):
            statement = statement.where(table_class.id == kwargs['id'])
        if not (kwargs.get('is_provider', None) is None):
            statement = statement.where(table_class.is_provider == kwargs['is_provider'])
        if not (kwargs.get('is_buyer', None) is None):
            statement = statement.where(table_class.is_buyer == kwargs['is_buyer'])
        if not (kwargs.get('is_active', None) is None):
            statement = statement.where(table_class.is_active == kwargs['is_active'])
        if joined_load is not None:
            statement = statement.options(joinedload(joined_load, innerjoin=True))
        result = await session.execute(statement)
        return result.scalars().all()
