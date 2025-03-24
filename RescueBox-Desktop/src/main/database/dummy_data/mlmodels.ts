import { createModelId } from 'src/main/models/ml-model';
import isrAppMetadata from 'src/shared/dummy_data/info_page';
import { APIRoutes, AppMetadata } from 'src/shared/generated_models';

export const isrModelRoutes: APIRoutes = [
  {
    order: 0,
    payload_schema: '/super-resolution/payload_schema',
    run_task: '/super-resolution',
    sample_payload: '/super-resolution/sample_payload',
    short_title: 'Super Resolution',
    task_schema: '/super-resolution/task_schema',
  },
];

export const sbfAppMetadata: AppMetadata = {
  name: 'Small Block Forensics',
  info: `
# Small Block Forensics
This model determines the existence of any subset of some small dataset in a large target dataset.

## Input Type
- **Image:** The small dataset to be searched for in the large dataset.
## Output Type
- **Text:** True or False for each element in the small dataset, indicating whether it exists in the large dataset.

## Parameters
- **Block Size:** The size of the blocks to be hashed and compared between the small and large datasets.

## Constraints
- **Block Size Range:** The block size must be positive and less than the size of the small dataset.
- **Target Probability:** This value should be between 0 and 1 (inclusive).
`,
  author: 'Jane Appleseed',
  version: '1.0.0',
};

export const sbfModelRoutes: APIRoutes = [
  {
    order: 0,
    payload_schema: '/gen_hash_random/payload_schema',
    run_task: '/gen_hash_random',
    sample_payload: '/gen_hash_random/sample_payload',
    short_title: 'Hash random blocks of a target directory',
    task_schema: '/gen_hash_random/task_schema',
  },
  {
    order: 1,
    payload_schema: '/hash_random/payload_schema',
    run_task: '/hash_random',
    sample_payload: '/hash_random/sample_payload',
    short_title: 'Hash random blocks of a target directory with seed DB',
    task_schema: '/hash_random/task_schema',
  },
  {
    order: 2,
    payload_schema: '/gen_hash/payload_schema',
    run_task: '/gen_hash',
    sample_payload: '/gen_hash/sample_payload',
    short_title: 'Generate SQLite DB of Hashes',
    task_schema: '/gen_hash/task_schema',
  },
];

export const imgObjAppMetadata: AppMetadata = {
  name: 'Image Object Detection',
  info: `
# Image Object Detection
This model identifies and classifies objects in an image.

## Input Type
- **Image:** The image to be analyzed.

## Output Type
- **Image:** The analyzed image with bounding boxes around detected objects.
- **CSV:** A CSV file containing the bounding boxes, labels, probabilities of detected objects.

## Parameters
- **Model Type:** The type of model to use for object detection.
- **Threshold:** The minimum probability required for an object to be detected.

## Constraints
- **Dictionary size:** Detects 80 common objects
`,
  author: 'Random Hacker',
  version: '1.0.0',
};

export const imgObjModelRoutes: APIRoutes = [
  {
    order: 0,
    payload_schema: '/detect/payload_schema',
    run_task: '/detect',
    sample_payload: '/detect/sample_payload',
    short_title: 'Detect Objects',
    task_schema: '/detect/task_schema',
  },
];

export const dummyModels: { appMetadata: AppMetadata; routes: APIRoutes }[] = [
  {
    appMetadata: isrAppMetadata,
    routes: isrModelRoutes,
  },
  {
    appMetadata: sbfAppMetadata,
    routes: sbfModelRoutes,
  },
  {
    appMetadata: imgObjAppMetadata,
    routes: imgObjModelRoutes,
  },
];

export const isrModelId = createModelId(isrAppMetadata, isrModelRoutes);
export const sbfModelId = createModelId(sbfAppMetadata, sbfModelRoutes);
export const imgObjModelId = createModelId(
  imgObjAppMetadata,
  imgObjModelRoutes,
);
