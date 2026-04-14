"""
检查数据库中的模板数据
"""

from db.mysql_session import SessionLocal
from models.template import Template

db = SessionLocal()

try:
    templates = db.query(Template).all()
    print(f"数据库中的模板数量: {len(templates)}")
    
    for template in templates:
        print(f"\n模板ID: {template.id}")
        print(f"模板名称: {template.name}")
        print(f"是否删除: {template.is_deleted}")
        print(f"创建者ID: {template.creator_id}")
        
finally:
    db.close()
