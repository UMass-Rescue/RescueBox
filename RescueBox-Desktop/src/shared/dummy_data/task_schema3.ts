import { TaskSchema } from '../generated_models';

const taskSchema3: TaskSchema = {
  inputs: [
    {
      inputType: 'directory',
      key: 'target_directory',
      label: 'Target Directory',
      subtitle:
        'The directory containing files/folders of the content to analyze',
    },
    {
      inputType: 'directory',
      key: 'known_content_directory',
      label: 'Known Content Directory',
      subtitle: 'The directory containing the files/folders of known content',
    },
    {
      inputType: 'file',
      key: 'output_sql_path',
      label: 'Output SQL Path',
      subtitle: 'The path to save the SQLite table for known_content',
    },
  ],
  parameters: [
    {
      key: 'block_size',
      label: 'Block Size',
      subtitle: 'The block size in bytes to be used. Defaults to 4096.',
      value: {
        default: 4096,
        parameterType: 'ranged_int',
        range: {
          max: 1024,
          min: 1,
        },
      },
    },
    {
      key: 'target_probability',
      label: 'Target Probability',
      subtitle:
        'The target probability to achieve. Higher means more of the target drive will be scanned. Defaults to 0.95',
      value: {
        default: 0.95,
        parameterType: 'ranged_float',
        range: {
          max: 1.0,
          min: 0.0,
        },
      },
    },
  ],
} satisfies TaskSchema;

export default taskSchema3;
