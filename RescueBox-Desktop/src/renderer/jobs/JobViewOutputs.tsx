import { useParams } from 'react-router-dom';
import {
  directoryResponse,
  batchDirectoryResponse,
} from 'src/shared/dummy_data/file_response';
import markdownResponseBody from 'src/shared/dummy_data/markdown_response';
import {
  batchFileResponse,
  fileResponse,
} from 'src/shared/dummy_data/batchfile_response';
import isDummyMode from 'src/shared/dummy_data/set_dummy_mode';
import {
  textResponse,
  batchTextResponse,
} from 'src/shared/dummy_data/batchtext_response';
import { useJob, useMLModel, useTask } from '../lib/hooks';
import PreviewResponseBody from './PreviewResponseBody';
import StatusComponent from './sub-components/StatusComponent';
import { match } from 'ts-pattern';

function JobViewOutputs() {
  const { jobId } = useParams();

  const { data: job, error: jobError, isLoading: jobIsLoading } = useJob(jobId);

  const {
      data: model,
      error: modelError,
      isLoading: modelIsLoading,
    } = useMLModel(job?.modelUid);

    const {
      data: task,
      error: taskError,
      isLoading: taskIsLoading,
    } = useTask(job?.taskUid, model?.uid);

  if (!job || !jobId) return <div>no job id</div>;
  if (jobIsLoading) return <div>loading job..</div>;
  if (jobError)
    return <div>failed to load job. Error: {jobError.toString()}</div>;

  if (modelError)
    return <div>failed to run job. Error: {modelError.toString()}</div>;

  if (taskError)
    return <div>failed to run job. Error: {taskError.toString()}</div>;

  const { response, statusText } = job;

  if (!response) return <div className="p-2 border border-red-400 bg-slate-200 rounded-lg w-full">
                        <StatusComponent status={job.status} />
                         {statusText}
                        </div>;

  if (isDummyMode) {
    return (
      <div className="border border-gray-300 rounded-lg m-1 p-6 flex flex-col gap-4 shadow-md bg-white">

        <PreviewResponseBody response={markdownResponseBody} />
        <PreviewResponseBody response={fileResponse} />
        <PreviewResponseBody response={batchFileResponse} />
        <PreviewResponseBody response={directoryResponse} />
        <PreviewResponseBody response={batchDirectoryResponse} />
        <PreviewResponseBody response={textResponse} />
        <PreviewResponseBody response={batchTextResponse} />
      </div>
    );
  }

  const msg =  match(response).with({ output_type: 'text' }, (response) => {
    if (response.value.includes('Input error')) {
      return true;
    }
  });

  return (
    <div className="border border-gray-300 rounded-lg m-1 p-6 flex flex-col gap-4 shadow-md bg-white">
      <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-bold">{task?.shortTitle}</h1>
                <StatusComponent status={job.status} />
      </div>

      <div className="flex flex-col gap-2">
              <h1 className="font-bold text-sm xl:text-base">Results</h1>
              {msg ? (
                <div className="p-4 border border-green-400 bg-slate-200 rounded-lg w-full">
                  <PreviewResponseBody response={response} />
                </div>
              ):  (
                <div className="p-2 border border-red-400 bg-slate-200 rounded-lg w-full">
                  <PreviewResponseBody response={response} />
                </div>
              )}
      </div>
      <div className="w-full flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <h1 className="font-bold text-sm xl:text-base">Start Time</h1>
              <div className="p-2 border border-slate-400 bg-slate-200 rounded-lg w-full">
                {job.startTime.toLocaleString('en-US', { timeZone: 'EST' })}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <h1 className="font-bold text-sm xl:text-base">End Time</h1>
              <div className="p-2 border border-slate-400 bg-slate-200 rounded-lg w-full">
                {job.endTime
                  ? job.endTime.toLocaleString('en-US', { timeZone: 'EST' })
                  : 'Pending'}
              </div>
            </div>
      </div>
    </div>
  );
}

export default JobViewOutputs;
