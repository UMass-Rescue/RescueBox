import { v4 as uuidv4 } from 'uuid';
import log from 'electron-log/main';
import { ResponseBody } from 'src/shared/generated_models';
import { RunJobArgs } from 'src/shared/models';
import JobDb, { JobStatus } from '../models/job';
import { getRaw, showNotification } from '../util';
import ModelAppService from '../services/model-app-service';
import TaskDb from '../models/tasks';

export type JobByIdArgs = {
  uid: string;
};

export type CompleteJobArgs = {
  uid: string;
  endTime: Date;
  status: JobStatus;
  response?: ResponseBody;
  statusText?: string;
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const getJobs = async (_event: any, _arg: any) => {
  return JobDb.getAllJobs().then((jobsDb) => jobsDb.map(getRaw));
};

const completeJob = async (args: CompleteJobArgs) => {
  log.info(
    'Updating job end time and status in the database for job',
    args.uid,
  );
  await JobDb.updateJobEndTime(args.uid, args.endTime);
  await JobDb.updateJobStatus(args.uid, args.status);
  if (args.status === JobStatus.Failed) {
    await JobDb.updateJobStatusText(args.uid, args.statusText!);
  } else {
    await JobDb.updateJobResponse(args.uid, args.response!);
  }
};

const cancelJob = async (_event: any, args: JobByIdArgs) => {
  log.info('Canceling job', args.uid);

  await JobDb.updateJobEndTime(args.uid, new Date());
  await JobDb.updateJobStatus(args.uid, JobStatus.Canceled);
  await JobDb.updateJobStatusText(args.uid, 'Job canceled by user.');
};

const runJob = async (_event: any, arg: RunJobArgs) => {
  log.info(`Creating a job for model ${arg.modelUid}`);

  // Setup job parameters
  const uid = uuidv4();
  log.info('Trying to create a job in the Job model');

  // Get the model service
  const service = await ModelAppService.init(arg.modelUid);
  if (!service.checkValidTaskId(arg.taskUid)) {
    log.error('API route not found for task with order: ', arg.taskUid);
    throw new Error('Error creating job');
  }

  // Create a job in the database
  try {
    await JobDb.createJob(
      uid,
      arg.modelUid,
      new Date(),
      arg.requestBody,
      arg.taskUid,
      arg.taskSchemaAtTimeOfRun,
    );
  } catch (err) {
    log.error(
      `Encountered an error while creating job for model id ${arg.modelUid}`,
    );
    log.error('Error details:', err);
    throw new Error('Error creating job');
  }

  // Call the task service for the particular model,
  // and update the job status after a reply is received
  log.info('Calling task service for model', arg.modelUid);
  service
    .runTask(arg.taskUid, arg.requestBody)
    .then(async (response: ResponseBody) => {
      const job = await JobDb.getJobByUid(uid);
      if (job?.status === JobStatus.Canceled) {
        log.info('Job Canceled: Not updating job information.');
      } else {
        log.info('Success: Updating job information.');
        completeJob({
          uid,
          endTime: new Date(),
          status: JobStatus.Completed,
          response,
        });
        const task = await TaskDb.getTask(arg.taskUid, arg.modelUid);
        if (task) {
          showNotification(
            'Job Completed',
            `Job '${task.shortTitle}' has completed. Click to view results.`,
            `/jobs/${uid}/outputs`,
          );
        }
      }
      return null;
    })
    .catch(async (err) => {
      log.error('Request failed: Updating job information.');
      completeJob({
        uid,
        status: JobStatus.Failed,
        endTime: new Date(),
        statusText: err.message,
      });
      const task = await TaskDb.getTask(arg.taskUid, arg.modelUid);
      if (task) {
        showNotification(
          'Job Failed',
          `Job '${task.shortTitle}' has failed. Click to view details.`,
          `/jobs/${uid}/details`,
        );
      }
      return null;
    });
  log.info('Job model created successfully, fetching job from database.');
  return JobDb.getJobByUid(uid).then(getRaw);
};

const getJobById = async (_event: any, arg: JobByIdArgs) => {
  return JobDb.getJobByUid(arg.uid).then(getRaw);
};

const deleteJobById = async (_event: any, arg: JobByIdArgs) => {
  log.info('Deleting job by id', arg.uid);
  return JobDb.deleteJob(arg.uid);
};

export { getJobs, runJob, getJobById, deleteJobById, cancelJob };
