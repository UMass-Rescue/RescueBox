import { clsx, type ClassValue } from 'clsx';
import {
  BatchDirectoryInput,
  BatchFileInput,
  BatchTextInput,
  DirectoryInput,
  FileInput,
  FileResponse,
  Input,
  InputType,
  NewFileInputType,
  RequestBody,
  TaskSchema,
  TextInput,
} from 'src/shared/generated_models';
import { ModelServer } from 'src/shared/models';
import { twMerge } from 'tailwind-merge';
import { match, P } from 'ts-pattern';

// eslint-disable-next-line import/prefer-default-export
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function createMLServerMap(servers: ModelServer[]) {
  const serverMap: Record<string, ModelServer> = {};
  servers.forEach((server) => {
    serverMap[server.modelUid] = server;
  });
  return serverMap;
}

export function buildRequestBody(
  taskSchema: TaskSchema,
  data: { [key: string]: string | string[] },
): RequestBody {
  const requestBody: RequestBody = {
    inputs: {},
    parameters: {},
  };
  taskSchema.inputs.forEach((input) => {
    const inputData = data[input.key];
    match(input)
      .with({ inputType: 'text' }, () => {
        if (typeof inputData !== 'string') {
          throw new Error(`Invalid data type for text input: ${inputData}`);
        }
        requestBody.inputs[input.key] = { text: inputData };
      })
      .with({ inputType: 'textarea' }, () => {
        if (typeof inputData !== 'string') {
          throw new Error(`Invalid data type for textarea input: ${inputData}`);
        }
        requestBody.inputs[input.key] = { text: inputData };
      })
      .with({ inputType: 'file' }, () => {
        if (typeof inputData !== 'string') {
          throw new Error(`Invalid data type for file input: ${inputData}`);
        }
        requestBody.inputs[input.key] = {
          path: inputData,
        } satisfies FileInput;
      })
      .with({ inputType: 'directory' }, () => {
        if (typeof inputData !== 'string') {
          throw new Error(
            `Invalid data type for directory input: ${inputData}`,
          );
        }
        requestBody.inputs[input.key] = {
          path: inputData,
        } satisfies DirectoryInput;
      })
      .with({ inputType: 'batchtext' }, () => {
        if (!Array.isArray(inputData)) {
          throw new Error(
            `Invalid data type for batchtext input: ${inputData}`,
          );
        }
        requestBody.inputs[input.key] = {
          texts: inputData.map((text) => ({ text }) satisfies TextInput),
        } satisfies BatchTextInput;
      })
      .with({ inputType: 'batchfile' }, () => {
        if (!Array.isArray(inputData)) {
          throw new Error(
            `Invalid data type for batchfile input: ${inputData}`,
          );
        }
        requestBody.inputs[input.key] = {
          files: inputData.map((file) => ({ path: file }) satisfies FileInput),
        } satisfies BatchFileInput;
      })
      .with({ inputType: 'batchdirectory' }, () => {
        if (!Array.isArray(inputData)) {
          throw new Error(
            `Invalid data type for batchdirectory input: ${inputData}`,
          );
        }
        requestBody.inputs[input.key] = {
          directories: inputData.map(
            (dir) => ({ path: dir }) satisfies DirectoryInput,
          ),
        } satisfies BatchDirectoryInput;
      })
      .with(
        {
          inputType: {
            inputType: 'newfile',
          },
        },
        () => {
          if (typeof inputData !== 'string') {
            throw new Error(
              `Invalid data type for newfile input: ${inputData}`,
            );
          }
          requestBody.inputs[input.key] = {
            path: inputData,
          } satisfies FileInput;
        },
      )
      .exhaustive();
  });
  taskSchema.parameters.forEach((parameter) => {
    requestBody.parameters[parameter.key] = data[parameter.key];
  });
  return requestBody;
}

