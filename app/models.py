from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, default="")
    recurrent = Column(Boolean, default=False)
    expected_monthly = Column(Float, default=0.0)

    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="category", cascade="all, delete-orphan")

class Subcategory(Base):
    __tablename__ = "subcategories"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String, nullable=False)
    description = Column(String, default="")
    labels = Column(String, default="")

    category = relationship("Category", back_populates="subcategories")
    expenses = relationship("Expense", back_populates="subcategory", cascade="all, delete-orphan")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, default="")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    expected = Column(Boolean, default=False)

    category = relationship("Category", back_populates="expenses")
    subcategory = relationship("Subcategory", back_populates="expenses")

class Income(Base):
    __tablename__ = "incomes"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, default="")

class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    expected_amount = Column(Float, default=0.0)
