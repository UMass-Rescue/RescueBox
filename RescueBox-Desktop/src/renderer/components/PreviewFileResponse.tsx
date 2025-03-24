import { FileResponse } from 'src/shared/generated_models';
import { Cross1Icon, OpenInNewWindowIcon } from '@radix-ui/react-icons';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import FilePreview from './response_body/previews/FilePreview';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function PreviewFileResponse({
  response,
  open,
  setOpen,
}: {
  response: FileResponse;
  open: boolean;
  setOpen: (open: boolean) => void;
}) {
  return (
    <div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogDescription />
        <DialogContent className="[&>button]:hidden xs:max-w-md sm:max-w-xl md:max-w-2xl lg:max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <div className="grid grid-cols-6 gap-4">
              <DialogTitle
                className="flex items-center gap-4 col-span-5 text-ellipsis"
                asChild
              >
                <h1 className="font-bold text-xl break-words">
                  {response.title
                    ? `Preview: ${response.title
                        .replaceAll('/', '/\u200B')
                        .replaceAll('\\', '\\\u200B')}`
                    : 'Preview'}
                </h1>
              </DialogTitle>
              <div className="ml-auto flex">
                <Button
                  className="bg-transparent hover:bg-gray-200 shadow-none p-1 mr-3"
                  onClick={() =>
                    window.fileSystem.showFileInExplorer({
                      path: response.path,
                    })
                  }
                  title="View in Explorer"
                >
                  <OpenInNewWindowIcon className="size-6 text-gray-800" />
                </Button>
                <Button
                  className="bg-transparent hover:bg-gray-200 shadow-none p-1"
                  onClick={() => setOpen(false)}
                  title="Close"
                >
                  <Cross1Icon className="size-6 text-gray-800" />
                </Button>
              </div>
            </div>
            {response.subtitle && (
              <span className="block max-h-10 overflow-y-auto text-sm">
                {response.subtitle}
              </span>
            )}
          </DialogHeader>
          <div className="overflow-auto h-full">
            <FilePreview response={response} modal />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
