from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()


def _tune_sqlite_connection(dbapi_connection, _connection_record):
    """SQLite 默认 journal 模式下并发写会直接抛 'database is locked'。

    踩过的坑：结束面试时 stop_interview 与 socket disconnect 会各触发一次
    end_interview，两次写叠加曾稳定复现 database is locked。
    这里开启 WAL（读不再阻塞写）并设置 30s busy_timeout（写锁等待而非立刻失败）。
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA busy_timeout=30000')
        cursor.close()
    except Exception:
        # 非 SQLite（如 MySQL）或驱动不支持时静默跳过
        pass


def init_app(app):
    db.init_app(app)

    with app.app_context():
        try:
            if db.engine.dialect.name == 'sqlite':
                event.listen(db.engine, 'connect', _tune_sqlite_connection)
        except Exception:
            pass
        db.create_all()
