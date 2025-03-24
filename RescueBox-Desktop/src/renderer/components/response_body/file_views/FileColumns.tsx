import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@shadcn/dropdown-menu';
import { Button } from '@shadcn/button';
import { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown, MoreHorizontal } from 'lucide-react';
import { FileResponse } from 'src/shared/generated_models';

export type FileRow = {
  title: string;
  icon: string;
  file: FileResponse;
};

const fileColumns: ColumnDef<FileRow>[] = [
  {
    accessorKey: 'icon',
    id: 'icon',
    header: () => <div className="sr-only">Icon</div>,
    cell: ({ row }) => {
      const { icon } = row.original;
      return (
        <div className="flex items-center justify-center">
          <img src={icon} alt={row.original.title} className="h-6 w-6" />
        </div>
      );
    },
  },
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
    accessorKey: 'file.path',
    id: 'File Path',
    header: ({ column }) => (
      <Button
        variant="ghost"
        className="p-0 w-full -ml-2"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        <div className="flex items-center p-2 w-full">
          <div className="font-bold text-black">File Path</div>
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </div>
      </Button>
    ),
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const { file } = row.original;

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
                    path: file.path,
                  })
                }
              >
                View in Explorer
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={async () => navigator.clipboard.writeText(file.path)}
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

export default fileColumns;
