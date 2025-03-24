import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, ArrowUpDown } from 'lucide-react';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@shadcn/dropdown-menu';
import { Button } from '@shadcn/button';
import { DirectoryResponse } from 'src/shared/generated_models';

export type PathRow = {
  fullPath: string;
  fileName: string;
  parent: string;
};

export const fileColumns: ColumnDef<PathRow>[] = [
  {
    accessorKey: 'fileName',
    id: 'File / Directory',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="p-0 w-full -ml-2"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <div className="flex items-center p-2 w-full">
          <div className="font-bold text-black">File / Directory</div>
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </div>
      </Button>
    ),
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const { fullPath } = row.original;

      return (
        <div className="flex items-center justify-end space-x-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
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
                    path: fullPath,
                  })
                }
              >
                View in Explorer
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={async () => navigator.clipboard.writeText(fullPath)}
              >
                Copy Path
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      );
    },
  },
];

export const directoryColumns: ColumnDef<DirectoryResponse>[] = [
  {
    accessorKey: 'title',
    id: 'Title',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="p-0 w-full -ml-2"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <div className="flex items-center p-2 w-full">
          <div className="font-bold text-black">Title</div>
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </div>
      </Button>
    ),
  },
  {
    accessorKey: 'path',
    id: 'Directory',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="p-0 w-full -ml-2"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <div className="flex items-center p-2 w-full">
          <div className="font-bold text-black">Directory</div>
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </div>
      </Button>
    ),
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const { path } = row.original;

      return (
        <div className="flex items-center justify-end space-x-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
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
                    path,
                  })
                }
              >
                View in Explorer
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={async () => navigator.clipboard.writeText(path)}
              >
                Copy Path
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      );
    },
  },
];
