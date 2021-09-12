# interval example
import logging
import pickle

from flask_apscheduler import APScheduler
from tinyCKMS.db import db

job_scheduler = APScheduler()
custom_tasks = {}


# Helper function to execute dynamic created functions
def _run_function(*task_args, **task_kwargs):
    exec(custom_tasks[task_args[0]])


# Helper function to check if the scheduler already has the job
def _has_job(job_id):
    for job in job_scheduler.get_jobs():
        if job.id == job_id:
            return True
    return False


def _add_task_scheduler(task_id, task_func_str, job_trigger, **job_kwargs):
    """
    This function is used to add dynamic python code to the scheduler to perform regular tasks. The function
    is used during startup to import the new tasks from DB to scheduler or during the creation of a new task
    in the CLI or GUI
    :param task_id: unique identifier of the task
    :param task_func_str: string representation of the python script to be executed
    :param job_trigger: kind of trigger 'date', 'interval', 'cron'
    :param job_kwargs: parameters used by the trigger (see APScheduler documentation)
    :return: None
    """
    try:
        c = compile(task_func_str, '<string>', 'exec')
        custom_tasks[task_id] = c
        if _has_job(task_id):
            job_scheduler.remove_job(task_id)
            job_scheduler.add_job(task_id, _run_function, trigger=job_trigger, task_args=[task_id], **job_kwargs)
        else:
            job_scheduler.add_job(task_id, _run_function, trigger=job_trigger, task_args=[task_id], **job_kwargs)
    except SyntaxError as e:
        logging.error(f"Compilation failed (Syntax Error): {e}")
        raise e
    except ValueError as e:
        logging.error(f"Compilation failed (Syntax Error): {e}")
        raise e


class Task(db.Model):
    task_id = db.Column(db.String(80), primary_key=True)
    task_trigger = db.Column(db.String(10), nullable=False)
    task_code = db.Column(db.Text, nullable=False)
    task_labels = db.Column(db.String(128))
    task_params = db.Column(db.PickleType, nullable=False)


def add_task(task_id, task_func_str, task_labels, job_trigger, **job_kwargs):
    """
    Main function to add a task to the system.
    :param task_id: unique identifier of the task
    :param task_func_str: string representation of the python script to be executed
    :param task_labels: labels for categorization of the tasks
    :param job_trigger: kind of trigger 'date', 'interval', 'cron'
    :param job_kwargs: parameters used by the trigger (see APScheduler documentation)
    :return: None
    """
    _add_task_scheduler(task_id, task_func_str, job_trigger, **job_kwargs)
    task = Task(task_id=task_id,
                task_trigger=job_trigger,
                task_code=task_func_str,
                task_labels=task_labels,
                task_params=job_kwargs)
    db.session.add(task)
    db.session.commit()


# ------------------------------------------------------------------------------------------------------


# Default tasks: expiration notification checking
@job_scheduler.task('interval', id='expiry_notification', seconds=10, misfire_grace_time=900)
def expiry_notification():

    print('Check certificate old expiry')
