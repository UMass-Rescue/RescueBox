import {
  CopyIcon,
  CheckCircledIcon,
  ReloadIcon,
  ResetIcon,
} from '@radix-ui/react-icons';
import { useState } from 'react';
import LogsIcon from '../components/icons/LogsIcon';
import { Button } from '../components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../components/ui/tooltip';
import { useLogs } from '../lib/hooks';
import LoadingIcon from '../components/icons/LoadingIcon';
import ExportIcon from '../components/icons/ExportIcon';
import LoadingScreen from '../components/LoadingScreen';

const MAX_LOGS = 100;

export default function AuditLogs() {
  const { data: logs, error, isLoading, isValidating, mutate } = useLogs();
  const [isCopying, setIsCopying] = useState(false);

  if (error) return <div>Error: {error.message}</div>;
  if (!logs) return <LoadingScreen />;

  logs[0].lines.reverse();

  const handleCopy = async (): Promise<void> => {
    await navigator.clipboard.writeText(logs[0].lines.join('\n'));
  };

  const handleExport = async (): Promise<void> => {
    await window.fileSystem.saveLogs();
  };

  const handleClear = async (): Promise<void> => {
    await window.logging.clearLogs();
    await mutate();
  };

  const handleRefresh = async (): Promise<void> => {
    await mutate();
  };

  return (
    <div className="flex flex-col items-center m-3 gap-8">
      <div className="flex flex-col p-4 gap-2 bg-gray-950 rounded-md drop-shadow-lg text-blue-50 w-4/5 max-w-full">
        <div className="flex flex-row justify-between gap-2 items-center text-xl bg-gray-800 px-3 py-2 rounded-md">
          <div className="flex flex-row items-center gap-3 font-bold">
            <LogsIcon className="fill-white" />
            Audit Logs
            {isLoading && <LoadingIcon className="text-blue-500" />}
            {isValidating && <LoadingIcon className="text-blue-500" />}
          </div>
          <div className="flex flex-row gap-2 items-center">
            <TooltipProvider delayDuration={100}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button className="bg-gray-950" onClick={handleRefresh}>
                    <ReloadIcon className="text-white size-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>Refresh</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button className="bg-gray-950" onClick={handleClear}>
                    <ResetIcon className="text-white size-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>Clear Logs</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button className="bg-gray-950" onClick={handleExport}>
                    <ExportIcon className="stroke-white" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>Export to File</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    className="bg-gray-950"
                    onClick={async () => {
                      setIsCopying(!isCopying);
                      await handleCopy();
                      setTimeout(() => {
                        setIsCopying(false);
                      }, 1000);
                    }}
                  >
                    {!isCopying ? (
                      <CopyIcon className="size-6" />
                    ) : (
                      <CheckCircledIcon className="size-6" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p>Copy Logs</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
        <div className="mx-2 flex flex-col gap-2 mt-2 text-sm">
          <pre className="text-gray-50">
            Displaying the last {MAX_LOGS} logs...
          </pre>
          <pre className="text-gray-50">
            {isLoading && <LoadingIcon className="text-blue-500" />}
            {logs[0].lines.slice(0, MAX_LOGS).join('\n')}
          </pre>
        </div>
      </div>
    </div>
  );
}
