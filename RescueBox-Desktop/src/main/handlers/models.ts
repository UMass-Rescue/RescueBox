import MLModelDb from '../models/ml-model';
import { getRaw } from '../util';

export type GetModelByUidArgs = {
  modelUid: string;
};

export type RemoveModelByUidArgs = {
  modelUid: string;
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function getModels(_event: any, _arg: any) {
  return MLModelDb.findAll().then((modelsDb) => modelsDb.map(getRaw));
}

export async function getModelByUid(event: any, arg: GetModelByUidArgs) {
  return MLModelDb.getModelByUid(arg.modelUid).then(getRaw);
}

export async function removeModelByUid(event: any, arg: RemoveModelByUidArgs) {
  return MLModelDb.removeModel(arg.modelUid);
}
