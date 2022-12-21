import datetime
import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey, String, text, CheckConstraint, Boolean, func, DateTime, \
    select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine import ChunkedIteratorResult
from sqlalchemy.orm import sessionmaker, relationship, joinedload, aliased, backref
from sqlalchemy.sql import expression

from tgbot.models.base import BaseModel, AccountingInteger

logger = logging.getLogger(__name__)


class ERPOperation(BaseModel):
    __tablename__ = "erp_operation"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class ERPMeasureUnit(BaseModel):
    __tablename__ = "erp_measure_unit"
    name = Column(String(10), primary_key=True)
    full_name = Column(String(50))


class ERPSection(BaseModel):
    __tablename__ = "erp_section"
    id = Column(Integer, primary_key=True)  # id  счета
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(255), nullable=False)


class ERPChartOfAccount(BaseModel):
    __tablename__ = "erp_coa"
    id = Column(Integer, primary_key=True)  # id  счета
    parent_id = Column(Integer, ForeignKey(id))
    account_no = Column(String(50), nullable=False, index=True, unique=True)
    account_name = Column(String(100), nullable=False, index=True, unique=True)
    account_kind = Column(String(2), CheckConstraint("account_kind IN ('A', 'P', 'AP')", name="check_kind"),
                          nullable=False, server_default=text("A"))
    is_currency = Column(Boolean, nullable=False, server_default=expression.false())
    is_quantitative = Column(Boolean, nullable=False, server_default=expression.false())
    is_balance = Column(Boolean, nullable=False, server_default=expression.true())

    children = relationship("ERPChartOfAccount")
    sections = relationship("ERPSection", secondary="erp_coa_section")


class ERPChartOfAccountSection(BaseModel):
    __tablename__ = "erp_coa_section"
    account_no = Column(String(50), ForeignKey('erp_coa.account_no', ondelete="RESTRICT", onupdate="CASCADE"),
                        primary_key=True)
    section_id = Column(Integer, ForeignKey('erp_section.id', ondelete="RESTRICT", onupdate="CASCADE"),
                        primary_key=True)


class ERPAccountingEntry(BaseModel):
    __tablename__ = "erp_acc_entry"
    id = Column(Integer, primary_key=True)
    entry_dt = Column(DateTime(), nullable=False, index=True,
                      unique=True, server_default=func.date('now', 'localtime'))
    operation_id = Column(Integer, ForeignKey('erp_operation.id', ondelete="RESTRICT", onupdate="CASCADE"))
    dr_account_no = Column(String(50), ForeignKey('erp_coa.account_no', ondelete="RESTRICT", onupdate="CASCADE"))
    cr_account_no = Column(String(50), ForeignKey('erp_coa.account_no', ondelete="RESTRICT", onupdate="CASCADE"))
    amount = Column(AccountingInteger, nullable=False)


class ERPAccountBalance(BaseModel):
    __tablename__ = "erp_acc_balance"
    account_no = Column(String(50), ForeignKey('erp_coa.account_no', ondelete="RESTRICT", onupdate="CASCADE"),
                        primary_key=True)
    balance_date = Column(DateTime(), primary_key=True, index=True, )
    opening_dr_amount = Column(AccountingInteger, nullable=False, server_default=text("0"))
    opening_cr_amount = Column(AccountingInteger, nullable=False, server_default=text("0"))
    dr_amount = Column(AccountingInteger, nullable=False, server_default=text("0"))
    cr_amount = Column(AccountingInteger, nullable=False, server_default=text("0"))
    account = relationship("ERPChartOfAccount", backref=backref("account_balance", uselist=False))


async def get_account_from_account_no(Session: sessionmaker, account_no: str) -> Optional[ERPChartOfAccount]:
    coa_alias = aliased(ERPChartOfAccount)
    statement = select(ERPChartOfAccount)

    statement = statement.join(ERPChartOfAccount.children.of_type(coa_alias), isouter=True)
    statement = statement.where(coa_alias.id.is_(None), ERPChartOfAccount.account_no == account_no)
    statement = statement.options(joinedload(ERPChartOfAccount.sections,
                                             innerjoin=False))
    async with Session() as session:
        result = await session.execute(statement)
        return result.scalar()

    # ledger_date = Column(Date(), primary_key=True, server_default=func.date('now', 'localtime'))
    # account_id = Column(Integer, ForeignKey('erp_coa.id', ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    # side = Column(String(2), CheckConstraint("side IN ('Dr', 'Cr')", name="check_side"), primary_key=True)
    # opening_balance = (Column(AccountingInteger, nullable=False))
    # amount = Column(AccountingInteger, nullable=False)
    # currency_amount = Column(AccountingInteger)
    # currency_iso_code = Column(String(3))
    # quantity = Column(AccountingInteger)
    # measure_unit = Column(String(10),
    #                       ForeignKey('erp_measure_unit.short_name', ondelete="RESTRICT", onupdate="CASCADE"))


