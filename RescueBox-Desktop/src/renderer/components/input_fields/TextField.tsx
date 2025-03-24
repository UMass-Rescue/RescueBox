import { Input } from '../ui/input';

export default function TextField({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex items-center mt-2">
      <Input
        type="text"
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="border border-gray-300 disabled:opacity-100 disabled:cursor-text"
        defaultValue={disabled ? value : ''}
      />
    </div>
  );
}
