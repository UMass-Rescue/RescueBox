import { BatchFileResponse, FileResponse } from '../generated_models';

const fileResponse: FileResponse = {
  output_type: 'file',
  file_type: 'img',
  path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\input\\baboon.png',
  title: 'sample3',
  subtitle: 'second sample image',
};

const batchFileResponse: BatchFileResponse = {
  output_type: 'batchfile',
  files: [
    {
      output_type: 'file',
      file_type: 'img',
      path: '/home/shreneken/Pictures/cat_walp.jpg',
      title: 'sample1',
      subtitle: 'first sample image',
    },
    {
      output_type: 'file',
      file_type: 'text',
      path: 'C:\\Users\\LENOVO\\Downloads\\markdown.txt',
      title: 'sample2',
      subtitle: 'first sample text',
    },
    {
      output_type: 'file',
      file_type: 'img',
      path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\input\\baboon.png',
      title: 'sample3',
      subtitle: 'second sample image',
    },
    {
      output_type: 'file',
      file_type: 'csv',
      path: 'C:\\Users\\LENOVO\\Downloads\\addresses.csv',
      title: 'sample',
      subtitle: 'sample CSV',
    },
    {
      output_type: 'file',
      file_type: 'img',
      path: 'some/path/ok2.img',
      title: 'sample',
      subtitle: 'sample image',
    },
  ],
};

export { fileResponse, batchFileResponse };
