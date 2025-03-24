import { Button } from '@shadcn/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@shadcn/tooltip';
import { CopyIcon } from 'lucide-react';
import { TextResponse } from 'src/shared/generated_models';

export default function TextView({ response }: { response: TextResponse }) {
  return (
    <div className="flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="font-bold text-lg lg:text-xl flex items-center">
          {response.title}
        </h1>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  await navigator.clipboard.writeText(response.value || '');
                }}
              >
                <CopyIcon className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p>Copy Text</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <div className="flex flex-col gap-2 text-md rounded-md">
        <div className="text-sm text-gray-500 mt-1">{response.value}</div>
      </div>
    </div>
  );
}