export function extractValuesFromRequestBodyInput(
  inputType: InputType | NewFileInputType,
  reqInput: Input,
): string | string[] {
  return match(inputType)
    .with(
      {
        inputType: 'newfile',
      },
      () => {
        if (!('path' in reqInput)) {
          throw new Error(
            `Invalid request body: 'path' was not in reqInput: ${reqInput}`,
          );
        }
        return reqInput.path;
      },
    )
    .with('text', () => {
      if (!('text' in reqInput)) {
        throw new Error(
          `Invalid request body: 'text' was not in reqInput: ${reqInput}`,
        );
      }
      return reqInput.text;
    })
    .with('textarea', () => {
      if (!('text' in reqInput)) {
        throw new Error(
          `Invalid request body: 'text' was not in reqInput: ${reqInput}`,
        );
      }
      return reqInput.text;
    })
    .with('file', () => {
      if (!('path' in reqInput)) {
        throw new Error(
          `Invalid request body: 'path' was not in reqInput: ${reqInput}`,
        );
      }
      return reqInput.path;
    })
    .with('directory', () => {
      if (!('path' in reqInput)) {
        throw new Error(
          `Invalid request body: 'path' was not in reqInput: ${reqInput}`,
        );
      }
      return reqInput.path;
    })
    .with('batchtext', () => {
      if (!('texts' in reqInput)) {
        throw new Error(
          `Invalid request body: 'texts' was not in reqInput: ${reqInput}`,
        );
      }
      return (reqInput as BatchTextInput).texts.map((text) => text.text);
    })
    .with('batchfile', () => {
      if (!('files' in reqInput)) {
        throw new Error(
          `Invalid request body: 'files' was not in reqInput: ${reqInput}`,
        );
      }
      return (reqInput as BatchFileInput).files.map((file) => file.path);
    })
    .with('batchdirectory', () => {
      if (!('directories' in reqInput)) {
        throw new Error(
          `Invalid request body: 'directories' was not in reqInput: ${reqInput}`,
        );
      }
      return (reqInput as BatchDirectoryInput).directories.map(
        (dir) => dir.path,
      );
    })
    .exhaustive();
}

export function partitionFilesByType(
  files: FileResponse[],
  searchTerms: Record<string, string>,
): Record<string, FileResponse[]> {
  const searchFilter = (file: FileResponse, searchTerm: string): boolean => {
    const fileName = file.path.split(/[/\\]/).pop();
    if (!fileName) return false;
    return fileName.toLowerCase().includes(searchTerm.toLowerCase());
  };

  return {
    img: files.filter(
      (file) => file.file_type === 'img' && searchFilter(file, searchTerms.img),
    ),
    csv: files.filter(
      (file) => file.file_type === 'csv' && searchFilter(file, searchTerms.csv),
    ),
    json: files.filter(
      (file) =>
        file.file_type === 'json' && searchFilter(file, searchTerms.json),
    ),
    text: files.filter(
      (file) =>
        file.file_type === 'text' && searchFilter(file, searchTerms.text),
    ),
    audio: files.filter(
      (file) =>
        file.file_type === 'audio' && searchFilter(file, searchTerms.audio),
    ),
    video: files.filter(
      (file) =>
        file.file_type === 'video' && searchFilter(file, searchTerms.video),
    ),
    markdown: files.filter(
      (file) =>
        file.file_type === 'markdown' &&
        searchFilter(file, searchTerms.markdown),
    ),
  };
}

export function isRunnableTaskSchema(taskSchema: TaskSchema): {
  runnable: boolean;
  reasons?: string[];
} {
  const reasons: string[] = [];
  const isRunnable = !taskSchema.parameters.some((paramSchema) =>
    match(paramSchema)
      .with(
        {
          value: {
            enumVals: P.array(),
          },
        },
        (enumParamSchema) => {
          reasons.push(
            `Parameter "${enumParamSchema.label}" has no available values to select from.`,
          );
          return enumParamSchema.value.enumVals.length === 0;
        },
      )
      .otherwise(() => false),
  );
  return isRunnable ? { runnable: true } : { runnable: false, reasons };
}
