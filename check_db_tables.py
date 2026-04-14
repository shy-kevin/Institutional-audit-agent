"""
检查数据库表结构
"""

from db.mysql_session import engine, Base
from sqlalchemy import inspect

inspector = inspect(engine)

print("数据库中的表:")
for table_name in inspector.get_table_names():
    print(f"  - {table_name}")

print("\n检查模板相关表:")
if "templates" in inspector.get_table_names():
    print("  [OK] templates 表存在")
    columns = inspector.get_columns("templates")
    print("  列:")
    for col in columns:
        print(f"    - {col['name']}: {col['type']}")
else:
    print("  [X] templates 表不存在")

if "template_sections" in inspector.get_table_names():
    print("  [OK] template_sections 表存在")
    columns = inspector.get_columns("template_sections")
    print("  列:")
    for col in columns:
        print(f"    - {col['name']}: {col['type']}")
else:
    print("  [X] template_sections 表不存在")
