import { FallbackProps } from 'react-error-boundary';
import { mutate } from 'swr';
import { CheckCircledIcon, CopyIcon } from '@radix-ui/react-icons';
import { useState } from 'react';
import { Button } from './ui/button';
import CancelIcon from './icons/CancelIcon';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';

function resetSWRCache() {
  return mutate(() => true, undefined);
}

function ErrorContentForError({ error }: { error: Error }) {
  return (
    <div className="mx-2 flex flex-col gap-2">
      <h1 className="text-lg font-bold">Error:</h1>
      <pre className="text-red-500">{error.message}</pre>
      <h1 className="text-lg font-bold">Call Stack:</h1>
      <pre className="text-gray-50">{error.stack}</pre>
    </div>
  );
}

function ErrorContentForAnyError({ error }: { error: any }) {
  return (
    <div className="mx-2 flex flex-col gap-2">
      <pre className="text-gray-50">
        {!error ? 'Error is undefined' : error.toString()}
      </pre>
    </div>
  );
}

function FallbackError({ error, resetErrorBoundary }: FallbackProps) {
  const handleErrorReset = async (): Promise<void> => {
    await window.database.resetDatabase();
    await resetSWRCache();
    resetErrorBoundary();
  };

  const handleErrorCopy = async (): Promise<void> => {
    if (!error) return;
    if (error instanceof Error)
      await navigator.clipboard.writeText(error.stack ?? error.message);
    else await navigator.clipboard.writeText(error.toString());
  };

  const [isCopying, setIsCopying] = useState(false);

  return (
    <div className="flex flex-col p-4 gap-2 bg-gray-950 rounded-md drop-shadow-lg text-blue-50">
      <div className="flex flex-row justify-between gap-2 items-center text-xl bg-gray-800 px-3 py-2 rounded-md">
        <div className="flex flex-row items-center gap-2 font-bold">
          <CancelIcon className="fill-white" />
          App Crash
        </div>
        <div className="flex flex-row gap-2 items-center">
          <TooltipProvider delayDuration={100}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  className="bg-gray-950"
                  onClick={async () => {
                    setIsCopying(!isCopying);
                    await handleErrorCopy();
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
          <Button className="bg-gray-950" onClick={handleErrorReset}>
            Reset Database
          </Button>
        </div>
      </div>
      <div className="text-gray-50 mx-2">
        The application encountered a crash. Please copy the logs and share them
        with the developers.
      </div>
      {error instanceof Error ? (
        <ErrorContentForError error={error} />
      ) : (
        <ErrorContentForAnyError error={error} />
      )}
    </div>
  );
}

export default FallbackError;
