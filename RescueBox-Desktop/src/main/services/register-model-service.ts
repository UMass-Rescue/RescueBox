/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  APIRoutes,
  ListPlugins,
  AppMetadata,
  SchemaAPIRoute,
} from 'src/shared/generated_models';
import { isrModelRoutes } from 'src/main/database/dummy_data/mlmodels';
import log from 'electron-log/main';
import path from 'path';
import isDummyMode from 'src/shared/dummy_data/set_dummy_mode';
import MLModelDb from '../models/ml-model';
import ModelServerDb from '../models/model-server';
import { spawn, ChildProcess } from 'child_process';
import TaskDb from '../models/tasks';

const API_LISTPLUGINS_SLUG = '/manage/list_plugins';

type ModelMetadataError = { error: 'App metadata not set' };


export enum ServerStatus {
  Running = 'Running',
  Starting = 'Starting',
  Completed = 'Starting',
  Failed = 'Failed',
}

const isDevelopment =
process.env.NODE_ENV === 'development' || process.env.DEBUG_PROD === 'true';

export default class RegisterModelService {
  // List Plugins call


  /**
   * Start RescueBox server
   */

  public static IS_SERVER_RUNNING = false;

  public static serverPath = path.join(
    process.resourcesPath,
    'assets',
    'rb_server',
    'dist',
    'rescuebox',
  );
  public static serverExe = path.join(RegisterModelService.serverPath, 'rescuebox.exe',);
  public static  childprocess: ChildProcess;

  public static  async startServer() {
    if (isDevelopment) {
      log.info(`Skip Starting server ${RegisterModelService.serverExe}`);
      return;
    }
    log.info(`Starting server ${RegisterModelService.serverExe}`);
    const options: any[] = [];
    const defaults = {
      cwd: RegisterModelService.serverPath,
      env: process.env,
    };
    if (RegisterModelService.IS_SERVER_RUNNING)
      return;
    RegisterModelService.childprocess = spawn(RegisterModelService.serverExe, options, defaults);
    if (RegisterModelService.childprocess != null) {
      RegisterModelService.childprocess.stdout?.on('data', (data: any) => {
        log.info(`sever ${data}`);
        RegisterModelService.IS_SERVER_RUNNING = true;
      });

      RegisterModelService.childprocess.stderr?.on('data', (data: any) => {
        log.info(`sever ${data}`);
      });
    }
  }

  static async registerModel(serverAddress: string, serverPort: number): Promise<boolean>{
    let listPlugins: ListPlugins = [];
    RegisterModelService.startServer();
    while (!RegisterModelService.IS_SERVER_RUNNING) {
      listPlugins = await RegisterModelService.getListPlugins(
        serverAddress,
        serverPort,
      );
      log.info(`listPlugins ${listPlugins.length} ${listPlugins}`);
      if (listPlugins.length > 0) {
        break;
      }
      log.info(`waiting for fastapi rescuebox server to start on ${serverAddress}:${serverPort}`);
      const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
      await sleep(10000); // Wait for 10 seconds
    }
    let db: ModelServerDb[] = [];
    // eslint-disable-next-line no-await-in-loop

    // eslint-disable-next-line no-await-in-loop
    for (let i = 0; i < listPlugins.length; i += 1) {
      // eslint-disable-next-line no-await-in-loop
      const plugins = listPlugins;
      const plugin = plugins[i];
      log.info(`Got plugin ${plugin}`);
      const pluginName = String(plugin);
      if (pluginName === 'fs' || pluginName === 'docs') {
        // eslint-disable-next-line no-continue
        continue;
      }
      log.info(`Registering new plugin_name=${plugin}`);
      // eslint-disable-next-line no-await-in-loop
      db[i] = await RegisterModelService.registerEachPlugin(
        serverAddress,
        serverPort,
        pluginName,
      );
    }
    return true;
  }

  public static getListPlugins(
    serverAddress: string,
    serverPort: number,
  ): Promise<ListPlugins> {
    log.info(
      `Fetching list plugins from http://${serverAddress}:${serverPort}${API_LISTPLUGINS_SLUG}`,
    );

    return fetch(
      `http://${serverAddress}:${serverPort}${API_LISTPLUGINS_SLUG}`,
      { method: 'POST' },
    )
      .then(async (res) => {
        if (res.status === 404) {
          throw new Error('404 ListPlugins not found on server', {
            cause: res.statusText,
          });
        }
        if (res.status !== 200) {
          throw new Error('Failed to fetch ListPlugins.');
        }
        return res.json();
      })
      .then((data: ListPlugins | ModelMetadataError) => {
        if ('error' in data) {
          return [];
        }
        return data;
      })
      .catch((error) => {
        log.error('Failed to fetch ListPlugins', error);
        return [];
      });
  }

  private static async registerEachPlugin(
    serverAddress: string,
    serverPort: number,
    pluginName: string,
    gpu: boolean = false,
  ): Promise<ModelServerDb> {
    const modelInfo = await RegisterModelService.getAppMetadata(
      serverAddress,
      serverPort,
      pluginName,
    );
    log.info(`Model name: ${modelInfo.name} Plugin name: ${pluginName} {gpu: ${modelInfo.gpu}}`);
    const apiRoutes = await RegisterModelService.getAPIRoutes(
      serverAddress,
      serverPort,
      pluginName,
    );

    // Use the stable model name to find the model
    const prevModel = await MLModelDb.findByName(modelInfo.name);
    if (prevModel) {
      log.info(`Nodel found in db with uid ${prevModel.uid}`);
      log.info(
        `Updating registration info for ${prevModel.uid} at ${serverAddress}:${serverPort}`,
      );
      // Update the existing model's metadata and routes
      const updatedModel = await MLModelDb.updateModel(
        modelInfo, // Pass appMetadata directly
        apiRoutes,
      );
      if (updatedModel) {
          await ModelServerDb.updateServer(
            updatedModel.uid,
            serverAddress,
            serverPort,
            pluginName,
          );

        const server = await ModelServerDb.getServerByModelUid(updatedModel.uid);
        if (!server) {
          throw new Error(`FATAL: Server not found for model ${updatedModel.uid}`);
        }
        log.info(`Existing model updated for ${server.pluginName}`);
        return server;
      }
    }
    log.info(
      `Registering new model app metadata at ${serverAddress}:${serverPort}`,
    );
    const modelDb = await MLModelDb.createModel(modelInfo, apiRoutes);
    await RegisterModelService.createTasks(
      RegisterModelService.getSchemaApiRoutes(apiRoutes),
      modelDb.uid,
    );
    return ModelServerDb.registerServer(
      modelDb.uid,
      serverAddress,
      serverPort,
      pluginName,
    );
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
    pluginName: string,
  ): Promise<AppMetadata> {
    const APP_METADATA_SLUG = `/${pluginName}/api/app_metadata`;
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
    pluginName: string,
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
    const API_ROUTES_SLUG = `/${pluginName}/api/routes`;
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
