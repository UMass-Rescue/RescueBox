import { Link } from 'react-router-dom';
import {
  TooltipProvider,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from '@shadcn/tooltip';
import { MLModel, ModelAppStatus } from 'src/shared/models';
import { KeyedMutator } from 'swr';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Button } from '../components/ui/button';
import {
  GreenCircleIcon,
  RedCircleIcon,
} from '../components/icons/CircleIcons';
import GreenRunIcon from '../components/icons/GreenRunIcon';
import { ConnectIcon } from '../components/icons/ConnectIcon';
import { ModelRedButton } from '../components/custom_ui/customButtons';

function ModelsTable({
  models,
  serverStatuses,
  mutateModels,
}: {
  models: MLModel[];
  serverStatuses: Record<string, ModelAppStatus>;
  mutateModels: KeyedMutator<MLModel[]>;
}) {
  async function handleRemoveButton(model: MLModel) {
    await window.models.removeModelByUid({ modelUid: model.uid });
    mutateModels();
  }

  return (
    <div className="">
      <div className="shadow-md mt-6">
        <Table className="text-md lg:text-lg">
          <TableHeader className="bg-slate-200">
            <TableRow className="justify-between">
              <TableHead className="pl-4 w-3/6 text-gray-900">Model</TableHead>
              <TableHead className="pr-6 w-1/12 text-gray-900">
                Version{' '}
              </TableHead>
              <TableHead className="w-1/6 text-gray-900">Status</TableHead>
              <TableHead className="w-1/12" />
              <TableHead className="w-1/12" />
              <TableHead className="w-1/12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {models.length === 0 && (
              <TableRow className="hover:bg-gray-50">
                <TableCell className="pl-4">No models available</TableCell>
              </TableRow>
            )}
            {models.map((model: MLModel) => (
              <TableRow key={model.uid} className="hover:bg-gray-50">
                <TableCell className="pl-4">{model.name}</TableCell>
                <TableCell className="pr-6 text-gray-900 text-center">
                  {model.version}
                </TableCell>
                <TableCell className="">
                  <div className="pl-4">
                    {serverStatuses[model.uid] === 'Online' ? (
                      <GreenCircleIcon />
                    ) : (
                      <RedCircleIcon />
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-left py-2 px-1">
                  <Link
                    to={`/models/${model.uid}/details`}
                    className="py-2 px-3 pl-5 "
                  >
                    <Button
                      variant="outline"
                      className="hover:-translate-y-0.5 transition-all  rounded-lg"
                    >
                      Inspect
                    </Button>
                  </Link>
                </TableCell>
                <TableCell className="text-left py-2 pr-4">
                  <TooltipProvider delayDuration={100}>
                    {serverStatuses[model.uid] === ModelAppStatus.Online && ( //
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Link to={`/models/${model.uid}/run`}>
                            <Button className="w-full hover:-translate-y-0.5 transition-all py-2 px-6 rounded-lg bg-green-600 hover:bg-green-500">
                              <GreenRunIcon />
                            </Button>
                          </Link>
                        </TooltipTrigger>
                        <TooltipContent side="bottom">
                          <p>Run</p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                    {serverStatuses[model.uid] !== ModelAppStatus.Online && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Link to={`/registration/${model.uid}`}>
                            <Button
                              variant="outline"
                              className=" text-black text-base w-full font-normal hover:-translate-y-0.5 transition-all py-2 px-6 rounded-lg"
                            >
                              <ConnectIcon />
                            </Button>
                          </Link>
                        </TooltipTrigger>
                        <TooltipContent side="bottom">
                          <p>Connect</p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </TooltipProvider>
                </TableCell>
                <TableCell className="text-center py-2 px-2">
                  <ModelRedButton
                    model={model}
                    handleClick={() => handleRemoveButton(model)}
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

export default ModelsTable;
