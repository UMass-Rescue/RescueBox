/* eslint-disable no-use-before-define */
declare namespace Components {
  namespace Schemas {
    export type APIRoutes = (SchemaAPIRoute | NoSchemaAPIRoute)[];
    /**
     * example:
     * {
     *   "info": "# Welcome to the Face Match App\n\nThis app will help you to match faces in your images..."
     * }
     */
    export interface AppMetadata {
      /**
       * Markdown content to render on the info page
       */
      info: string;
      author: string;
      version: string;
      /**
       * example:
       * Face Match App
       */
      name: string;
    }
    export interface BatchDirectoryInput {
      directories: DirectoryInput[];
    }
    export interface BatchDirectoryResponse {
      output_type: 'batchdirectory';
      directories: DirectoryResponse[];
    }
    export interface BatchFileInput {
      files: FileInput[];
    }
    export interface BatchFileResponse {
      output_type: 'batchfile';
      files: FileResponse[];
    }
    export interface BatchTextInput {
      texts: TextInput[];
    }
    export interface BatchTextResponse {
      output_type: 'batchtext';
      texts: TextResponse[];
    }
    export interface DirectoryInput {
      path: string;
    }
    export interface DirectoryResponse {
      output_type: 'directory';
      path: string;
      title: string;
      subtitle?: string | null;
    }
    export interface EnumParameterDescriptor {
      parameterType: ParameterType;
      enumVals: {
        label?: string;
        key?: string;
      }[];
      messageWhenEmpty?: string | null;
      default: string;
    }
    export interface FileInput {
      path: string;
    }
    export interface FileResponse {
      output_type: 'file';
      file_type:
        | 'img'
        | 'csv'
        | 'json'
        | 'text'
        | 'audio'
        | 'video'
        | 'markdown';
      path: string;
      title?: string | null;
      subtitle?: string | null;
    }
    export interface FloatParameterDescriptor {
      parameterType: ParameterType;
      default: number;
    }
    export interface FloatRangeDescriptor {
      min: number;
      max: number;
    }
    export type Input =
      | FileInput
      | DirectoryInput
      | TextInput
      | BatchFileInput
      | BatchTextInput
      | BatchDirectoryInput;
    export interface InputSchema {
      key: string;
      label: string;
      subtitle: string | null;
      inputType: InputType | NewFileInputType;
    }
    export type InputType =
      | 'file'
      | 'directory'
      | 'text'
      | 'textarea'
      | 'batchfile'
      | 'batchtext'
      | 'batchdirectory';
    export interface IntParameterDescriptor {
      parameterType: ParameterType;
      default: number | null;
    }
    export interface IntRangeDescriptor {
      min: number;
      max: number;
    }
    export interface MarkdownResponse {
      output_type: 'markdown';
      value: string;
      title?: string | null;
      subtitle?: string;
    }
    export interface NewFileInputType {
      /**
       * example:
       * my_file
       */
      defaultName?: string | null;
      /**
       * example:
       * .db
       */
      defaultExtension: string;
      allowedExtensions: '*' | string[];
      inputType: 'newfile';
    }
    export interface NoSchemaAPIRoute {
      /**
       * example:
       * /tasks/{name_of_task}
       */
      run_task: string;
      /**
       * example:
       * /tasks/{name_of_task}/payload_schema
       */
      payload_schema?: string;
      /**
       * example:
       * /tasks/{name_of_task}/sample_payload
       */
      sample_payload?: string;
    }
    export interface ParameterSchema {
      key: string;
      label: string;
      subtitle: string | null;
      value:
        | RangedFloatParameterDescriptor
        | FloatParameterDescriptor
        | EnumParameterDescriptor
        | TextParameterDescriptor
        | RangedIntParameterDescriptor
        | IntParameterDescriptor;
    }
    export type ParameterType =
      | 'ranged_float'
      | 'float'
      | 'enum'
      | 'text'
      | 'ranged_int'
      | 'int';
    export interface RangedFloatParameterDescriptor {
      parameterType: ParameterType;
      range: FloatRangeDescriptor;
      default: number;
    }
    export interface RangedIntParameterDescriptor {
      parameterType: ParameterType;
      range: IntRangeDescriptor;
      default: number;
    }
    export interface RequestBody {
      inputs: {
        [name: string]: Input;
      };
      parameters: {
        [key: string]: any;
      };
    }
    export type ResponseBody =
      | FileResponse
      | DirectoryResponse
      | MarkdownResponse
      | TextResponse
      | BatchFileResponse
      | BatchTextResponse
      | BatchDirectoryResponse;
    export interface SchemaAPIRoute {
      /**
       * example:
       * /tasks/{name_of_task}/task_schema
       */
      task_schema: string;
      /**
       * example:
       * /tasks/{name_of_task}
       */
      run_task: string;
      /**
       * example:
       * /tasks/{name_of_task}/payload_schema
       */
      payload_schema: string;
      /**
       * example:
       * /tasks/{name_of_task}/sample_payload
       */
      sample_payload: string;
      /**
       * example:
       * {A short title for the task}
       */
      short_title: string;
      /**
       * example:
       * 1
       */
      order: number;
    }
    export interface TaskSchema {
      inputs: InputSchema[];
      parameters: ParameterSchema[];
    }
    export interface TextInput {
      text: string;
    }
    export interface TextParameterDescriptor {
      parameterType: ParameterType;
      default: string | null;
    }
    export interface TextResponse {
      output_type: 'text';
      value: string;
      title?: string | null;
      subtitle?: string;
    }
  }
}

