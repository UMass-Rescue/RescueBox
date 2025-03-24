import { BatchTextResponse } from 'src/shared/generated_models';
import DataTable from '../DataTable';
import textColumns from './TextColumns';

export default function BatchTextView({
  response,
}: {
  response: BatchTextResponse;
}) {
  return (
    <div className="flex flex-col">
      <div className="flex flex-col  text-md rounded-md">
        <div>
          <h1 className="font-bold my-4 text-lg lg:text-xl">Text Collection</h1>
        </div>
        <DataTable columns={textColumns} data={response.texts} />
      </div>
    </div>
  );
}
