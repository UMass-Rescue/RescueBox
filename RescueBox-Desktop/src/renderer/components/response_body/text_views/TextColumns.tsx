import { ColumnDef } from '@tanstack/react-table';
import {
  ArrowUpDown,
  CopyIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from 'lucide-react';
import { Button } from '@shadcn/button';
import { TextResponse } from 'src/shared/generated_models';
import {
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@shadcn/tooltip';
import { Tooltip } from '@radix-ui/react-tooltip';

const textColumns: ColumnDef<TextResponse>[] = [
  {
    accessorKey: 'title',
    id: 'Title',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="p-0 w-full -ml-2"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <div className="flex items-center p-2 ml-1 min-w-20 w-full">
          <div className="font-bold text-black">Title</div>
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </div>
      </Button>
    ),
  },
  {
    accessorKey: 'value',
    id: 'Result',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="p-0 w-full -ml-2"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <div className="flex items-center p-2 w-full">
          <div className="font-bold text-black">Result</div>
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </div>
      </Button>
    ),
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const response = row.original;

      return (
        <div className="flex items-center justify-start space-x-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    row.toggleExpanded();
                  }}
                >
                  {row.getIsExpanded() ? (
                    <ChevronUpIcon className="h-4 w-4" />
                  ) : (
                    <ChevronDownIcon className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>{row.getIsExpanded() ? 'Collapse' : 'Expand'}</p>
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await navigator.clipboard.writeText(response.value);
                  }}
                >
                  <CopyIcon className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Copy</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      );
    },
  },
];

export default textColumns;
