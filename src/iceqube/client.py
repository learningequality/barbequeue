from iceqube.common.classes import Job, State
from iceqube.storage.backends import inmem as storage_inmem

MEMORY = storage_inmem.StorageBackend.MEMORY


class Client(object):
    def __init__(self, app, storage_path=MEMORY):
        self.storage = storage_inmem.StorageBackend(app, app, storage_path)

    def schedule(self, func, *args, **kwargs):
        """
        Schedules a function func for execution.

        One special parameter is track_progress. If passed in and not None, the func will be passed in a
        keyword parameter called update_progress:

        def update_progress(progress, total_progress, stage=""):

        The running function can call the update_progress function to notify interested parties of the function's
        current progress.

        Another special parameter is the "cancellable" keyword parameter. When passed in and not None, a special
        "check_for_cancel" parameter is passed in. When called, it raises an error when the user has requested a job
        to be cancelled.

        The caller can also pass in any pickleable object into the "extra_metadata" parameter. This data is stored
        within the job and can be retrieved when the job status is queried.

        All other parameters are directly passed to the function when it starts running.

        :type func: callable or str
        :param func: A callable object that will be scheduled for running.
        :return: a string representing the job_id.
        """

        # if the func is already a job object, just schedule that directly.
        if isinstance(func, Job):
            job = func
        # else, turn it into a job first.
        else:
            job = Job(func, *args, **kwargs)

        job.track_progress = kwargs.pop('track_progress', False)
        job.cancellable = kwargs.pop('cancellable', False)
        job.extra_metadata = kwargs.pop('extra_metadata', {})
        job_id = self.storage.schedule_job(job)
        return job_id

    def cancel(self, job_id):
        """
        Mark a job as canceling, and let the scheduler pick this up to initiate
        the cancel of the job.

        :param job_id: the job_id of the Job to cancel.
        """
        self.storage.mark_job_as_canceling(job_id)

    def all_jobs(self):
        """
        Return all the jobs scheduled, queued, running, failed or completed.
        Returns: A list of all jobs.

        """
        return self.storage.get_all_jobs()

    def status(self, job_id):
        """
        Returns a Job object corresponding to the job_id. From there, you can query for the following attributes:

        - function string to run
        - its current state (see Job.State for the list of states)
        - progress (returning an int), total_progress (returning an int), and percentage_progress
        (derived from running job.progress/total_progress)
        - the job.exception and job.traceback, if the job's function returned an error

        :param job_id: the job_id to get the Job object for
        :return: the Job object corresponding to the job_id
        """
        return self.storage.get_job(job_id)

    def wait(self, job_id, timeout=None):
        """
        Wait until the job given by job_id has a new update.

        :param job_id: the id of the job to wait for.
        :param timeout: how long to wait for a job state change before timing out.
        :return: Job object corresponding to job_id
        """
        return self.storage.wait_for_job_update(job_id, timeout=timeout)

    def wait_for_completion(self, job_id, timeout=None):
        """
        Wait for the job given by job_id to change to COMPLETED or CANCELED. Raises a
        iceqube.exceptions.TimeoutError if timeout is exceeded before each job change.

        :param job_id: the id of the job to wait for.
        :param timeout: how long to wait for a job state change before timing out.
        """
        while 1:
            job = self.wait(job_id, timeout=timeout)
            if job.state in [State.COMPLETED, State.FAILED, State.CANCELED]:
                return job
            else:
                continue

    def clear(self, force=False):
        """
        Clear all jobs that have succeeded or failed.
        :type force: bool
        :param force: Whether to clear all jobs from the job storage queue, regardless if they've been completed or not.
        """
        self.storage.clear(force=force)
