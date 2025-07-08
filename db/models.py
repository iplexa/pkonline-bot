from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class ApplicationStatusEnum(enum.Enum):
    QUEUED = "queued"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROBLEM = "problem"

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    fio = Column(String, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    is_priority = Column(Boolean, default=False)
    status = Column(Enum(ApplicationStatusEnum), default=ApplicationStatusEnum.QUEUED)
    status_reason = Column(Text, nullable=True)
    queue_type = Column(String, nullable=False)  # 'lk' или 'epgu'
    processed_by_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    processed_by = relationship("Employee", back_populates="applications")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # 'lk', 'epgu', 'escalation'
    employees = relationship("Employee", secondary="employee_groups", back_populates="groups")

class EmployeeGroup(Base):
    __tablename__ = "employee_groups"
    employee_id = Column(Integer, ForeignKey("employees.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    tg_id = Column(String, unique=True, nullable=False)
    fio = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    applications = relationship("Application", back_populates="processed_by")
    groups = relationship("Group", secondary="employee_groups", back_populates="employees") 