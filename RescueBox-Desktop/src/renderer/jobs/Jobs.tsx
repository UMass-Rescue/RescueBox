import { Tooltip, TooltipProvider } from '@radix-ui/react-tooltip';
import LoadingScreen from 'src/renderer/components/LoadingScreen';
import {
  Table,
  TableBody,
  TableRow,
  TableCell,
  TableHead,
  TableHeader,
} from '../components/ui/table';
import { Job } from '../../shared/models';
import { useJobs, useMLModels } from '../lib/hooks';
import LoadingIcon from '../components/icons/LoadingIcon';
import { TooltipContent, TooltipTrigger } from '../components/ui/tooltip';
import CompletedIcon from '../components/icons/CompletedIcon';
import FailedIcon from '../components/icons/FailedIcon';
import CanceledIcon from '../components/icons/CanceledIcon';
import {
  ViewButton,
  JobRedButton,
} from '../components/custom_ui/customButtons';

function Jobs() {
  const {
    jobs,
    error: jobsError,
    isLoading: jobsIsLoading,
    mutate: jobsMutate,
  } = useJobs();
  const {
    models,
    error: modelsError,
    isLoading: modelsIsLoading,
  } = useMLModels();

  const getModelName = (uid: string) => {
    return models?.find((model) => model.uid === uid)?.name;
  };

  async function handleDeleteJob(job: Job) {
    await window.job.deleteJobById({ uid: job.uid });
    await jobsMutate();
  }

  async function handleCancelJob(job: Job) {
    await window.job.cancelJob({ uid: job.uid });
    await jobsMutate();
  }

  if (jobsError)
    return <div>failed to load jobs. Error: {jobsError.toString()}</div>;
  if (jobsIsLoading) return <LoadingScreen />;
  if (!jobs) return <div>no jobs</div>;

  if (modelsError)
    return <div>failed to load models. Error: {modelsError.toString()}</div>;
  if (modelsIsLoading) return <LoadingScreen />;
  if (!models) return <div>no models</div>;

  jobs.sort((a, b) => b.startTime.getTime() - a.startTime.getTime());

  return (
    <div className="flex flex-col items-center m-3 gap-8">
      <div className="w-4/5 max-w-full">
        <h1 className="font-bold text-xl md:text-2xl lg:text-4xl mb-4">
          Running Jobs
          {jobsIsLoading && modelsIsLoading && (
            <LoadingIcon className="size-8 text-blue-600" />
          )}
        </h1>
        <div className="shadow-md mt-6">
          <Table className="text-md lg:text-lg">
            <TableHeader className="bg-slate-200">
              <TableRow className="justify-between">
                <TableHead className="pl-4 w-1/3 text-gray-900">
                  Model
                </TableHead>
                <TableHead className="w-1/6 text-gray-900">
                  Start Time
                </TableHead>
                <TableHead className="w-1/6 text-gray-900">End Time</TableHead>
                <TableHead className="w-1/6 text-gray-900 pl-4">
                  Status
                </TableHead>
                <TableHead className="w-1/12" />
                <TableHead className="w-1/12" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.uid}>
                  <TableCell className="pl-4 w-1/3">
                    {getModelName(job.modelUid)}
                  </TableCell>
                  <TableCell className="w-1/6">
                    <div className="flex flex-col">
                      <span>{job.startTime.toLocaleDateString()}</span>
                      <span>{job.startTime.toLocaleTimeString()}</span>
                    </div>
                  </TableCell>
                  <TableCell className="w-1/6">
                    {job.endTime && (
                      <div className="flex flex-col">
                        <span>{job.endTime.toLocaleDateString()}</span>
                        <span>{job.endTime.toLocaleTimeString()}</span>
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="w-1/6 pl-7">
                    <TooltipProvider delayDuration={100}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center">
                            {job.status === 'Running' && (
                              <LoadingIcon className="size-6 ml-[0.5px]" />
                            )}
                            {job.status === 'Completed' && <CompletedIcon />}
                            {job.status === 'Failed' && <FailedIcon />}
                            {job.status === 'Canceled' && <CanceledIcon />}
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="bottom">
                          <p>{job.status}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableCell>
                  <TableCell className="text-center py-4 px-4">
                    <ViewButton job={job} />
                  </TableCell>
                  <TableCell className="text-center py-4 px-4">
                    {job.status === 'Running' ? (
                      <JobRedButton
                        job={job}
                        variant="cancel"
                        handleClick={() => handleCancelJob(job)}
                      />
                    ) : (
                      <JobRedButton
                        job={job}
                        variant="delete"
                        handleClick={() => handleDeleteJob(job)}
                      />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

export default Jobs;
