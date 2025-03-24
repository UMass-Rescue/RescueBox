/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  APIRoutes,
  AppMetadata,
  SchemaAPIRoute,
} from 'src/shared/generated_models';
import { isrModelRoutes } from 'src/main/database/dummy_data/mlmodels';
import log from 'electron-log/main';
import isDummyMode from 'src/shared/dummy_data/set_dummy_mode';
import MLModelDb from '../models/ml-model';
import ModelServerDb from '../models/model-server';
import TaskDb from '../models/tasks';

const API_ROUTES_SLUG = '/api/routes';
const APP_METADATA_SLUG = '/api/app_metadata';

type ModelMetadataError = { error: 'App metadata not set' };

export default class RegisterModelService {
  static async registerModel(serverAddress: string, serverPort: number) {
    const modelInfo = await RegisterModelService.getAppMetadata(
      serverAddress,
      serverPort,
    );
    const apiRoutes = await RegisterModelService.getAPIRoutes(
      serverAddress,
      serverPort,
    );
    const prevModel = await MLModelDb.getModelByModelInfoAndRoutes(
      modelInfo,
      apiRoutes,
    );
    if (prevModel) {
      log.info(`Old model found with uid ${prevModel.uid}`);
      log.info(
        `Updating registration info for ${prevModel.uid} at ${serverAddress}:${serverPort}`,
      );
      await MLModelDb.restoreModel(prevModel.uid);
      await ModelServerDb.updateServer(
        prevModel.uid,
        serverAddress,
        serverPort,
      );
      const server = await ModelServerDb.getServerByModelUid(prevModel.uid);
      if (!server) {
        throw new Error(`FATAL: Server not found for model ${prevModel.uid}`);
      }
      return server;
    }
    log.info(
      `Registering new model app metadata at ${serverAddress}:${serverPort}`,
    );
    const modelDb = await MLModelDb.createModel(modelInfo, apiRoutes);
    await RegisterModelService.createTasks(
      RegisterModelService.getSchemaApiRoutes(apiRoutes),
      modelDb.uid,
    );
    return ModelServerDb.registerServer(modelDb.uid, serverAddress, serverPort);
  }

  private static getSchemaApiRoutes(apiRoutes: APIRoutes) {
    return apiRoutes.filter((apiRoute) => 'order' in apiRoute);
  }

  private static async createTasks(
    apiRoutes: SchemaAPIRoute[],
    modelUid: string,
  ) {
    const taskParams = apiRoutes.map((route) => ({
      uid: String(route.order),
      modelUid,
      schemaApiRoute: route,
    }));
    return TaskDb.createTasks(taskParams);
  }

  static async getAppMetadata(
    serverAddress: string,
    serverPort: number,
  ): Promise<AppMetadata> {
    log.info(
      `Fetching app metadata from http://${serverAddress}:${serverPort}${APP_METADATA_SLUG}`,
    );

    return fetch(`http://${serverAddress}:${serverPort}${APP_METADATA_SLUG}`)
      .then(async (res) => {
        if (res.status === 404) {
          throw new Error('404 APP_METADATA_SLUG not found on server', {
            cause: res.statusText,
          });
        }
        if (res.status !== 200) {
          throw new Error('Failed to fetch app metadata.');
        }
        return res.json();
      })
      .then((data: AppMetadata | ModelMetadataError) => {
        if ('error' in data) {
          throw new Error('App metadata not set');
        }
        return data;
      })
      .catch((error) => {
        log.error('Failed to fetch app metadata', error);
        throw error;
      });
  }

  static async getAPIRoutes(
    serverAddress: string,
    serverPort: number,
  ): Promise<APIRoutes> {
    if (isDummyMode) {
      log.info(
        'Fetching API routes for isr model from dummy data. This will take some time.',
      );
      const apiRoutes = isrModelRoutes;
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(RegisterModelService.getSchemaApiRoutes(apiRoutes));
        }, 1000);
      });
    }
    const url = `http://${serverAddress}:${serverPort}${API_ROUTES_SLUG}`;
    log.info(`Fetching API routes from ${url}`);
    const apiRoutes: APIRoutes = await fetch(url)
      .then((res) => {
        if (res.status !== 200) {
          throw new Error(`Failed to fetch API routes. Status: ${res.status}`);
        }
        return res.json();
      })
      .catch((error) => {
        log.error('Failed to fetch API routes', error);
        throw new Error('Failed to fetch API routes. Server may be offline.');
      });
    return apiRoutes;
  }
}