def check_active_passive_balance(account: ERPChartOfAccount, debit, credit) -> bool:
    balance = debit - credit
    if account.account_kind == "A" and balance < 0:
        logger.error("Active account %s will be negative", account.account_no)
        raise ValueError(f"Active account {account.account_no} will be negative")
    elif account.account_kind == "P" and balance > 0:
        raise ValueError(f"Passive account {account.account_no} will be positive")
    elif account.account_kind == "AP":
        return True
    return True


async def get_last_account_balance(Session: sessionmaker,
                                   account: ERPChartOfAccount) -> ERPAccountBalance:
    subquery = select(func.max(ERPAccountBalance.balance_date)
                      ).where(ERPAccountBalance.account_no == account.account_no).subquery()
    select_statement = select(ERPAccountBalance).where(ERPAccountBalance.account_no == account.account_no,
                                                       ERPAccountBalance.balance_date == subquery)
    async with Session() as session:
        result = await session.execute(select_statement)
        return result.scalar()


async def check_entry_dt(Session: sessionmaker, entry_dt: datetime.datetime) -> Optional[bool]:
    select_statement = select(func.max(ERPAccountingEntry.entry_dt).label("last_entry_dt"))
    async with Session() as session:
        result: ChunkedIteratorResult = await session.execute(select_statement)
        last_entry = result.one_or_none()
        if last_entry and last_entry["last_entry_dt"] and last_entry["last_entry_dt"] >= entry_dt:
            logger.error(f"The date and time {entry_dt: %d.%m.Y %H:%M:%S} incorrectly. There is a later entry.")
            raise ValueError(f"The date and time {entry_dt: %d.%m.Y %H:%M:%S} incorrectly. There is a later entry.")
        return True


async def add_entry(Session: sessionmaker, operation_id: int, dr: str, cr: str, amount: Decimal, **kwargs):
    """
    kwargs {"dr_section": {1: object_id, 2: object_id, 3: object_id},
            "cr_section": {1: object_id, 2: object_id, 3: object_id},
            "currency_amount": value,
            "currency_iso_code": value,
            "quantity": value,
            "measure_unit": value}

    :param operation_id:
    :param Session:
    :param dr:
    :param cr:
    :param amount:
    :param kwargs:
    :return:
    """
    dr_account = await get_account_from_account_no(Session, dr)
    cr_account = await get_account_from_account_no(Session, cr)
    # Check Dr account is valid
    if not (dr_account and cr_account):
        logger.error("Account Dr = %s and Cr = %s can't be used in entry.", dr, cr)
        raise ValueError("Account can't be used in entry.")

    dr_account_balance = await get_last_account_balance(Session, dr_account)
    cr_account_balance = await get_last_account_balance(Session, cr_account)

    entry_dt = kwargs['entry_dt'] if kwargs.get('entry_dt') else datetime.datetime.now()
    await check_entry_dt(Session, entry_dt)

    dr_debit_amount = Decimal(0)
    dr_credit_amount = Decimal(0)
    cr_debit_amount = Decimal(0)
    cr_credit_amount = Decimal(0)
    if dr_account_balance.balance_date < entry_dt.date():
        dr_values = {"opening_dr_amount": dr_account_balance.dr_amount,
                     "opening_cr_amount": dr_account_balance.cr_amount}
        dr_debit_amount = amount
    elif dr_account_balance.balance_date == entry_dt.date():
        dr_debit_amount = dr_account_balance.dr_amount + amount

    if cr_account_balance.balance_date < entry_dt.date():
        cr_values = {"opening_dr_amount": cr_account_balance.dr_amount,
                     "opening_cr_amount": cr_account_balance.cr_amount}
    elif cr_account_balance.balance_date == entry_dt.date():
        cr_credit_amount = cr_account_balance.cr_amount + amount

    check_active_passive_balance(dr_account, dr_debit, dr_credit)

    check_active_passive_balance(cr_account, cr_debit, cr_credit)

    if (dr_account_balance and (dr_account_balance.entry_dt > entry_dt)) or \
            (cr_account_balance and (cr_account_balance.entry_dt > entry_dt)):
        logger.error("Wrong %s entry date and time. Account balance for Dr = %s or Cr = %s already exist.",
                     entry_dt.strftime("%H:%M:%S %d.%m.%Y"), dr, cr)
        raise ValueError("Wrong entry date and time. Account balance already exist.")
    entry_values = {"entry_dt": entry_dt,
                    "operation_id": operation_id,
                    "dr_account_no": dr_account.account_no,
                    "cr_account_no": cr_account.account_no,
                    "amount": amount}
    insert_account_balance = insert(ERPAccountBalance).values([{"account_no": dr_account.account_no,
                                                                "entry_dt": entry_dt,
                                                                "debit": dr_debit,
                                                                "credit": dr_credit},
                                                               {"account_no": cr_account.account_no,
                                                                "entry_dt": entry_dt,
                                                                "debit": cr_debit,
                                                                "credit": cr_credit}])

    entry_statement = insert(ERPAccountingEntry).values(**entry_values)
    async with Session() as session:
        await session.execute(entry_statement)
        await session.execute(insert_account_balance)
        await session.commit()
    #     await session.execute(entry_section_statement)
