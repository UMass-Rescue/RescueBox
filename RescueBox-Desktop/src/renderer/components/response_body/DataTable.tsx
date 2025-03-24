import {
  ColumnDef,
  SortingState,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  ColumnFiltersState,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  getExpandedRowModel,
} from '@tanstack/react-table';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@shadcn/table';

import { Button } from '@shadcn/button';
import { Input } from '@shadcn/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@shadcn/select';
import { FileResponse } from 'src/shared/generated_models';
import { useState } from 'react';
import PreviewFileResponse from '../PreviewFileResponse';
import { FileRow } from './file_views/FileColumns';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
}

function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState<any>([]);

  const [showPreview, setShowPreview] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileResponse | null>(null);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    getFilteredRowModel: getFilteredRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize: 5,
      },
    },
  });

  const headers = table
    .getHeaderGroups()
    .flatMap((headerGroup) => headerGroup.headers)
    .filter((header) => header.id !== 'actions' && header.id !== 'icon');

  const [searchColumn, setSearchColumn] = useState(
    headers.length > 1 ? 'All Columns' : headers[0].id,
  );

  return (
    <div>
      {showPreview && selectedFile && (
        <PreviewFileResponse
          response={selectedFile}
          open={showPreview}
          setOpen={setShowPreview}
        />
      )}
      <div className="flex items-center pb-4 max-w-sm gap-2">
        {headers.length > 1 && (
          <Select onValueChange={(e) => setSearchColumn(e)}>
            <SelectTrigger className="w-1/2 focus:ring-0">
              <SelectValue placeholder="All Columns" />
            </SelectTrigger>
            <SelectContent className="w-full">
              <SelectItem value="All Columns">All Columns</SelectItem>
              {headers.map((header) => {
                return (
                  <SelectItem key={header.id} value={header.id}>
                    {header.id}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        )}
        {(() => {
          if (headers.length > 1) {
            if (searchColumn === 'All Columns') {
              return (
                <Input
                  placeholder="Search..."
                  onChange={(event) =>
                    table.setGlobalFilter(String(event.target.value))
                  }
                  className="max-w-sm"
                />
              );
            }
            return (
              <Input
                placeholder={`Filter by ${searchColumn}`}
                value={
                  (table.getColumn(searchColumn)?.getFilterValue() as string) ??
                  ''
                }
                onChange={(event) =>
                  table
                    .getColumn(searchColumn)
                    ?.setFilterValue(event.target.value)
                }
                className="max-w-sm"
              />
            );
          }
          return (
            <Input
              placeholder={`Filter by ${searchColumn}`}
              value={
                (table.getColumn(searchColumn)?.getFilterValue() as string) ??
                ''
              }
              onChange={(event) =>
                table
                  .getColumn(searchColumn)
                  ?.setFilterValue(event.target.value)
              }
              className="max-w-sm"
            />
          );
        })()}
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && 'selected'}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell
                      key={cell.id}
                      className={
                        cell.column.id === 'actions'
                          ? 'align-top'
                          : 'cursor-default'
                      }
                      onClick={() => {
                        if (cell.column.id !== 'actions') {
                          setSelectedFile((row.original as FileRow).file);
                          setShowPreview(true);
                        }
                      }}
                    >
                      <div
                        className={
                          row.getIsExpanded()
                            ? ''
                            : 'overflow-hidden text-ellipsis line-clamp-1'
                        }
                      >
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </div>
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {table.getPageCount() > 1 && (
        <div className="flex items-center justify-end space-x-2 py-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

export default DataTable;
