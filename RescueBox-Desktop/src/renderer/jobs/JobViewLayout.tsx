import { NavLink, Outlet, useParams } from 'react-router-dom';

import { cn } from '../lib/utils';
import { useJob, useMLModel } from '../lib/hooks';
import LoadingScreen from '../components/LoadingScreen';

function JobView() {
  const { jobId } = useParams();

  const { data: job, error: jobError, isLoading: jobIsLoading } = useJob(jobId);

  const {
    data: model,
    error: modelError,
    isLoading: modelIsLoading,
  } = useMLModel(job?.modelUid);

  if (jobIsLoading) return <LoadingScreen />;
  if (jobError)
    return <div>failed to load job. Error: {jobError.toString()}</div>;
  if (!job) return <div>no job</div>;

  if (modelIsLoading) return <LoadingScreen />;
  if (modelError)
    return <div>failed to load model. Error: {modelError.toString()}</div>;
  if (!model) return <div>no model</div>;

  return (
    <div className="flex flex-grow h-full">
      <div className="w-1/4 p-4 sticky top-24 self-start">
        <h1 className="text-2xl font-bold mb-4">{model.name}</h1>
        <div className="flex flex-col space-y-1">
          <NavLink
            to={`/jobs/${jobId}/details`}
            replace
            className={({ isActive }) =>
              isActive
                ? cn(
                    'text-md md:text-md lg:text-md xl:text-md',
                    'bg-gray-200 p-2 font-semibold rounded',
                    'p-2 rounded',
                  )
                : cn(
                    'text-md md:text-md lg:text-md xl:text-md',
                    'hover:bg-gray-200 p-2 rounded',
                    'p-2 rounded',
                  )
            }
          >
            Details
          </NavLink>
          <NavLink
            to={`/jobs/${jobId}/outputs`}
            className={({ isActive }) =>
              isActive
                ? cn(
                    'text-md md:text-md lg:text-md xl:text-md',
                    'bg-gray-200 p-2 font-semibold rounded',
                    'p-2 rounded',
                  )
                : cn(
                    'text-md md:text-md lg:text-md xl:text-md',
                    'hover:bg-gray-200 p-2 rounded',
                    'p-2 rounded',
                  )
            }
          >
            Results
          </NavLink>
        </div>
      </div>
      <div className="w-3/4 p-5 border-l-2 mb-2 scrollable">
        <Outlet />
      </div>
    </div>
  );
}

export default JobView;
