import { FileResponse } from 'src/shared/generated_models';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@shadcn/tooltip';
import { Button } from '@shadcn/button';
import { CopyIcon } from 'lucide-react';
import { OpenInNewWindowIcon } from '@radix-ui/react-icons';
import FilePreview from '../previews/FilePreview';

export default function FileView({ response }: { response: FileResponse }) {
  return (
    <div className="flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="font-bold text-lg lg:text-xl flex items-center">
          {response.title
            ?.replaceAll('/', '/\u200B')
            .replaceAll('\\', '\\\u200B')}
        </h1>
        <div className="flex items-center space-x-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await window.fileSystem.showFileInExplorer({
                      path: response.path,
                    });
                  }}
                >
                  <OpenInNewWindowIcon className="size-6" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Open in File Explorer</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await navigator.clipboard.writeText(response.path);
                  }}
                >
                  <CopyIcon className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Copy Path</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
      <div className="flex flex-col gap-2 text-md rounded-md">
        <FilePreview response={response} modal={false} />
      </div>
    </div>
  );
}
