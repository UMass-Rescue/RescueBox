/* eslint-disable no-use-before-define */
import {
  CreationOptional,
  DataTypes,
  InferAttributes,
  InferCreationAttributes,
  Model,
  Sequelize,
} from 'sequelize';
import { SchemaAPIRoute } from 'src/shared/generated_models';
import MLModelDb from './ml-model';

/*
(taskUid,modelUid) - primary key
shortTitle
taskRoute
taskOrder
taskSchema
*/

class TaskDb extends Model<
  InferAttributes<TaskDb>,
  InferCreationAttributes<TaskDb>
> {
  declare id: CreationOptional<number>;

  declare taskId: string;

  declare modelUid: string;

  declare shortTitle: string;

  declare taskRoute: string;

  declare taskOrder: number;

  public static getAllTasks() {
    return TaskDb.findAll();
  }

  public static async getTask(taskId: string, modelUid: string) {
    return TaskDb.findOne({
      where: {
        taskId,
        modelUid,
      },
    });
  }

  public static getTaskByModelUid(modelUid: string) {
    return TaskDb.findAll({
      where: {
        modelUid,
      },
    });
  }

  public static getTaskByModelUidAndTaskId(taskId: string, modelUid: string) {
    return TaskDb.findOne({
      where: {
        taskId,
        modelUid,
      },
    });
  }

  public static createTask(
    taskId: string,
    modelUid: string,
    schemaApiRoute: SchemaAPIRoute,
  ) {
    const {
      short_title: shortTitle,
      run_task: taskRoute,
      order: taskOrder,
    } = schemaApiRoute;

    return TaskDb.create({
      taskId,
      modelUid,
      shortTitle,
      taskRoute,
      taskOrder,
    });
  }

  public static createTasks(
    taskParams: {
      uid: string;
      modelUid: string;
      schemaApiRoute: SchemaAPIRoute;
    }[],
  ) {
    return Promise.all(
      taskParams.map((tP) =>
        TaskDb.createTask(tP.uid, tP.modelUid, tP.schemaApiRoute),
      ),
    );
  }

  public static deleteTask(taskId: string, modelUid: string) {
    return TaskDb.destroy({
      where: {
        taskId,
        modelUid,
      },
    });
  }
}

export const initTask = async (connection: Sequelize) => {
  TaskDb.init(
    {
      id: {
        type: DataTypes.INTEGER,
        autoIncrement: true,
        primaryKey: true,
      },
      taskId: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      modelUid: {
        type: DataTypes.STRING,
        allowNull: false,
        references: {
          model: MLModelDb,
          key: 'uid',
        },
      },
      shortTitle: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      taskOrder: {
        type: DataTypes.INTEGER,
        allowNull: false,
      },
      taskRoute: {
        type: DataTypes.STRING,
        allowNull: false,
      },
    },
    {
      sequelize: connection,
      tableName: 'tasks',
    },
  );
};

export default TaskDb;
