import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@shadcn/table';
import { MLModel } from 'src/shared/models';
import RegisterModelButton from 'src/renderer/components/custom_ui/RegisterModelButton';
import { useMLModels, useServers } from '../lib/hooks';
import { createMLServerMap } from '../lib/utils';
import ModelStatusIndicator from '../models/ModelStatusIndicator';
import ModelConnectionButton from './ModelConnectionButton';
import LoadingScreen from '../components/LoadingScreen';

/**
 * Partitions an array into two arrays, one with elements that pass a test and one with elements that fail the test.
 * @param array an array to partition of type T
 * @param isValid a predicate function that takes an element of type T and returns a boolean
 * @returns [pass, fail] where pass is an array of elements that passed the test and fail is an array of elements that failed the test
 */
export function partition<T>(
  array: T[],
  isValid: (elem: T) => boolean,
): [T[], T[]] {
  return array.reduce(
    (acc, elem: T) => {
      const [pass, fail] = acc;
      return isValid(elem) ? [[...pass, elem], fail] : [pass, [...fail, elem]];
    },
    [[], []] as [T[], T[]],
  );
}

export default function RegistrationTable() {
  // ML Models Hook
  const modelMethods = useMLModels();
  const { models } = modelMethods;
  const { error: modelError, isLoading: modelIsLoading } = modelMethods;

  // Servers Hook
  const {
    servers,
    error,
    isLoading: serverIsLoading,
    mutate: mutateServers,
  } = useServers();

  if (modelError)
    return <div>failed to load models. Error: {modelError.toString()}</div>;
  if (modelIsLoading) return <LoadingScreen />;
  if (!models) return <div>no models</div>;

  if (error) return <div>failed to load {error.toString()}</div>;
  if (serverIsLoading) return <LoadingScreen />;
  if (!servers) return <div>no servers</div>;

  const serverMap = { ...createMLServerMap(servers) };

  return (
    <div className="w-4/5 max-w-full">
      <div className="flex justify-between items-center mb-4">
        <h1 className="font-bold text-xl md:text-2xl lg:text-4xl">
          Registered Models
        </h1>
        <RegisterModelButton replace />
      </div>
      <div className="shadow-md mt-6">
        <Table className="text-md lg:text-lg">
          <TableHeader className="bg-slate-200">
            <TableRow className="justify-between">
              <TableHead className="pl-4 w-2/5 text-gray-900">Model</TableHead>
              <TableHead className="w-1/5 text-gray-900">
                Server Address
              </TableHead>
              <TableHead className="w-1/5 text-gray-900">Port</TableHead>
              <TableHead className="text-gray-900">Status</TableHead>
              <TableHead className="text-gray-900">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {models
              .filter((model) => !model.isRemoved)
              .map((model: MLModel) => (
                <TableRow key={model.uid} className="py-2 hover:bg-gray-50">
                  <TableCell className="pl-4">{model.name}</TableCell>
                  <TableCell className="">
                    {serverMap[model.uid]
                      ? serverMap[model.uid].serverAddress
                      : ''}
                  </TableCell>
                  <TableCell className="">
                    {serverMap[model.uid]
                      ? serverMap[model.uid].serverPort
                      : ''}
                  </TableCell>
                  <TableCell className="">
                    <div className="pl-4">
                      <ModelStatusIndicator modelUid={model.uid} />
                    </div>
                  </TableCell>
                  <TableCell>
                    <ModelConnectionButton
                      mutate={mutateServers}
                      modelUid={model.uid}
                    />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