export type APIRoutes = Components.Schemas.APIRoutes;
export type AppMetadata = Components.Schemas.AppMetadata;
export type BatchDirectoryInput = Components.Schemas.BatchDirectoryInput;
export type BatchDirectoryResponse = Components.Schemas.BatchDirectoryResponse;
export type BatchFileInput = Components.Schemas.BatchFileInput;
export type BatchFileResponse = Components.Schemas.BatchFileResponse;
export type BatchTextInput = Components.Schemas.BatchTextInput;
export type BatchTextResponse = Components.Schemas.BatchTextResponse;
export type DirectoryInput = Components.Schemas.DirectoryInput;
export type DirectoryResponse = Components.Schemas.DirectoryResponse;
export type EnumParameterDescriptor =
  Components.Schemas.EnumParameterDescriptor;
export type FileInput = Components.Schemas.FileInput;
export type FileResponse = Components.Schemas.FileResponse;
export type FloatParameterDescriptor =
  Components.Schemas.FloatParameterDescriptor;
export type FloatRangeDescriptor = Components.Schemas.FloatRangeDescriptor;
export type Input = Components.Schemas.Input;
export type InputSchema = Components.Schemas.InputSchema;
export type InputType = Components.Schemas.InputType;
export type IntParameterDescriptor = Components.Schemas.IntParameterDescriptor;
export type IntRangeDescriptor = Components.Schemas.IntRangeDescriptor;
export type MarkdownResponse = Components.Schemas.MarkdownResponse;
export type NewFileInputType = Components.Schemas.NewFileInputType;
export type NoSchemaAPIRoute = Components.Schemas.NoSchemaAPIRoute;
export type ParameterSchema = Components.Schemas.ParameterSchema;
export type ParameterType = Components.Schemas.ParameterType;
export type RangedFloatParameterDescriptor =
  Components.Schemas.RangedFloatParameterDescriptor;
export type RangedIntParameterDescriptor =
  Components.Schemas.RangedIntParameterDescriptor;
export type RequestBody = Components.Schemas.RequestBody;
export type ResponseBody = Components.Schemas.ResponseBody;
export type SchemaAPIRoute = Components.Schemas.SchemaAPIRoute;
export type TaskSchema = Components.Schemas.TaskSchema;
export type TextInput = Components.Schemas.TextInput;
export type TextParameterDescriptor =
  Components.Schemas.TextParameterDescriptor;
export type TextResponse = Components.Schemas.TextResponse;
