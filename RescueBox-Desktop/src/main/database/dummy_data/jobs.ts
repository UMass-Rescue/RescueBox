import { v4 as uuidv4 } from 'uuid';
import { Job } from 'src/shared/models';
import { TaskSchema } from 'src/shared/generated_models';
import { imgObjModelId, isrModelId, sbfModelId } from './mlmodels';

const isrTaskSchema: TaskSchema = {
  inputs: [
    {
      inputType: 'batchfile',
      key: 'input_images',
      label: 'Input Images',
      subtitle: 'Images to be upscaled',
    },
    {
      inputType: 'directory',
      key: 'output_directory',
      label: 'Output Directory',
      subtitle: 'Directory to save the upscaled images',
    },
  ],
  parameters: [
    {
      key: 'weights',
      label: 'Model Weights',
      subtitle: '',
      value: {
        default: 'gans',
        enumVals: [
          {
            key: 'gans',
            label: 'GANS',
          },
          {
            key: 'psnr-large',
            label: 'PSNR Large',
          },
          {
            key: 'psnr-small',
            label: 'PSNR Small',
          },
          {
            key: 'noise-cancel',
            label: 'Noise Cancel',
          },
        ],
        parameterType: 'enum',
      },
    },
    {
      key: 'scale',
      label: 'Scale Factor',
      subtitle: '',
      value: {
        default: 4.0,
        parameterType: 'ranged_float',
        range: {
          max: 4.0,
          min: 1.0,
        },
      },
    },
  ],
};

const sbfTaskSchema: TaskSchema = {
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
};

const imgObjDetectTaskSchema: TaskSchema = {
  inputs: [
    {
      inputType: 'file',
      key: 'input_path',
      label: 'Input Image',
      subtitle: '',
    },
    {
      inputType: 'file',
      key: 'output_img',
      label: 'Output Image',
      subtitle: '',
    },
    {
      inputType: 'file',
      key: 'output_csv',
      label: 'Output CSV',
      subtitle: '',
    },
  ],
  parameters: [
    {
      key: 'min_perc_prob',
      label: 'Minimum Percentage Probability',
      subtitle: '',
      value: {
        default: 30,
        parameterType: 'ranged_int',
        range: {
          max: 100,
          min: 0,
        },
      },
    },
    {
      key: 'model_type',
      label: 'Model Type',
      subtitle: '',
      value: {
        default: 'retina-net',
        enumVals: [
          {
            key: 'yolov3',
            label: 'Yolov3',
          },
          {
            key: 'tiny-yolov3',
            label: 'Tiny Yolov3',
          },
          {
            key: 'retina-net',
            label: 'Retina Net',
          },
        ],
        parameterType: 'enum',
      },
    },
  ],
};

const jobs: Job[] = [
  {
    uid: uuidv4(),
    modelUid: isrModelId,
    startTime: new Date('2023-10-01T10:14:00Z'),
    endTime: new Date('2023-10-01T12:09:00Z'),
    // @ts-ignore
    status: 'Completed',
    request: {
      inputs: {
        input_images: {
          files: [
            {
              path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\input\\baboon.png',
            },
            {
              path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\input\\meerkat.png',
            },
            {
              path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\input\\street.png',
            },
          ],
        },
        output_directory: {
          path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\output',
        },
      },
      parameters: {
        weights: 'gans',
        scale: 4.0,
      },
    },
    response: {
      output_type: 'directory',
      path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\output',
      title: 'High Resolution Images',
    },
    taskUid: '0',
    taskSchema: isrTaskSchema,
  },
  {
    uid: uuidv4(),
    modelUid: sbfModelId,
    startTime: new Date('2023-10-02T14:19:08Z'),
    endTime: new Date('2023-10-02T14:19:49Z'),
    // @ts-ignore
    status: 'Failed',
    statusText: '[{"message":"fetch failed"}]',
    request: {
      inputs: {
        known_content_directory: {
          path: 'F:/USB/Forensic/Input',
        },
        output_sql_path: {
          path: 'F:/USB/Forensic/Output.sqlite',
        },
        target_directory: {
          path: 'F:/USB/Forensic/Target',
        },
      },
      parameters: {
        block_size: 4096,
        target_probability: 0.99,
      },
    },
    taskUid: '0',
    taskSchema: sbfTaskSchema,
  },
  {
    uid: 'ddd43cfe-fa7e-4b80-a7c6-25ddd5e92dc7',
    modelUid: sbfModelId,
    startTime: new Date('2024-10-09T17:24:23.526Z'),
    endTime: new Date('2024-10-09T17:24:23.634Z'),
    // @ts-ignore
    status: 'Completed',
    request: {
      inputs: {
        known_content_directory: {
          path: '/Users/atharvakale/Downloads/known_dataset_images_input2',
        },
        target_directory: {
          path: '/Users/atharvakale/Downloads/known_dataset_images_output',
        },
        output_sql_path: {
          path: '/Users/atharvakale/Downloads/sqlite-hashes-2024-10-09T17:24:19.935Z.db',
        },
      },
      parameters: {
        block_size: 16,
        target_probability: 0.9,
      },
    },
    response: {
      output_type: 'markdown',
      value: '## Results\n\nThe model has successfully completed the task.',
      title: 'Model Output',
    },
    taskUid: '0',
    taskSchema: sbfTaskSchema,
  },
  {
    uid: uuidv4(),
    modelUid: imgObjModelId,
    startTime: new Date('2023-10-06T09:03:45Z'),
    // @ts-ignore
    status: 'Running',
    request: {
      inputs: {
        input_path: {
          path: '/Users/path/to/file.png',
        },
        output_csv: {
          path: '/Users/path/to/file.csv',
        },
        output_img: {
          path: '/Users/path/to/file-out.png',
        },
      },
      parameters: {
        min_perc_prob: 30,
        model_type: 'yolov3',
      },
    },
    taskUid: '0',
    taskSchema: imgObjDetectTaskSchema,
  },
];

export default jobs;
