/* eslint-disable no-use-before-define */
import {
  CreationOptional,
  DataTypes,
  InferAttributes,
  InferCreationAttributes,
  Model,
  Sequelize,
} from 'sequelize';
import {
  RequestBody,
  ResponseBody,
  TaskSchema,
} from 'src/shared/generated_models';
import MLModelDb from './ml-model';

export enum JobStatus {
  Running = 'Running',
  Completed = 'Completed',
  Canceled = 'Canceled',
  Failed = 'Failed',
}

class JobDb extends Model<
  InferAttributes<JobDb>,
  InferCreationAttributes<JobDb>
> {
  declare uid: string;

  declare modelUid: string;

  declare startTime: Date;

  declare endTime: CreationOptional<Date>;

  declare status: JobStatus;

  declare statusText: CreationOptional<string>;

  declare request: RequestBody; // JSON string

  declare response: CreationOptional<ResponseBody>; // JSON string

  declare taskUid: string;

  declare taskSchema: TaskSchema; // JSON String

  public static getAllJobs() {
    return JobDb.findAll();
  }

  public static getJobByStatus(status: JobStatus) {
    return JobDb.findAll({
      where: {
        status,
      },
    });
  }

  public static async getJobByUid(uid: string) {
    return JobDb.findOne({
      where: {
        uid,
      },
    });
  }

  public static createJob(
    uid: string,
    modelUid: string,
    startTime: Date,
    request: RequestBody,
    taskUid: string,
    taskSchema: TaskSchema,
  ) {
    return JobDb.create({
      uid,
      modelUid,
      startTime,
      request,
      status: JobStatus.Running,
      taskUid,
      taskSchema,
    });
  }

  public static async updateJobStatus(uid: string, status: JobStatus) {
    const job = await JobDb.findByPk(uid);
    if (!job) {
      throw new Error(`Job with uid ${uid} not found`);
    }
    job.status = status;
    return job.save();
  }

  public static async updateJobStatusText(uid: string, statusText: string) {
    const job = await JobDb.findByPk(uid);
    if (!job) {
      throw new Error(`Job with uid ${uid} not found`);
    }
    job.statusText = statusText;
    return job.save();
  }

  public static async updateJobResponse(uid: string, response: ResponseBody) {
    const job = await JobDb.findByPk(uid);
    if (!job) {
      throw new Error(`Job with uid ${uid} not found`);
    }
    job.response = response;
    return job.save();
  }

  public static async updateJobEndTime(uid: string, endTime: Date) {
    const job = await JobDb.findByPk(uid);
    if (!job) {
      throw new Error(`Job with uid ${uid} not found`);
    }
    job.endTime = endTime;
    return job.save();
  }

  public static deleteJob(uid: string) {
    return JobDb.destroy({
      where: {
        uid,
      },
    });
  }
}

export const initJob = async (connection: Sequelize) => {
  JobDb.init(
    {
      uid: {
        type: DataTypes.STRING,
        allowNull: false,
        primaryKey: true,
      },
      modelUid: {
        type: DataTypes.STRING,
        allowNull: false,
        references: {
          model: MLModelDb,
          key: 'uid',
        },
      },
      startTime: {
        type: DataTypes.DATE,
        allowNull: false,
      },
      endTime: {
        type: DataTypes.DATE,
        allowNull: true,
      },
      status: {
        type: DataTypes.ENUM(...Object.values(JobStatus)),
        allowNull: false,
      },
      statusText: {
        type: DataTypes.STRING,
        allowNull: true,
      },
      request: {
        type: DataTypes.TEXT,
        allowNull: false,
        get() {
          return JSON.parse(
            // @ts-ignore
            this.getDataValue('request') as unknown as RequestBody,
          );
        },
        set(value) {
          this.setDataValue('request', JSON.stringify(value) as any);
        },
      },
      response: {
        type: DataTypes.TEXT,
        allowNull: true,
        get() {
          return JSON.parse(this.getDataValue('response') as unknown as string);
        },
        set(value) {
          // @ts-ignore
          this.setDataValue('response', JSON.stringify(value));
        },
      },
      taskUid: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      taskSchema: {
        type: DataTypes.TEXT,
        allowNull: false,
        get() {
          // @ts-ignore
          return JSON.parse(this.getDataValue('taskSchema') as TaskSchema);
        },
        set(value) {
          this.setDataValue('taskSchema', JSON.stringify(value) as any);
        },
      },
    },
    {
      sequelize: connection,
      tableName: 'jobs',
    },
  );
};

export default JobDb;
