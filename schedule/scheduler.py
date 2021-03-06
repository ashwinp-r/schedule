# module: schedule
# file: scheduler.py
import datetime
import logging
import time

from schedule.job import Job

logger = logging.getLogger('schedule')


class CancelJob(object):
    """
    Can be returned from a job to unschedule itself.
    """
    pass


class Scheduler(object):
    """
    Objects instantiated by the :class:`Scheduler <Scheduler>` are
    factories to create jobs, keep record of scheduled jobs and
    handle their execution.
    """

    def __init__(self):
        self.jobs = []

    def run_pending(self):
        """
        Run all jobs that are scheduled to run.

        Please note that it is *intended behavior that run_pending()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you only call run_pending()
        in one hour increments then your job won't be run 60 times in
        between but only once.
        """
        runnable_jobs = (job for job in self.jobs if job.should_run)
        for job in sorted(runnable_jobs):
            self._run_job(job)

    def run_all(self, delay_seconds=0):
        """
        Run all jobs regardless if they are scheduled to run or not.

        A delay of `delay` seconds is added between each job. This helps
        distribute system load generated by the jobs more evenly
        over time.

        :param delay_seconds: A delay added between every executed job
        """
        logger.info('Running *all* %i jobs with %is delay inbetween',
                    len(self.jobs), delay_seconds)
        for job in self.jobs[:]:
            self._run_job(job)
            time.sleep(delay_seconds)

    def clear(self, tag=None):
        """
        Deletes scheduled jobs marked with the given tag, or all jobs
        if tag is omitted.

        :param tag: An identifier used to identify a subset of
                    jobs to delete
        """
        if tag is None:
            del self.jobs[:]
        else:
            self.jobs[:] = (job for job in self.jobs if tag not in job.tags)

    def cancel_job(self, job):
        """
        Delete a scheduled job.

        :param job: The job to be unscheduled
        """
        try:
            self.jobs.remove(job)
        except ValueError:
            pass

    def every(self, interval=1):
        """
        Schedule a new periodic job.

        :param interval: A quantity of a certain time unit
        :return: An unconfigured :class:`Job <Job>`
        """
        job = Job(interval, self)
        return job

    def _check_returned_value(self, job, ret):
        if isinstance(ret, CancelJob) or ret is CancelJob:
            self.cancel_job(job)

    def _run_job(self, job):
        ret = job.run()
        self._check_returned_value(job, ret)

    @property
    def next_run(self):
        """
        Datetime when the next job should run.

        :return: A :class:`~datetime.datetime` object
        """
        if not self.jobs:
            return None
        return min(self.jobs).next_run

    @property
    def idle_seconds(self):
        """
        :return: Number of seconds until
                 :meth:`next_run <Scheduler.next_run>`.
        """
        return (self.next_run - datetime.datetime.now()).total_seconds()
