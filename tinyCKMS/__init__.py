import logging
import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask import Flask

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Default configuration
    # TODO uniquify the database URL
    app.config.from_mapping(
        SECRET_KEY='dev',
        SCHEDULER_API_ENABLED=False,
        SCHEDULER_JOBSTORES={"default": SQLAlchemyJobStore(
            url=f"sqlite:///{app.instance_path}/tinyCKMS.sqlite",
            tablename="task_scheduler",
        )},
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{app.instance_path}/tinyCKMS.sqlite",
    )

    # Override configuration
    if test_config is None:
        # TODO: use maybe the from_env pointing to configuration file?
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError as err:
        if err.errno == 17:
            pass
        else:
            logging.warning(f'OS error: {err}')

    # Initialize the database
    from tinyCKMS.db import init_db
    with app.app_context():
        init_db(app)

    # Initialize the scheduler
    from tinyCKMS.tasks import job_scheduler
    tasks.job_scheduler.init_app(app)
    tasks.job_scheduler.start()

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    # Load the non-persisted tasks
    @app.before_first_request
    def load_tasks():
        from tinyCKMS import tasks

    return app
