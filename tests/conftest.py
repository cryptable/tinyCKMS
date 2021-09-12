import os
import tempfile
import logging

import pytest
from tinyCKMS import create_app

# with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
#     _data_sql = f.read().decode('utf8')


@pytest.fixture
def app(caplog):
    db_fd, db_path = tempfile.mkstemp()
    caplog.set_level(logging.INFO)
    logging.info(f"Path of database { db_path }")
    app = create_app({
        'TESTING': True,
        'SCHEDULER_JOBSTORES': {'default': f'SQLAlchemyJobStore(url=f"sqlite:///{db_path}"'
                                           ',tablename="task_scheduler")'},
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{db_path}",
    })

    with app.app_context():
        print("Hello")

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()