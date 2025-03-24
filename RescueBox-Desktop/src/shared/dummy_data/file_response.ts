import {
  BatchDirectoryResponse,
  DirectoryResponse,
  FileResponse,
} from '../generated_models';

const textResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\Downloads\\sample-markdown.txt',
  file_type: 'text',
  title: 'Sample Text',
  subtitle: 'Some info about sample text',
};

const markdownResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\Downloads\\sample-markdown.txt',
  file_type: 'markdown',
  title: 'Sample Markdown',
  subtitle: 'Some info about sample markdown',
};

const imageResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\UMass\\IMG-Super-Resolution\\input\\meerkat.png',
  file_type: 'img',
  title: 'Sample Image',
  subtitle: 'Some info about sample image',
};

const jsonResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\Downloads\\example_2.json',
  file_type: 'json',
  title: 'Sample JSON',
  subtitle: 'Some info about sample JSON',
};

const csvResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\Downloads\\addresses.csv',
  file_type: 'csv',
  title: 'Sample CSV',
  subtitle: 'Some info about sample CSV',
};

const audioResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\Downloads\\file_example_MP3_700KB.mp3',
  file_type: 'audio',
  title: 'Sample Audio',
  subtitle: 'Some info about sample audio',
};

const videoResponse: FileResponse = {
  output_type: 'file',
  path: 'C:\\Users\\LENOVO\\Videos\\Captures\\super-res-demo.mp4',
  file_type: 'video',
  title: 'Sample Video',
  subtitle: 'Some info about sample video',
};

const directoryResponse: DirectoryResponse = {
  output_type: 'directory',
  path: '/Users/atharvakale/Downloads',
  title: 'Sample Directory Outputs',
  // subtitle: 'Subtitle: Some info about sample directory',
};

const directoryResponse2: DirectoryResponse = {
  output_type: 'directory',
  path: '/Users/atharvakale/Downloads/rooting-5g',
  title: 'Sample Markdown',
  subtitle: 'Some info about sample markdown',
};

const batchDirectoryResponse: BatchDirectoryResponse = {
  directories: [directoryResponse, directoryResponse2],
  output_type: 'batchdirectory',
};

export {
  textResponse,
  directoryResponse,
  batchDirectoryResponse,
  markdownResponse,
  imageResponse,
  jsonResponse,
  csvResponse,
  audioResponse,
  videoResponse,
};
