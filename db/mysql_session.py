"""
MySQL数据库会话管理模块
提供数据库连接池和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
from config import settings

engine = create_engine(
    settings.MYSQL_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """
    获取数据库会话
    
    用于FastAPI依赖注入，自动管理数据库会话的生命周期
    
    Yields:
        Generator: 数据库会话对象
    
    Example:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    
    创建所有定义的表结构
    """
    Base.metadata.create_all(bind=engine)
