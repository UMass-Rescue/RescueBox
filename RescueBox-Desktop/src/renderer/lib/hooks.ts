import { ModelAppStatus, ModelServer } from 'src/shared/models';
import useSWR, { SWRConfiguration } from 'swr';

const JOBS_REFRESH_INTERVAL = 200;

export function useServerStatuses(servers?: ModelServer[]) {
  const fetcher = () =>
    Promise.all(
      servers!.map((server) =>
        window.registration.getModelAppStatus({
          modelUid: server.modelUid,
        }),
      ),
    ).then((statuses) => {
      const serverStatuses: Record<string, ModelAppStatus> = {};
      for (let i = 0; i < servers!.length; i += 1) {
        serverStatuses[servers![i].modelUid] = statuses[i];
      }
      return serverStatuses;
    });

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    !servers ? null : `register:get-model-app-status`,
    fetcher,
  );

  return {
    serverStatuses: data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useServerStatus(modelUid?: string) {
  const fetcher = () =>
    window.registration.getModelAppStatus({
      modelUid: modelUid!,
    });

  const { data, error, isLoading, isValidating, mutate } = useSWR(
    !modelUid ? null : `register:get-model-app-status-${modelUid}`,
    fetcher,
  );

  return {
    serverStatus: data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useServers() {
  const serverFetcher = () => window.registration.getModelServers();
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    `register:get-model-servers`,
    serverFetcher,
  );

  return {
    servers: data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useServer(modelUid?: string, options?: SWRConfiguration) {
  const fetcher = () =>
    window.registration.getModelServer({ modelUid: modelUid! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    modelUid ? `register:get-model-app-ip-${modelUid}` : null,
    fetcher,
    options,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useMLModels() {
  const fetcher = () => window.models.getModels();
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    `models:get-models`,
    fetcher,
  );

  return {
    models: data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useMLModel(modelUid?: string) {
  const fetcher = () => window.models.getModelByUid({ modelUid: modelUid! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    modelUid ? `models:get-model-by-uid-${modelUid}` : null,
    fetcher,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useReadFile(path?: string) {
  const fetcher = () => window.fileSystem.readFile({ path: path! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    path ? `fileSystem:read-file-${path}` : null,
    fetcher,
  );
  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useDirFiles(path?: string) {
  const fetcher = () => window.fileSystem.getFilesFromDir({ path: path! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    path ? `fileSystem:get-files-from-dir-${path}` : null,
    fetcher,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useJobs() {
  const fetcher = () => window.job.getJobs();
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    `job:get-jobs`,
    fetcher,
    {
      refreshInterval: JOBS_REFRESH_INTERVAL,
    },
  );

  return {
    jobs: data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useJob(jobId?: string) {
  const fetcher = () => window.job.getJobById({ uid: jobId! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    jobId ? `job:get-job-by-id-${jobId}` : null,
    fetcher,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useLogs() {
  const fetcher = () => window.logging.getLogs();
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    `logging:get-logs`,
    fetcher,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useModelInfo(modelUid?: string) {
  const fetcher = () => window.models.getModelByUid({ modelUid: modelUid! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    modelUid ? `models:get-model-by-uid-${modelUid}` : null,
    fetcher,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useTaskSchema(modelUid?: string, taskId?: string) {
  const fetcher = async () =>
    window.task.getTaskSchema({
      modelUid: modelUid!,
      taskId: taskId!,
    });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    modelUid && taskId ? `task:get-task-schema-${modelUid}-${taskId}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
    },
  );
  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useTask(taskId?: string, modelUid?: string) {
  const fetcher = async () =>
    window.task.getTaskByModelUidAndTaskId({
      modelUid: modelUid!,
      taskId: taskId!,
    });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    modelUid && taskId
      ? `task:get-task-by-model-uid-and-task-id-${modelUid}-${taskId}`
      : null,
    fetcher,
    {
      revalidateOnFocus: false,
    },
  );
  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}

export function useApiRoutes(modelUid?: string) {
  const fetcher = () => window.task.getApiRoutes({ modelUid: modelUid! });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    modelUid ? `task:get-api-routes-${modelUid}` : null,
    fetcher,
  );

  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}
export function useFilePathIcon(filePath: string) {
  const fetcher = () => window.fileSystem.getFileIcon({ path: filePath });
  const { data, error, isLoading } = useSWR(
    filePath ? `fileSystem:get-file-icon` : null,
    fetcher,
  );
  return {
    data,
    error,
    isLoading,
  };
}

export function useFileIcons(paths: string[]) {
  const fetcher = () =>
    Promise.all(
      paths.map((path) => window.fileSystem.getFileIcon({ path })),
    ).then((icons) => {
      const fileIcons: Record<string, string> = {};
      icons.forEach((icon, idx) => {
        fileIcons[paths[idx]] = icon;
      });
      return fileIcons;
    });
  const { data, error, isLoading, isValidating, mutate } = useSWR(
    paths ? `fileSystem:get-file-icon` : null,
    fetcher,
  );
  return {
    data,
    error,
    isLoading,
    isValidating,
    mutate,
  };
}
