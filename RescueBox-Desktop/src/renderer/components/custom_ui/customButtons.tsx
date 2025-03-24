import { Button } from '@shadcn/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@shadcn/tooltip';
import { Link } from 'react-router-dom';
import { Job, MLModel } from 'src/shared/models';
import CancelIcon from '../icons/CancelIcon';
import DeleteIcon from '../icons/DeleteIcon';

export function ViewButton({ job }: { job: Job }) {
  return (
    <Link to={`/jobs/${job.uid}/details`} className="">
      <Button
        variant="outline"
        className="px-8 hover:-translate-y-0.5 transition-all rounded-lg"
      >
        View
      </Button>
    </Link>
  );
}

export function JobRedButton({
  job,
  variant,
  handleClick,
}: {
  job: Job;
  variant: 'cancel' | 'delete';
  handleClick: (job: Job) => void;
}) {
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            className="px-4 bg-red-600 mr-2 hover:-translate-y-0.5 transition-all"
            onClick={() => handleClick(job)}
          >
            {variant === 'cancel' ? <CancelIcon /> : <DeleteIcon />}
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>{variant === 'cancel' ? 'Cancel' : 'Delete'}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function ModelRedButton({
  model,
  handleClick,
}: {
  model: MLModel;
  handleClick: (model: MLModel) => void;
}) {
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            className="px-4 bg-red-600 mr-2 hover:-translate-y-0.5 transition-all"
            onClick={() => handleClick(model)}
          >
            <DeleteIcon />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Delete</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
