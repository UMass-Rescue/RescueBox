import { BatchDirectoryResponse } from 'src/shared/generated_models';
import DataTable from '../DataTable';
import { directoryColumns } from './DirectoryColumns';

export default function BatchDirectoryView({
  response,
}: {
  response: BatchDirectoryResponse;
}) {
  return (
    <div className="flex flex-col">
      <div className="flex flex-col  text-md rounded-md">
        <div>
          <h1 className="font-bold my-4 text-lg lg:text-xl">
            Directory Collection
          </h1>
        </div>
        <DataTable columns={directoryColumns} data={response.directories} />
      </div>
    </div>
  );
}
