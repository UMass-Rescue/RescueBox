import { SchemaAPIRoute } from 'src/shared/generated_models';
import { imgObjModelId, isrModelId, sbfModelId } from './mlmodels';

const dummyTaskData: {
  uid: string;
  modelUid: string;
  schemaApiRoute: SchemaAPIRoute;
}[] = [
  {
    uid: '0',
    modelUid: isrModelId,
    schemaApiRoute: {
      order: 0,
      payload_schema: '/gen_hash_random/payload_schema',
      run_task: '/gen_hash_random',
      sample_payload: '/gen_hash_random/sample_payload',
      short_title: 'Hash random blocks of a target directory',
      task_schema: '/gen_hash_random/task_schema',
    },
  },
  {
    uid: '0',
    modelUid: sbfModelId,
    schemaApiRoute: {
      order: 0,
      payload_schema: '/gen_hash_random/payload_schema',
      run_task: '/gen_hash_random',
      sample_payload: '/gen_hash_random/sample_payload',
      short_title: 'Hash random blocks of a target directory',
      task_schema: '/gen_hash_random/task_schema',
    },
  },
  {
    uid: '0',
    modelUid: imgObjModelId,
    schemaApiRoute: {
      order: 0,
      payload_schema: '/detect/payload_schema',
      run_task: '/detect',
      sample_payload: '/detect/sample_payload',
      short_title: 'Detect Objects',
      task_schema: '/detect/task_schema',
    },
  },
];

export default dummyTaskData;
