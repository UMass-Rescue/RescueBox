import { TaskSchema } from '../generated_models';

const taskSchema1: TaskSchema = {
  inputs: [
    {
      inputType: 'batchfile',
      key: 'audio_files',
      label: 'Audio Files',
      subtitle: 'Provide a collection of audio files to transcribe',
    },
  ],
  parameters: [],
} satisfies TaskSchema;

export default taskSchema1;
