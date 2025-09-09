import { useFileIcons } from 'src/renderer/lib/hooks';
import { useState } from 'react';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@shadcn/accordion';
import { ListBulletIcon } from '@radix-ui/react-icons';
import { ColumnDef } from '@tanstack/react-table';
import {
  TooltipProvider,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from '@shadcn/tooltip';
import { Button } from '@shadcn/button';
import { GridIcon } from 'lucide-react';
import { Input } from '@shadcn/input';
import { BatchFileResponse } from 'src/shared/generated_models';
import LoadingScreen from '../../LoadingScreen';
import fileColumns from './FileColumns';
import BatchFileGrid, { FilesByType } from './BatchFileGrid';
import DataTable from '../DataTable';

export default function BatchFileView({
  response,
}: {
  response: BatchFileResponse;
}) {
  const { files: allFiles } = response;

  const shouldUseDynamicColumns =
    allFiles.length > 0 &&
    allFiles[0].metadata &&
    (allFiles[0].file_type === 'img' || allFiles[0].file_type === 'text');

  const {
    data: fileIcons,
    error: fileIconsError,
    isLoading: fileIconsIsLoading,
  } = useFileIcons(allFiles.map((file) => file.path));

  const [isListView, setIsListView] = useState(shouldUseDynamicColumns);
  const [searchTerms, setSearchTerms] = useState<Record<string, string>>({
    img: '',
    csv: '',
    json: '',
    text: '',
    audio: '',
    video: '',
    markdown: '',
  });
  const [gridStartOffset, setGridStartOffset] = useState(0);

  if (fileIconsIsLoading) return <LoadingScreen />;
  if (fileIconsError) return <div>Error loading file icons</div>;
  if (!fileIcons) return <div>No file icons available</div>;

  const typeToTitle: Record<string, string> = {
    img: 'Image Results',
    csv: 'CSV Results',
    json: 'JSON Results',
    text: 'Text Results',
    audio: 'Audio Results',
    video: 'Video Results',
    markdown: 'Markdown Results',
  };

  const filesByType = allFiles.reduce((acc, file) => {
    const type = file.file_type;
    if (acc.findIndex((f) => f.type === type) === -1) {
      acc.push({
        type,
        title: typeToTitle[type],
        files: [file],
        icon: fileIcons[file.path],
      });
    } else {
      const existing = acc.find((f) => f.type === type);
      if (existing) {
        existing.files.push(file);
      }
    }
    return acc;
  }, [] as FilesByType[]);


  // Function to dynamically generate columns from metadata keys
  const generateColumns = (metadataKeys: string[]): ColumnDef<Record<string, any>>[] => {
    return metadataKeys.map(key => ({
      accessorKey: key,
      header: key,

      cell: ({ row }) => {
        // Try direct access instead of row.getValue
        const value = row.original[key];
        console.log(`Cell rendering - Key: ${key}, Value: ${value}`);
        if (key.toLowerCase().includes('path') && typeof value === 'string') {
          return <span>{value.split(/[\\/]/).pop()}</span>;
        }
        return <span>{String(value)}</span>;
    },
    }));
  };

  // Determine if we should use dynamic columns based on the presence of metadata
  // and if the file type is one that we expect to have tabular metadata (e.g., 'img' or 'text')

  const dynamicColumns: ColumnDef<Record<string, any>>[] = shouldUseDynamicColumns
    ? generateColumns(Object.keys(allFiles[0].metadata!))
    : fileColumns; // Fallback to existing fileColumns

  return (
    <div>
      {!shouldUseDynamicColumns && (
        <div className="flex items-center justify-end rounded-md overflow-hidden">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => setIsListView(true)}
                  className={`h-10 w-15 rounded-r-none ${
                    !isListView ? 'bg-gray-300' : ''
                  }`}
                >
                  <ListBulletIcon className="text-white size-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>List View</p>
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => setIsListView(false)}
                  className={`h-10 w-15 rounded-l-none ${
                    isListView ? 'bg-gray-300' : ''
                  }`}
                >
                  <GridIcon className="text-white size-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Grid View</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}
      <Accordion type="multiple" className="w-full">
        {filesByType.map((fileGroup) => (
          <AccordionItem
            value={fileGroup.title}
            key={fileGroup.title}
            onAnimationEnd={() => {
              setSearchTerms((prevTerms) => ({
                ...prevTerms,
                [fileGroup.type]: '',
              }));
            }}
          >
            <AccordionTrigger className="text-xl flex items-left">
              <span className="py-2 w-4/5 text-left">{fileGroup.title}</span>
              <AccordionContent className="p-1 mr-5 float-right">
                {!isListView ? (
                  <div className="relative flex items-center">
                    <Input
                      className="w-full h-9"
                      onClick={(e) => e.stopPropagation()}
                      placeholder="Search..."
                      onChange={(e) => {
                        setSearchTerms({
                          ...searchTerms,
                          [fileGroup.type]: e.target.value,
                        });
                        setGridStartOffset(0);
                      }}
                    />
                  </div>
                ) : null}
              </AccordionContent>
            </AccordionTrigger>
            <AccordionContent className="mt-1">

              {isListView ? (
                <>
                {console.log("Data passed to DataTable (real data):", fileGroup.files.map((f) => f.metadata || {}))}
                  <DataTable
                    columns={
                      shouldUseDynamicColumns &&
                      (fileGroup.type === 'img' || fileGroup.type === 'text')
                        ? dynamicColumns
                        : fileColumns
                    }
                    data={
                      shouldUseDynamicColumns &&
                      (fileGroup.type === 'img' || fileGroup.type === 'text')
                        ? fileGroup.files.map((f) => f.metadata || {})
                        : fileGroup.files.map((file) => ({
                            title: file.path.split(/[\\/]/).pop() || file.path,
                            icon: fileIcons[file.path],
                            file,
                          }))
                    }
                  />
                </>
              ) : (
                <BatchFileGrid
                  data={fileGroup}
                  searchTerm={searchTerms[fileGroup.type]}
                  startOffset={gridStartOffset}
                  setStartOffset={setGridStartOffset}
                />
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
