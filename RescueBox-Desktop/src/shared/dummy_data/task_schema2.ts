import { TaskSchema } from '../generated_models';

const taskSchema2: TaskSchema = {
  inputs: [
    {
      inputType: 'batchtext',
      key: 'text_inputs',
      label: 'Text Inputs',
      subtitle:
        'Provide a collection of text inputs to recognize named entities',
    },
  ],
  parameters: [],
} satisfies TaskSchema;

export default taskSchema2;
