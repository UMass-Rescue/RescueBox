import { TaskSchema } from '../generated_models';

const taskSchema4: TaskSchema = {
  inputs: [
    {
      inputType: 'text',
      key: 'text_input',
      label: 'Some Text',
      subtitle: 'Write a sentence to transform',
    },
    {
      inputType: 'textarea',
      key: 'textarea_input',
      label: 'Some Long Text',
      subtitle: 'Write a paragraph to transform',
    },
    {
      inputType: 'file',
      key: 'file_input',
      label: 'Audio Files',
      subtitle: 'Provide an audio file to transcribe',
    },
    {
      inputType: 'directory',
      key: 'directory_input',
      label: 'Directory with Audio Files',
      subtitle: 'Select a directory of audio files to transcribe',
    },
    {
      inputType: 'batchtext',
      key: 'batchtext_input',
      label: 'Collection of Texts',
      subtitle: 'Write multiple sentences to transform',
    },
    {
      inputType: 'batchfile',
      key: 'batchfile_input',
      label: 'Collection of Audio Files',
      subtitle: 'Select multiple audio files to transcribe',
    },
    {
      inputType: 'batchdirectory',
      key: 'batchdirectory_input',
      label: 'Directories with Audio Files',
      subtitle: 'Select multiple directories of audio files to transcribe',
    },
    {
      inputType: {
        defaultName: 'untitled',
        defaultExtension: 'txt',
        allowedExtensions: ['txt', 'md'],
        inputType: 'newfile',
      },
      key: 'newfile_input',
      label: 'New File',
      subtitle: 'Select a location to save a new file',
    },
  ],
  parameters: [
    {
      key: 'text_param',
      label: 'Seed Sentence',
      subtitle: 'Choose a seed sentence for the transformation',
      value: {
        default: 'The quick brown fox jumped over the fence.',
        parameterType: 'text',
      },
    },
    {
      key: 'int_param',
      label: 'Number of Features',
      subtitle: 'Choose the number of features in your dataset',
      value: {
        default: 10,
        parameterType: 'int',
      },
    },
    {
      key: 'float_param',
      label: 'Regularization Term',
      subtitle: 'Choose a value for your regularization term',
      value: {
        default: 0.1,
        parameterType: 'float',
      },
    },
    {
      key: 'enum_param',
      label: 'Normalization',
      subtitle: 'Choose a method of normalization',
      value: {
        default: 'none',
        parameterType: 'enum',
        enumVals: [
          {
            key: 'none',
            label: 'None',
          },
          {
            key: 'batchnorm',
            label: 'Batch Normalization',
          },
          {
            key: 'layernorm',
            label: 'Layer Normalization',
          },
        ],
        messageWhenEmpty: 'None',
      },
    },
    {
      key: 'ranged_int_param',
      label: 'Number of Layers',
      subtitle: 'Choose the number of layers in your network',
      value: {
        default: 2,
        parameterType: 'ranged_int',
        range: {
          max: 16,
          min: 2,
        },
      },
    },
    {
      key: 'ranged_float_param',
      label: 'Confidence Probability',
      subtitle: 'Choose the confidency probability for classification',
      value: {
        default: 0.7,
        parameterType: 'ranged_float',
        range: {
          max: 1.0,
          min: 0.0,
        },
      },
    },
  ],
};

export default taskSchema4;
