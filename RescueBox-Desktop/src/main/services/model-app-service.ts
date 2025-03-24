/* eslint-disable class-methods-use-this */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { MLModel, ModelServer } from 'src/shared/models';
import {
  AppMetadata,
  TaskSchema,
  RequestBody,
  ResponseBody,
  SchemaAPIRoute,
} from 'src/shared/generated_models';
import dummyApiRoutes from 'src/shared/dummy_data/api_routes';
import markdownResponseBody from 'src/shared/dummy_data/markdown_response';
import taskSchemas from 'src/shared/dummy_data/task_schemas';
import isDummyMode from 'src/shared/dummy_data/set_dummy_mode';
import camelcaseKeys from 'camelcase-keys';
import log from 'electron-log/main';
import http from 'http';
import ModelServerDb from '../models/model-server';
import MLModelDb, { createModelId } from '../models/ml-model';
import RegisterModelService from './register-model-service';

const API_ROUTES_SLUG = '/api/routes';

class ModelAppService {
  private modelDb: MLModel;

  private modelServer: ModelServer;

  private apiRoutes: SchemaAPIRoute[];

  private constructor(modelDb: MLModel, server: ModelServer) {
    this.modelDb = modelDb;
    this.modelServer = server;
    if (isDummyMode) {
      this.apiRoutes = dummyApiRoutes.filter((apiRoute) => 'order' in apiRoute);
    } else {
      this.apiRoutes = modelDb.routes.filter((apiRoute) => 'order' in apiRoute);
    }
  }

  static async init(modelUid: string): Promise<ModelAppService> {
    const modelServer = await ModelServerDb.getServerByModelUid(modelUid);
    if (!modelServer) {
      throw new Error(`Server not found for model ${modelUid}`);
    }
    const modelDb = await MLModelDb.getModelByUid(modelUid);
    if (!modelDb) {
      throw new Error(`Model not found for model ${modelUid}`);
    }
    return new ModelAppService(modelDb, modelServer);
  }

  public async getApiRoutes(): Promise<SchemaAPIRoute[]> {
    return this.apiRoutes;
  }

  public async getAppMetadata(): Promise<AppMetadata> {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          name: this.modelDb.name,
          version: this.modelDb.version,
          author: this.modelDb.author,
          info: this.modelDb.info,
        } satisfies AppMetadata);
      }, 1000);
    });
  }

  public checkValidTaskId(taskId: string): boolean {
    const task = this.apiRoutes.find((route) => String(route.order) === taskId);
    return !!task;
  }

  public findRouteByTaskId(taskId: string): SchemaAPIRoute {
    const task = this.apiRoutes.find((route) => String(route.order) === taskId);
    if (!task) {
      throw new Error('Task not found');
    }
    return task;
  }

  public async runTask(
    taskId: string,
    requestBody: RequestBody,
  ): Promise<ResponseBody> {
    if (isDummyMode) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(markdownResponseBody);
        }, 1000);
      });
    }
    const task = this.findRouteByTaskId(taskId);
    const postData = JSON.stringify(requestBody);
    return new Promise((resolve, reject) => {
      const req = http.request(
        {
          host: this.modelServer.serverAddress,
          port: this.modelServer.serverPort,
          path: task.run_task,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData),
          },
          timeout: 1800000,
        },
        (res) => {
          let responseData = '';

          // Collect response data
          res.on('data', (chunk) => {
            responseData += chunk;
          });

          // Handle the end of the response
          res.on('end', () => {
            if (!res || !res.statusCode) {
              log.error(`No response received ${res}`);
              reject(new Error(`No response received ${res}`));
              return;
            }
            if (res.statusCode !== 200) {
              // Handle non-200 status codes
              log.error(`Request failed with status code: ${res.statusCode}`);
              try {
                const errorResponse = JSON.parse(responseData);
                log.error('Error details:', errorResponse);
                reject(new Error(errorResponse.error));
              } catch (parseError) {
                log.error('Error parsing response body:', responseData);
                reject(
                  new Error(`Failed to parse response body ${responseData}`),
                );
              }
              return;
            }
            try {
              const jsonResponse = JSON.parse(responseData);
              resolve(jsonResponse);
            } catch (error) {
              reject(new Error(`Error parsing JSON: ${error}`));
            }
          });
        },
      );
      req.on('error', (error) => {
        reject(new Error('Request error:', error));
      });

      // Write data to request body
      req.write(postData);
      req.end();
    }).then((data) => data as unknown as ResponseBody);
  }

  public async getTaskSchema(taskId: string): Promise<TaskSchema> {
    if (isDummyMode) {
      log.info(`Fetching task schema for task ${taskId}`);
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(taskSchemas[Number(taskId)]);
        }, 1000);
      });
    }
    const task = this.findRouteByTaskId(taskId);
    const url = `http://${this.modelServer.serverAddress}:${this.modelServer.serverPort}${task.task_schema}`;
    return fetch(url)
      .then((res) => {
        if (res.status !== 200) {
          throw new Error('Failed to fetch task schema.');
        }
        return res.json();
      })
      .then(
        (data: Record<string, unknown>) =>
          camelcaseKeys(data, { deep: true }) as unknown as TaskSchema,
      )
      .catch((error) => {
        log.error('Failed to fetch task schema', error);
        throw new Error('Failed to fetch task schema. Server may be offline.');
      });
  }

  public async pingHealth(): Promise<boolean> {
    if (isDummyMode) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(true);
        }, 1000);
      });
    }
    try {
      // Get the model data
      const modelInfo = await RegisterModelService.getAppMetadata(
        this.modelServer.serverAddress,
        this.modelServer.serverPort,
      );
      const apiRoutes = await RegisterModelService.getAPIRoutes(
        this.modelServer.serverAddress,
        this.modelServer.serverPort,
      );
      // Recreate the UID
      const uid = createModelId(modelInfo, apiRoutes);

      // Check if UID matches the current model
      return this.modelDb.uid === uid;
    } catch {
      return false;
    }
  }
}

export default ModelAppService;
