import { SchemaAPIRoute } from 'src/shared/generated_models';
import ModelAppService from '../services/model-app-service';
import TaskDb from '../models/tasks';
import { getRaw } from '../util';

export type GetApiRoutesArgs = {
  modelUid: string;
};

export type GetAppMetadataArgs = {
  modelUid: string;
};

export type GetTaskSchemaArgs = {
  modelUid: string;
  taskId: string;
};

export type GetTaskByModelUidAndTaskIdArgs = GetTaskSchemaArgs;

const getApiRoutes = async (
  _event: any,
  arg: GetApiRoutesArgs,
): Promise<SchemaAPIRoute[]> => {
  const service = await ModelAppService.init(arg.modelUid);
  return service.getApiRoutes();
};

const getAppMetadata = async (_event: any, arg: GetAppMetadataArgs) => {
  const service = await ModelAppService.init(arg.modelUid);
  return service.getAppMetadata();
};

const getTaskSchema = async (_event: any, arg: GetTaskSchemaArgs) => {
  const service = await ModelAppService.init(arg.modelUid);
  return service.getTaskSchema(arg.taskId);
};

const getTaskByModelUidAndTaskId = async (
  _event: any,
  arg: GetTaskByModelUidAndTaskIdArgs,
) => {
  return TaskDb.getTaskByModelUidAndTaskId(arg.taskId, arg.modelUid).then(
    getRaw,
  );
};

export {
  getApiRoutes,
  getAppMetadata,
  getTaskSchema,
  getTaskByModelUidAndTaskId,
};
