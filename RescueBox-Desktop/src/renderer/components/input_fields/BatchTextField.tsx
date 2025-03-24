import { useState } from 'react';
import { MinusCircledIcon, PlusCircledIcon } from '@radix-ui/react-icons';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';

export default function BatchTextField({
  value,
  onChange,
  disabled = false,
}: {
  value: string[];
  onChange: (value: string[]) => void;
  disabled: boolean;
}) {
  const [fields, setFields] = useState<string[]>(value || []);

  const handleAddField = () => {
    setFields([...fields, '']);
  };

  const handleRemoveField = (index: number) => {
    const newFields = fields.filter((_, i) => i !== index);
    setFields(newFields);
    onChange(newFields);
  };

  const handleChange = (index: number, newValue: string) => {
    const newFields = fields.slice();
    newFields[index] = newValue;
    setFields(newFields);
    onChange(newFields);
  };

  return (
    <div className="mt-2">
      {!disabled && fields.length === 0 && (
        <div className="flex items-center mb-2">
          <Textarea
            value=""
            onChange={(e) => handleChange(0, e.target.value)}
            className="flex-grow"
          />
          <TooltipProvider delayDuration={100}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={handleAddField}
                  className="ml-2 self-start"
                >
                  <PlusCircledIcon className="size-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p>Add</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}
      {fields.map((field, index) => (
        <div
          // eslint-disable-next-line react/no-array-index-key
          key={`${index}`}
          className="flex items-center mb-2"
        >
          <Textarea
            value={field}
            onChange={(e) => handleChange(index, e.target.value)}
            className="flex-grow border border-gray-300 disabled:opacity-100 disabled:cursor-text"
            disabled={disabled}
          />
          {!disabled &&
            (index === fields.length - 1 ? (
              <TooltipProvider delayDuration={100}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      onClick={handleAddField}
                      className="ml-2 self-start"
                    >
                      <PlusCircledIcon className="size-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p>Add</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <TooltipProvider delayDuration={100}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      onClick={() => handleRemoveField(index)}
                      className="ml-2 self-start"
                    >
                      <MinusCircledIcon className="size-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom">
                    <p>Remove</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ))}
        </div>
      ))}
    </div>
  );
}
