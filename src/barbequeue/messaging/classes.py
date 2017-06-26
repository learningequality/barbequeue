import json
from collections import namedtuple


class UnknownMessageError(Exception):
    pass


class MessageType(object):
    # Job status messages
    JOB_FAILED = "JOB_FAILED"
    JOB_STARTED = "JOB_STARTED"
    JOB_UPDATED = "JOB_UPDATED"
    JOB_COMPLETED = "JOB_COMPLETED"

    # Job command messages
    START_JOB = "START_JOB"
    CANCEL_JOB = "CANCEL_JOB"


class Message(namedtuple("_Message", ["type", "message"])):
    def serialize(self):
        # check that message type is in one of the message types we define
        assert self.type in (
            t.value for t in list(MessageType)
        ), "Message type not found in predetermined message type list!"

        return json.dumps({"type": self.type, "messsage": self.message})


class SuccessMessage(Message):
    def __new__(cls, job_id, result):
        msg = {'job_id': job_id, 'result': result}
        self = super(SuccessMessage, cls).__new__(cls, type=MessageType.JOB_COMPLETED, message=msg)
        return self


class FailureMessage(Message):
    def __new__(cls, job_id, exc, trace):
        """
        Creates a message indicating an exception was raised when running the job given by job_id. 
        The exc is the exception raised, while trace is a string showing the traceback.
        
        :type trace: str
        :type exc: Exception
        :type job_id: str
        :param job_id: the job_id of the job that failed.
        :param exc: the exception raised during the run of the job.
        :param trace: the string form of the traceback generated by the job.
        :return: a new Message ready to be passed to the messaging backend.
        """

        msg = {'job_id': job_id, 'exception': exc, 'traceback': trace}
        self = super(FailureMessage, cls).__new__(cls, type=MessageType.JOB_FAILED, message=msg)
        return self


class ProgressMessage(Message):
    def __new__(cls, job_id, progress, total_progress, stage=""):
        """
        Creates a Message that updates the progress for the job given by job_id.
       
        :param job_id: The job_id of the job to update.
        :param progress: the current progress achieved by the running function so far. It should be less than or equal to the value of total_progress.
        :param total_progress: the total amount of progress achievable by the function. This can correspond directly to a concrete action done by the function (such as total number of videos to download, the number of items to process etc.)
        :param stage: an optional argument giving a short name for the current stage the job is on, e.g. 'downloading videos', 'loading subtitles', etc.
        :return: None
        
        :type job_id: str
        :type progress: float
        :type total_progress: float
        :type stage: str
        """
        msg = {'job_id': job_id, 'progress': progress, 'total_progress': total_progress, 'stage': stage}
        self = super(ProgressMessage, cls).__new__(cls, type=MessageType.JOB_UPDATED, message=msg)
        return self
