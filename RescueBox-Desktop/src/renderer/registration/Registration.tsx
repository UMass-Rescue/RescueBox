import { Link, Outlet, useNavigate } from 'react-router-dom';
import RegistrationTable from './RegistrationTable';
import Models from '../models/Models';
import ModelsTable from '../models/ModelsTable';
import { registerModelAppIp, useMLModels, useServers, useServerStatuses } from '../lib/hooks';
import LoadingScreen from '../components/LoadingScreen';
import LoadingIcon from '../components/icons/LoadingIcon';
import { GreenCircleIcon } from '../components/icons/CircleIcons';
import Modal from './Modal';
import { Button } from '@shadcn/button';

function Registration() {
  const navigate = useNavigate();

    // Servers Hook
    const { servers, error, isValidating: serversIsValidating } = useServers();

    const {
      data,
    } = registerModelAppIp();

       // Server Statuses Hook
       const {
        serverStatuses,
    } = useServerStatuses(servers);

    const {
      models,
    } = useMLModels();

    if (!models) return <div>no models</div>;
    if (!serverStatuses) return <LoadingScreen />;

  const onClose = () => {
    navigate('/models', { replace: true });
  };
  return (
    <Modal title="Models loaded Succesfully, click ok to continue" onClose={onClose}>
            <div className="flex justify-between items-center mb-4">

              <Button
                variant="outline"
                className="block mx-auto hover:-translate-y-0.5 transition-all py-2 px-6 rounded-lg bg-green-600 hover:bg-green-500"
                onClick = {onClose}
              >
                OK
              </Button>

          </div>
    </Modal>
  );
}

export default Registration;
