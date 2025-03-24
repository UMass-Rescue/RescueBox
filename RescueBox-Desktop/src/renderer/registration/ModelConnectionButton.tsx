import { ModelAppStatus, ModelServer } from 'src/shared/models';
import { KeyedMutator } from 'swr';
import { Link } from 'react-router-dom';
import { useServerStatus } from '../lib/hooks';
import { ConnectIcon, DisconnectIcon } from '../components/icons/ConnectIcon';
import { Button } from '../components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';

function ModelConnectionButton({
  modelUid,
  mutate,
}: {
  modelUid: string;
  mutate: KeyedMutator<ModelServer[]>;
}) {
  const {
    serverStatus,
    isValidating,
    mutate: mutateServerStatus,
  } = useServerStatus(modelUid);

  // eslint-disable-next-line @typescript-eslint/no-shadow
  async function disconnect(modelUid: string) {
    await window.registration.unregisterModelAppIp({ modelUid });
    await mutate();
    await mutateServerStatus();
  }

  if (isValidating) {
    return (
      <Button
        variant="outline"
        disabled
        className="hover:-translate-y-0.5 transition-all py-2 rounded-lg"
      >
        <ConnectIcon />
      </Button>
    );
  }
  if (serverStatus !== ModelAppStatus.Online) {
    return (
      <TooltipProvider delayDuration={100}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Link to={`/registration/${modelUid}`} replace>
              <Button
                variant="outline"
                className="hover:-translate-y-0.5 transition-all py-2 rounded-lg"
              >
                <ConnectIcon />
              </Button>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>Connect</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button className="bg-red-600" onClick={() => disconnect(modelUid)}>
            <DisconnectIcon />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Disconnect</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default ModelConnectionButton;
