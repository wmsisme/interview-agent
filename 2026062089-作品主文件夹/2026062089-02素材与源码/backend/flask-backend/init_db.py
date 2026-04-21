#!/usr/bin/env python3
import os
import sys
import logging
from app import create_app
from app.models import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    # 创建应用
    app = create_app()
    
    with app.app_context():
        try:
            # 创建所有表
            logger.info("开始创建数据库表...")
            db.create_all()
            logger.info("数据库表创建完成！")
            
            # 验证表结构
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"数据库中的表: {tables}")
            
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                logger.info(f"表 '{table_name}' 的列:")
                for column in columns:
                    logger.info(f"  - {column['name']}: {column['type']}")
            
            logger.info("数据库初始化完成！")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

if __name__ == '__main__':
    init_database()