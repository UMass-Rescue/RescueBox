import { Textarea } from '../ui/textarea';

export default function TextAreaField({
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
      <Textarea
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="border border-gray-300 disabled:opacity-100 disabled:cursor-text"
      />
    </div>
  );
}
