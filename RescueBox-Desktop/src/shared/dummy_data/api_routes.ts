import { APIRoutes } from '../generated_models';

const dummyApiRoutes: APIRoutes = [
  {
    order: 1,
    payload_schema: '/transcription/payload_schema',
    run_task: '/transcription',
    sample_payload: '/transcription/sample_payload',
    short_title: 'Audio Transcription',
    task_schema: '/transcription/task_schema',
  },
  {
    order: 2,
    payload_schema: '/named_entity_recognition/payload_schema',
    run_task: '/named_entity_recognition',
    sample_payload: '/named_entity_recognition/sample_payload',
    short_title: 'Text Named Entity Recognition',
    task_schema: '/named_entity_recognition/task_schema',
  },
  {
    order: 0,
    payload_schema:
      '/transcription_and_named_entity_recognition/payload_schema',
    run_task: '/transcription_and_named_entity_recognition',
    sample_payload:
      '/transcription_and_named_entity_recognition/sample_payload',
    short_title: 'Audio Transcription and NER',
    task_schema: '/transcription_and_named_entity_recognition/task_schema',
  },
  {
    order: 3,
    payload_schema: '/gen_hash_random/payload_schema',
    run_task: '/gen_hash_random',
    sample_payload: '/gen_hash_random/sample_payload',
    short_title: 'Hash Random Blocks of a Target Directory',
    task_schema: '/gen_hash_random/task_schema',
  },
] satisfies APIRoutes;

export default dummyApiRoutes;
