from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class ApplicationStatusEnum(enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PROBLEM = "problem"

class WorkDayStatusEnum(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FINISHED = "finished"

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
    taken_at = Column(DateTime, nullable=True)  # Время взятия в обработку

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
    work_days = relationship("WorkDay", back_populates="employee")

class WorkDay(Base):
    __tablename__ = "work_days"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee = relationship("Employee", back_populates="work_days")
    date = Column(DateTime, nullable=False)  # Дата рабочего дня
    start_time = Column(DateTime, nullable=True)  # Время начала рабочего дня
    end_time = Column(DateTime, nullable=True)  # Время окончания рабочего дня
    total_work_time = Column(Integer, default=0)  # Общее время работы в секундах
    total_break_time = Column(Integer, default=0)  # Общее время перерывов в секундах
    status = Column(Enum(WorkDayStatusEnum), default=WorkDayStatusEnum.ACTIVE)
    applications_processed = Column(Integer, default=0)  # Количество обработанных заявлений
    breaks = relationship("WorkBreak", back_populates="work_day")

class WorkBreak(Base):
    __tablename__ = "work_breaks"
    id = Column(Integer, primary_key=True)
    work_day_id = Column(Integer, ForeignKey("work_days.id"), nullable=False)
    work_day = relationship("WorkDay", back_populates="breaks")
    start_time = Column(DateTime, nullable=False)  # Время начала перерыва
    end_time = Column(DateTime, nullable=True)  # Время окончания перерыва
    duration = Column(Integer, default=0)  # Продолжительность перерыва в секундах 