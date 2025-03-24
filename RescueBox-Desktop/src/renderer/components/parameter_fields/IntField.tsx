import { ParameterSchema } from 'src/shared/generated_models';
import { Input } from '../ui/input';

export default function IntField({
  parameterSchema,
  value,
  onChange,
  disabled,
}: {
  parameterSchema: ParameterSchema;
  value: number;
  onChange: (value: number) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex items-center mt-2">
      <Input
        type="number"
        defaultValue={disabled ? value : Number(parameterSchema.value.default)}
        onChange={(e) => onChange(e.target.valueAsNumber)}
        disabled={disabled}
        className="border border-gray-300 disabled:opacity-100 disabled:cursor-text"
      />
    </div>
  );
}
