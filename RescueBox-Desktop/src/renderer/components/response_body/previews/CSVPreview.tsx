import { useState } from 'react';
import Papa from 'papaparse';
import { useReadFile } from 'src/renderer/lib/hooks';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@shadcn/table';
import { Input } from '@shadcn/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@shadcn/select';
import LoadingScreen from '../../LoadingScreen';

export default function CSVPreview({
  filePath,
  modal,
}: {
  filePath: string;
  modal: boolean;
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchColumn, setSearchColumn] = useState('All Columns');

  const {
    data: fileContents,
    error: fileContentsError,
    isLoading: fileContentsIsLoading,
  } = useReadFile(filePath);

  if (fileContentsIsLoading) return <LoadingScreen />;
  if (fileContentsError)
    return (
      <div>Error loading file contents: {fileContentsError.toString()}</div>
    );
  if (!fileContents) return <div>File contents not found</div>;

  const parsedData = Papa.parse(fileContents, { header: true });
  const filteredData = parsedData.data.filter((row: any) => {
    if (searchColumn !== 'All Columns') {
      return row[searchColumn]
        ?.toString()
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
    }
    return Object.values(row).some((value: any) =>
      value.toString().toLowerCase().includes(searchTerm.toLowerCase()),
    );
  });

  return (
    <div className="">
      <div className="flex justify-start w-2/3 mt-1 mb-3">
        <Select onValueChange={(e) => setSearchColumn(e)}>
          <SelectTrigger className="w-1/3 rounded-lg focus:ring-0">
            <SelectValue placeholder="All Columns" />
          </SelectTrigger>
          <SelectContent className="w-full">
            <SelectItem value="All Columns">All Columns</SelectItem>
            {parsedData.meta.fields?.map((field: string) => {
              return (
                <SelectItem key={field} value={field}>
                  {field}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
        <Input
          type="text"
          placeholder="Search..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="border border-gray-300 rounded-lg ml-3 w-2/3"
        />
      </div>
      <div className="border border-gray-300 rounded-lg p-4 bg-white">
        <div
          className={`overflow-auto ${modal ? 'max-h-80' : 'max-h-full'} pr-2`}
        >
          <Table className="min-w-full divide-y divide-gray-200">
            <TableHeader className="bg-gray-50">
              <TableRow>
                {parsedData.meta.fields?.map((field: string) => (
                  <TableHead
                    key={field}
                    className="px-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {field}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody className="bg-white divide-y divide-gray-200">
              {filteredData.map((row: any, index: number) => (
                // eslint-disable-next-line react/no-array-index-key
                <TableRow key={`${Object.values(row).join(',')}${index}`}>
                  {parsedData.meta.fields?.map((field: string) => (
                    <TableCell key={field} className="px-3 whitespace-nowrap">
                      {row[field]}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
