import RegisterModelButton from 'src/renderer/components/custom_ui/RegisterModelButton';
import { useMLModels, useServers, useServerStatuses } from '../lib/hooks';
import LoadingIcon from '../components/icons/LoadingIcon';
import LoadingScreen from '../components/LoadingScreen';
import ModelsTable from './ModelsTable';

function Models() {
  // ML Models Hook
  const {
    models,
    error: modelsError,
    isValidating: modelsIsValidating,
    mutate: mutateModels,
  } = useMLModels();

  // Servers Hook
  const { servers, error, isValidating: serversIsValidating } = useServers();

  // Server Statuses Hook
  const {
    serverStatuses,
    error: statusError,
    isValidating: statusIsValidating,
  } = useServerStatuses(servers);

  if (modelsError)
    return <div>failed to load models. Error: {modelsError.toString()}</div>;
  if (modelsIsValidating) return <LoadingScreen />;
  if (!models) return <div>no models</div>;

  if (error) return <div>failed to load {error.toString()}</div>;
  if (serversIsValidating) return <LoadingScreen />;
  if (!servers) return <div>no servers</div>;

  if (statusError)
    return <div>failed to load status. Error: {statusError.toString()}</div>;
  if (!serverStatuses) return <LoadingScreen />;

  const existingModels = models.filter((model) => !model.isRemoved);

  const onModels = existingModels.filter(
    (model) => serverStatuses[model.uid] === 'Online',
  );

  const offModels = existingModels.filter(
    (model) => serverStatuses[model.uid] !== 'Online',
  );

  return (
    <div className="flex flex-col items-center m-3">
      <div className="w-4/5 max-w-full">
        <div className="font-bold text-xl md:text-2xl lg:text-4xl mb-5 flex flex-row gap-8 items-center">
          <div className="flex flex-row justify-between w-full">
            Available Models
            {onModels.length === 0 && <RegisterModelButton replace={false} />}
          </div>
          {statusIsValidating && (
            <LoadingIcon className="size-8 text-blue-600" />
          )}
        </div>
        <ModelsTable
          models={onModels}
          serverStatuses={serverStatuses}
          mutateModels={mutateModels}
        />
        {offModels.length > 0 && (
          <h1 className="font-bold text-xl md:text-2xl lg:text-4xl my-5 flex flex-row gap-8 items-center">
            Unavailable Models
            {statusIsValidating && (
              <LoadingIcon className="size-8 text-blue-600" />
            )}
          </h1>
        )}
        {offModels.length > 0 && (
          <ModelsTable
            models={offModels}
            serverStatuses={serverStatuses}
            mutateModels={mutateModels}
          />
        )}
      </div>
    </div>
  );
}

export default Models;
