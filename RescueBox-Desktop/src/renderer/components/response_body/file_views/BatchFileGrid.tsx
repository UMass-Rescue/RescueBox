import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@shadcn/dropdown-menu';
import { Button } from '@shadcn/button';
import { MoreHorizontal } from 'lucide-react';
import { FileResponse } from 'src/shared/generated_models';
import { useState, useEffect } from 'react';
import ReactPaginate from 'react-paginate';
import PreviewFileResponse from '../../PreviewFileResponse';

export type FilesByType = {
  type: 'img' | 'text' | 'csv' | 'json' | 'audio' | 'video' | 'markdown';
  title: string;
  files: FileResponse[];
  icon: string;
};

function GridItems({
  currentFiles,
  type,
  icon,
}: {
  currentFiles: FileResponse[];
  type: string;
  icon: string;
}) {
  const [selectedFile, setSelectedFile] = useState<FileResponse | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  return (
    <div
      className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 ${type === 'img' ? 'h-80' : 'h-60'}`}
    >
      {showPreview && selectedFile && (
        <PreviewFileResponse
          response={selectedFile}
          open={showPreview}
          setOpen={setShowPreview}
        />
      )}
      {currentFiles &&
        currentFiles.map((file) => (
          <div key={file.title}>
            <div
              key={file.path}
              className="relative group border border-gray-400 rounded-lg"
            >
              <div className="absolute top-1 right-1">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="h-6 w-6 p-0 rounded-full bg-accent hover:bg-gray-200 cursor-default"
                    >
                      <span className="sr-only">Open Menu</span>
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel className="text-xs py-0.5 text-gray-400">
                      Actions
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() =>
                        window.fileSystem.showFileInExplorer({
                          path: file.path,
                        })
                      }
                    >
                      View in Explorer
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={async () =>
                        navigator.clipboard.writeText(file.path)
                      }
                    >
                      Copy Path
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <div
                className="flex flex-col items-center rounded-t-lg"
                role="button"
                tabIndex={0}
                onClick={() => {
                  setSelectedFile(file);
                  setShowPreview(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    setSelectedFile(file);
                    setShowPreview(true);
                  }
                }}
              >
                <img
                  src={type === 'img' ? `file://${file.path}` : icon}
                  alt="icon"
                  className={
                    type === 'img'
                      ? 'w-full h-28 mb-2 rounded-t-md'
                      : 'w-12 h-12 mt-6 mb-2'
                  }
                />
                <span className="px-2 font-semibold mb-2 overflow-hidden text-ellipsis whitespace-nowrap max-w-full">
                  {file.title}
                </span>
              </div>
            </div>
          </div>
        ))}
    </div>
  );
}

export default function BatchFileGrid({
  data,
  searchTerm,
  startOffset,
  setStartOffset,
}: {
  data: FilesByType;
  searchTerm: string;
  startOffset: number;
  setStartOffset: (offset: number) => void;
}) {
  const [filesPerPage, setFilesPerPage] = useState(12);

  const filteredFiles = data.files.filter((f) =>
    f.title
      ? f.title.toLowerCase().includes(searchTerm.toLowerCase())
      : f.path.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  useEffect(() => {
    const updateFilesPerPage = () => {
      const width = window.innerWidth;
      if (width < 640) {
        setFilesPerPage(4);
      } else if (width < 768) {
        setFilesPerPage(6);
      } else if (width < 1024) {
        setFilesPerPage(8);
      } else if (width < 1280) {
        setFilesPerPage(10);
      } else {
        setFilesPerPage(12);
      }
    };

    window.addEventListener('resize', updateFilesPerPage);
    updateFilesPerPage();

    return () => {
      window.removeEventListener('resize', updateFilesPerPage);
    };
  }, []);

  const endOffset = startOffset + filesPerPage;
  const currentFiles = filteredFiles.slice(startOffset, endOffset);
  const pageCount = Math.ceil(filteredFiles.length / filesPerPage);

  const handlePageClick = (event: { selected: number }) => {
    const newOffset = (event.selected * filesPerPage) % filteredFiles.length;
    setStartOffset(newOffset);
  };

  return (
    <div>
      <GridItems
        currentFiles={currentFiles}
        type={data.type}
        icon={data.icon}
      />
      <div className="flex justify-end mt-4">
        <ReactPaginate
          previousLabel={
            <span
              className={`px-3 py-2 text-xs font-semibold shadow-sm bg-white rounded-md border border-gray-200 hover:bg-gray-100 ${
                startOffset === 0 ? 'cursor-not-allowed opacity-50' : ''
              }`}
            >
              Previous
            </span>
          }
          nextLabel={
            <span
              className={`px-3 py-2 text-xs font-semibold shadow-sm bg-white rounded-md border border-gray-200 hover:bg-gray-100 ${
                endOffset >= filteredFiles.length
                  ? 'cursor-not-allowed opacity-50'
                  : ''
              }`}
            >
              Next
            </span>
          }
          pageCount={pageCount}
          onPageChange={handlePageClick}
          containerClassName="pagination flex my-1 space-x-2"
          pageClassName="hidden"
          breakClassName="hidden"
          previousLinkClassName={startOffset === 0 ? 'pointer-events-none' : ''}
          nextLinkClassName={
            endOffset >= filteredFiles.length ? 'pointer-events-none' : ''
          }
        />
      </div>
    </div>
  );
}
