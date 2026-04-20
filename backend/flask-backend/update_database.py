#!/usr/bin/env python3
"""
更新数据库表结构，添加视频面试相关字段
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.database import db

def update_database():
    """更新数据库表结构"""
    app = create_app()
    
    with app.app_context():
        # 获取数据库连接
        connection = db.engine.connect()
        
        # 检查表是否存在新字段
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('interview_record')]
        
        print("当前列:", columns)
        
        # 需要添加的字段
        new_columns = [
            ('is_video_interview', 'BOOLEAN DEFAULT FALSE'),
            ('video_session_id', 'VARCHAR(200)'),
            ('video_recording_url', 'VARCHAR(500)'),
            ('video_chat_model', 'VARCHAR(100)')
        ]
        
        added_columns = []
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    # 执行ALTER TABLE
                    sql = f"ALTER TABLE interview_record ADD COLUMN {column_name} {column_type};"
                    print(f"执行: {sql}")
                    connection.execute(db.text(sql))
                    added_columns.append(column_name)
                    print(f"✓ 添加列: {column_name}")
                except Exception as e:
                    print(f"✗ 添加列 {column_name} 失败: {e}")
            else:
                print(f"✓ 列已存在: {column_name}")
        
        connection.close()
        
        if added_columns:
            print(f"\n成功添加 {len(added_columns)} 个列: {', '.join(added_columns)}")
        else:
            print("\n所有列都已存在，无需更新")
        
        # 显示更新后的表结构
        print("\n更新后的表结构:")
        inspector = db.inspect(db.engine)
        for col in inspector.get_columns('interview_record'):
            print(f"  - {col['name']}: {col['type']}")

if __name__ == '__main__':
    update_database()