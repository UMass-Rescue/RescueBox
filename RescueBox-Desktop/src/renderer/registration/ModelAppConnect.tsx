/* eslint-disable react/require-default-props */
/* eslint-disable @typescript-eslint/no-shadow */
/* eslint-disable react/jsx-props-no-spreading */
import { useForm, SubmitHandler } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { mutate } from 'swr';
import { useState } from 'react';
import { ModelAppStatus } from 'src/shared/models';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { useMLModel, useServer } from '../lib/hooks';
import LoadingIcon from '../components/icons/LoadingIcon';
import Modal from './Modal';

type ConnectInputs = {
  ip: string;
  port: string;
};

type InvalidServer = {
  isInvalid: boolean;
  cause: 'failed' | 'flask-ml-version' | 'app-metadata-not-set' | null;
};

function ModelAppConnect() {
  // Params from URL
  const { modelUid } = useParams();
  if (!modelUid) throw new Error('modelUid is required');

  const navigate = useNavigate();

  const [isConnecting, setIsConnecting] = useState(false);
  const [invalidServer, setInvalidServer] = useState<InvalidServer>({
    isInvalid: false,
    cause: null,
  } satisfies InvalidServer);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
  } = useForm<ConnectInputs>({ mode: 'onChange' });

  const {
    data: model,
    error: modelError,
    isLoading: modelIsLoading,
  } = useMLModel(modelUid);

  const {
    data: server,
    error: serverError,
    isLoading: serverIsLoading,
  } = useServer(modelUid, {
    shouldRetryOnError: false,
  });

  if (serverError) {
    return <p>Error: {serverError.message}</p>;
  }
  if (serverIsLoading) return <LoadingIcon />;

  const onSubmit: SubmitHandler<ConnectInputs> = async (data) => {
    setIsConnecting(true);
    try {
      if (modelUid === 'new_model') {
        await window.registration.registerModelAppIp({
          serverAddress: data.ip,
          serverPort: Number(data.port),
        });
      } else {
        await window.registration.registerModelAppIp({
          modelUid,
          serverAddress: data.ip,
          serverPort: Number(data.port),
        });
        const status = await window.registration.getModelAppStatus({
          modelUid,
        });
        if (
          status === ModelAppStatus.Error ||
          status === ModelAppStatus.Offline
        ) {
          throw new Error('Failed to connect to the model server');
        }
      }
      await mutate(() => true, undefined);
      navigate('/registration', {
        replace: true,
      });
    } catch (error) {
      if (
        error instanceof Error &&
        error.message.includes('404 APP_METADATA_SLUG not found on server')
      ) {
        setInvalidServer({
          isInvalid: true,
          cause: 'flask-ml-version',
        });
      } else if (
        error instanceof Error &&
        error.message.includes('App metadata not set')
      ) {
        setInvalidServer({
          isInvalid: true,
          cause: 'app-metadata-not-set',
        });
      } else {
        setInvalidServer({
          isInvalid: true,
          cause: 'failed',
        });
      }
    }
    setIsConnecting(false);
  };

  if (modelIsLoading) return <LoadingIcon />;
  if (modelError) return <p>Error: {modelError.message}</p>;

  const onClose = () => {
    navigate('/registration', { replace: true });
  };

  return (
    <Modal title="Register Model Application" onClose={onClose}>
      <div className="flex flex-col gap-y-3">
        {model && (
          <h2 className="font-semibold flex flex-col space-y-2">
            <p>{model.name}</p>
            <p className="text-sm font-normal">Version {model.version}</p>
          </h2>
        )}
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex items-center space-x-2"
        >
          <div className="grid grid-container grid-cols-3 gap-2">
            <Label htmlFor="ip" className="text-sm font-medium col-span-2">
              Server IP Address
            </Label>
            <Label htmlFor="port" className="text-sm font-medium col-span-1">
              Port
            </Label>
            <Input
              {...register('ip', {
                required: 'This field is required',
                onChange: () =>
                  setInvalidServer({ isInvalid: false, cause: null }),
                pattern: {
                  value:
                    /^localhost|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
                  message: 'Invalid IP format',
                },
              })}
              defaultValue={server?.serverAddress || ''}
              className="col-span-2"
            />
            <Input
              {...register('port', {
                required: 'This field is required',
                onChange: () =>
                  setInvalidServer({ isInvalid: false, cause: null }),
                pattern: {
                  value:
                    /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/,
                  message: 'Invalid Port format',
                },
              })}
              defaultValue={server?.serverPort || ''}
              className="col-span-1"
            />
            <Button
              type="button"
              variant="outline"
              className="col-span-2 w-fit"
              onClick={() =>
                setValue('ip', '127.0.0.1', { shouldValidate: true })
              }
            >
              127.0.0.1
            </Button>
            <Button
              type="button"
              variant="outline"
              className="col-span-1 w-fit"
              onClick={() => setValue('port', '5000', { shouldValidate: true })}
            >
              5000
            </Button>
          </div>
          <Button
            size="default"
            className="px-3 self-end w-32 flex items-center justify-center"
            disabled={!isValid || isConnecting}
          >
            {isConnecting ? (
              <LoadingIcon className="text-white mr-0 ml-0" />
            ) : (
              'Connect'
            )}
          </Button>
        </form>
        {errors.ip && (
          <span className="text-red-500 text-xs -mt-2">
            Please enter a valid server address.
          </span>
        )}
        {errors.port && (
          <span className="text-red-500 text-xs -mt-2">
            Please enter a valid port number.
          </span>
        )}
        {invalidServer.isInvalid && invalidServer.cause === 'failed' && (
          <span className="text-red-500 text-xs -mt-2">
            Failed to reach the server. Make sure it is running at the specified
            IP address and port.
          </span>
        )}
        {invalidServer.isInvalid &&
          invalidServer.cause === 'flask-ml-version' && (
            <span className="text-red-500 text-xs">
              Failed to connect to the server. Make sure the Flask-ML version
              installed on the server is &ge; 0.2.5
            </span>
          )}
        {invalidServer.isInvalid &&
          invalidServer.cause === 'app-metadata-not-set' && (
            <span className="text-red-500 text-xs">
              Failed to connect to the server. Make sure that your server has
              app metadata added to it.
            </span>
          )}
      </div>
    </Modal>
  );
}
export default ModelAppConnect;
