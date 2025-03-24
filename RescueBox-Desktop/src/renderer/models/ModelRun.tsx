import LoadingScreen from 'src/renderer/components/LoadingScreen';
import { cn } from 'src/renderer/lib/utils';
import { NavLink, Outlet, useParams } from 'react-router-dom';
import { useApiRoutes, useMLModel } from '../lib/hooks';

function ModelRun() {
  const { modelUid } = useParams();

  const {
    data: apiRoutes,
    error: apiRoutesError,
    isLoading: apiRoutesIsLoading,
  } = useApiRoutes(modelUid);

  const {
    data: model,
    error: modelError,
    isLoading: modelIsLoading,
  } = useMLModel(modelUid);

  if (!modelUid) {
    return <div>Error: Model UID not found</div>;
  }

  if (!apiRoutes) {
    return <LoadingScreen />;
  }
  if (apiRoutesIsLoading) {
    return <LoadingScreen />;
  }
  if (apiRoutesError) {
    return <div>Error loading API routes</div>;
  }

  if (modelIsLoading) {
    return <LoadingScreen />;
  }
  if (modelError) {
    return <div>Error loading model: {modelError.message}</div>;
  }
  if (!model) {
    return <div>No model found</div>;
  }

  return (
    <div className="flex flex-grow h-full">
      <div className="w-1/4 p-4 sticky top-24 self-start">
        <h1 className="text-2xl font-bold mb-4">{model.name}</h1>
        <div className="flex flex-col space-y-1">
          {apiRoutes
            .sort((a, b) => a.order - b.order)
            .map((apiRoute) => (
              <NavLink
                key={apiRoute.order}
                to={`/models/${modelUid}/run/${apiRoute.order}`}
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
                {apiRoute.short_title || `Untitled Task ${apiRoute.order}`}
              </NavLink>
            ))}
        </div>
      </div>
      <div className="w-3/4 p-5 border-l-2 mb-2 scrollable">
        <Outlet context={apiRoutes} />
      </div>
    </div>
  );
}

export default ModelRun;
