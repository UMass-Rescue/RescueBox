import { InputSchema } from 'src/shared/generated_models';
import { match } from 'ts-pattern';
import DirectoryField from './input_fields/DirectoryField';
import FileField from './input_fields/FileField';
import TextField from './input_fields/TextField';
import TextAreaField from './input_fields/TextAreaField';
import BatchTextField from './input_fields/BatchTextField';
import BatchDirectoryField from './input_fields/BatchDirectoryField';
import BatchFileField from './input_fields/BatchFileField';
import NewFileField from './input_fields/NewFileField';

type InputFieldProps = {
  inputSchema: InputSchema;
  value: any;
  onChange: (value: any) => void;
  // eslint-disable-next-line react/require-default-props
  disabled?: boolean;
};

export default function InputField({
  inputSchema,
  value,
  onChange,
  disabled = false,
}: InputFieldProps) {
  return (
    <div>
      <h2 className="font-semibold text-sm xl:text-base">
        {inputSchema.label}
      </h2>
      {inputSchema.subtitle && (
        <p className="text-xs mt-1">{inputSchema.subtitle}</p>
      )}
      {match(inputSchema)
        .with({ inputType: 'text' }, () => (
          <TextField value={value} onChange={onChange} disabled={disabled} />
        ))
        .with({ inputType: 'textarea' }, () => (
          <TextAreaField
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        ))
        .with({ inputType: 'file' }, () => (
          <FileField value={value} onChange={onChange} disabled={disabled} />
        ))
        .with({ inputType: 'directory' }, () => (
          <DirectoryField
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        ))
        .with({ inputType: 'batchtext' }, () => (
          <BatchTextField
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        ))
        .with({ inputType: 'batchfile' }, () => (
          <BatchFileField
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        ))
        .with({ inputType: 'batchdirectory' }, () => (
          <BatchDirectoryField
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        ))
        .with(
          {
            inputType: {
              inputType: 'newfile',
            },
          },
          () => (
            <NewFileField
              inputSchema={inputSchema}
              value={value}
              onChange={onChange}
              disabled={disabled}
            />
          ),
        )
        .otherwise(() => (
          <div>Unsupported input type.</div>
        ))}
    </div>
  );
}
