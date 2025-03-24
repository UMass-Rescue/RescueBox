import {
  JobHandler,
  ModelsHandler,
  RegistrationHandler,
  FileSystemHandler,
  DatabaseHandler,
  LoggingHandler,
  TaskHandler,
  ElectronAPIHandler,
} from '../main/preload';

declare global {
  // eslint-disable-next-line no-unused-vars
  interface Window {
    registration: RegistrationHandler;
    models: ModelsHandler;
    job: JobHandler;
    task: TaskHandler;
    fileSystem: FileSystemHandler;
    database: DatabaseHandler;
    logging: LoggingHandler;
    electronAPI: ElectronAPIHandler;
  }
}

export {};
