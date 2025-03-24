// Disable no-unused-vars, broken for spread args
/* eslint no-unused-vars: off */
import { contextBridge, ipcRenderer } from 'electron';
import {
  MLModel,
  ModelServer,
  Job,
  ModelAppStatus,
  RunJobArgs,
  Task,
} from 'src/shared/models';
import {
  AppMetadata,
  SchemaAPIRoute,
  TaskSchema,
} from 'src/shared/generated_models';
import {
  GetModelAppStatusArgs,
  GetModelServerArgs,
  RegisterModelArgs,
  UnregisterModelArgs,
} from './handlers/registration';
import { JobByIdArgs } from './handlers/job';
import { GetModelByUidArgs, RemoveModelByUidArgs } from './handlers/models';
import {
  NewFileArgs,
  FileInfo,
  JoinPathArgs,
  PathArgs,
} from './handlers/file-system';
import {
  GetApiRoutesArgs,
  GetAppMetadataArgs,
  GetTaskByModelUidAndTaskIdArgs,
  GetTaskSchemaArgs,
} from './handlers/task';

const registrationHandler = {
  registerModelAppIp: (args: RegisterModelArgs) =>
    ipcRenderer.invoke(
      'register:register-model-app-ip',
      args,
    ) as Promise<ModelServer>,
  unregisterModelAppIp: (args: UnregisterModelArgs) =>
    ipcRenderer.invoke(
      'register:unregister-model-app-ip',
      args,
    ) as Promise<number>,
  getModelAppStatus: (args: GetModelAppStatusArgs) =>
    ipcRenderer.invoke(
      'register:get-model-app-status',
      args,
    ) as Promise<ModelAppStatus>,
  getModelServers: () =>
    ipcRenderer.invoke('register:get-model-servers') as Promise<ModelServer[]>,
  getModelServer: (args: GetModelServerArgs) =>
    ipcRenderer.invoke(
      'register:get-model-server',
      args,
    ) as Promise<ModelServer>,
};

const modelsHandler = {
  getModels: () =>
    ipcRenderer.invoke('models:get-models') as Promise<MLModel[]>,
  getModelByUid: (args: GetModelByUidArgs) =>
    ipcRenderer.invoke('models:get-model-by-uid', args) as Promise<MLModel>,
  removeModelByUid: (args: RemoveModelByUidArgs) =>
    ipcRenderer.invoke('models:remove-model-by-uid', args) as Promise<void>,
};

const jobHandler = {
  getJobs: () => ipcRenderer.invoke('job:get-jobs') as Promise<Job[]>,
  getJobById: (args: JobByIdArgs) =>
    ipcRenderer.invoke('job:get-job-by-id', args) as Promise<Job>,
  runJob: (args: RunJobArgs) =>
    ipcRenderer.invoke('job:run-job', args) as Promise<Job>,
  cancelJob: (args: JobByIdArgs) =>
    ipcRenderer.invoke('job:cancel-job', args) as Promise<void>,
  deleteJobById: (args: JobByIdArgs) =>
    ipcRenderer.invoke('job:delete-job-by-id', args) as Promise<number>,
};

const fileSystemHandler = {
  readFile: (args: PathArgs) =>
    ipcRenderer.invoke('fileSystem:read-file', args) as Promise<string>,
  openPath: (args: PathArgs) =>
    ipcRenderer.invoke('fileSystem:open-path', args) as Promise<string>,
  showFileInExplorer: (args: PathArgs) =>
    ipcRenderer.invoke(
      'fileSystem:show-file-in-explorer',
      args,
    ) as Promise<void>,
  selectDirectory: () =>
    ipcRenderer.invoke('fileSystem:select-directory') as Promise<string>,
  selectDirectories: () =>
    ipcRenderer.invoke('fileSystem:select-directories') as Promise<string[]>,
  selectFile: () =>
    ipcRenderer.invoke('fileSystem:select-file') as Promise<string>,
  selectFiles: () =>
    ipcRenderer.invoke('fileSystem:select-files') as Promise<string[]>,
  selectFileSave: (args: NewFileArgs) =>
    ipcRenderer.invoke('fileSystem:select-file-save', args) as Promise<string>,
  saveLogs: () => ipcRenderer.invoke('fileSystem:save-logs'),
  getFilesFromDir: (args: PathArgs) =>
    ipcRenderer.invoke('fileSystem:get-files-from-dir', args) as Promise<
      FileInfo[]
    >,
  deleteFile: (args: PathArgs) =>
    ipcRenderer.invoke('fileSystem:delete-file', args) as Promise<void>,
  getFileIcon: (args: PathArgs) =>
    ipcRenderer.invoke('fileSystem:get-file-icon', args) as Promise<string>,
  joinPath: (args: JoinPathArgs) =>
    ipcRenderer.invoke('fileSystem:join-path', args) as Promise<string>,
};

const databaseHandler = {
  resetDatabase: () => ipcRenderer.invoke('database:reset-database'),
};

const taskHandler = {
  getApiRoutes: (args: GetApiRoutesArgs) =>
    ipcRenderer.invoke('task:get-api-routes', args) as Promise<
      SchemaAPIRoute[]
    >,
  getAppMetadata: (args: GetAppMetadataArgs) =>
    ipcRenderer.invoke('task:get-app-metadata', args) as Promise<AppMetadata>,
  getTaskSchema: (args: GetTaskSchemaArgs) =>
    ipcRenderer.invoke('task:get-task-schema', args) as Promise<TaskSchema>,
  getTaskByModelUidAndTaskId: (args: GetTaskByModelUidAndTaskIdArgs) =>
    ipcRenderer.invoke(
      'task:get-task-by-model-uid-and-task-id',
      args,
    ) as Promise<Task>,
};

const loggingHandler = {
  getLogs: () =>
    ipcRenderer.invoke('logging:get-logs') as Promise<
      {
        path: string;
        lines: string[];
      }[]
    >,
  clearLogs: () => ipcRenderer.invoke('logging:clear-logs') as Promise<boolean>,
};

const electronAPIHandler = {
  onNavigate: (callback: (arg: any) => void) =>
    ipcRenderer.on('navigate-to', (event, page) => callback(page)),
  offNavigate: () => ipcRenderer.removeAllListeners('navigate-to'),
};

contextBridge.exposeInMainWorld('registration', registrationHandler);
contextBridge.exposeInMainWorld('models', modelsHandler);
contextBridge.exposeInMainWorld('job', jobHandler);
contextBridge.exposeInMainWorld('fileSystem', fileSystemHandler);
contextBridge.exposeInMainWorld('database', databaseHandler);
contextBridge.exposeInMainWorld('logging', loggingHandler);
contextBridge.exposeInMainWorld('task', taskHandler);
contextBridge.exposeInMainWorld('electronAPI', electronAPIHandler);

export type RegistrationHandler = typeof registrationHandler;
export type ModelsHandler = typeof modelsHandler;
export type JobHandler = typeof jobHandler;
export type FileSystemHandler = typeof fileSystemHandler;
export type DatabaseHandler = typeof databaseHandler;
export type LoggingHandler = typeof loggingHandler;
export type TaskHandler = typeof taskHandler;
export type ElectronAPIHandler = typeof electronAPIHandler;
