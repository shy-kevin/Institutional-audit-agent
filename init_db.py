"""
数据库初始化脚本
用于创建MySQL和PostgreSQL数据库
"""

import pymysql
import psycopg2
from config import settings


def init_mysql():
    """
    初始化MySQL数据库
    连接到MySQL服务器并创建数据库
    """
    try:
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD
        )
        
        cursor = connection.cursor()
        
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        
        print(f"MySQL数据库 '{settings.MYSQL_DATABASE}' 创建成功!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"MySQL数据库创建失败: {e}")


def init_postgres():
    """
    初始化PostgreSQL数据库
    连接到PostgreSQL服务器并创建数据库
    """
    try:
        connection = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database="postgres"
        )
        
        connection.autocommit = True
        cursor = connection.cursor()
        
        cursor.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DATABASE}'"
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {settings.POSTGRES_DATABASE}")
            print(f"PostgreSQL数据库 '{settings.POSTGRES_DATABASE}' 创建成功!")
        else:
            print(f"PostgreSQL数据库 '{settings.POSTGRES_DATABASE}' 已存在!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"PostgreSQL数据库创建失败: {e}")


if __name__ == "__main__":
    print("开始初始化数据库...")
    init_mysql()
    init_postgres()
    print("数据库初始化完成!")
