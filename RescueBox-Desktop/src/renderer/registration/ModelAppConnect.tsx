/* eslint-disable react/require-default-props */
/* eslint-disable @typescript-eslint/no-shadow */
/* eslint-disable react/jsx-props-no-spreading */
import { Outlet, useNavigate, useParams } from 'react-router-dom';
import { registerModelAppIp, useMLModels, useServers, useServerStatuses } from '../lib/hooks';
import Modal from './Modal';
import StatusComponent from '../jobs/sub-components/StatusComponent';
import RegisterModelButton from '../components/custom_ui/RegisterModelButton';
import LoadingScreen from '../components/LoadingScreen';
import RegistrationTable from './RegistrationTable';



type InvalidServer = {
  isInvalid: boolean;
  cause: 'failed' | 'flask-ml-version' | 'app-metadata-not-set' | null;
};

function ModelAppConnect() {
  // Params from URL
  const { modelUid } = useParams();


  const navigate = useNavigate();

  const {
    data,
    error: serverStatusError,
    isLoading: serverIsLoading,
    isValidating: serverStatusIsValidating,
    mutate: mutateServers,
  } = registerModelAppIp();

  const {
    models,
    error: modelsError,
    isValidating: modelsIsValidating,
    mutate: mutateModels,
  } = useMLModels();

  // Servers Hook
  const { servers, error, isValidating: serversIsValidating } = useServers();

  // Server Statuses Hook
  useServerStatuses(servers);

  const onClose = () => {
  };

  let status = 'Running';
  if (data) {
     navigate('/registration', { replace: true });
  }

  return (
    <Modal title="Register Models" onClose={onClose}>
       <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-bold">Model Server Startup</h1>
              <StatusComponent status={status} />
      </div>
    </Modal>
  );
}
export default ModelAppConnect;
