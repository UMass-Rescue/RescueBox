/* eslint-disable no-use-before-define */
import {
  DataTypes,
  InferAttributes,
  InferCreationAttributes,
  Model,
  Sequelize,
} from 'sequelize';
import log from 'electron-log/main';
import MLModelDb from './ml-model';

class ModelServerDb extends Model<
  InferAttributes<ModelServerDb>,
  InferCreationAttributes<ModelServerDb>
> {
  declare serverAddress: string;

  declare serverPort: number;

  declare modelUid: string;

  declare isUserConnected: boolean;

  public static async getAllServers() {
    return ModelServerDb.findAll();
  }

  public static getServerByModelUid(modelUid: string) {
    return ModelServerDb.findOne({
      where: {
        modelUid,
      },
    });
  }

  public static async registerServer(
    modelUid: string,
    serverAddress: string,
    serverPort: number,
  ) {
    const [model, wasCreated] = await ModelServerDb.findOrCreate({
      where: {
        modelUid,
      },
      defaults: {
        modelUid,
        serverAddress,
        serverPort,
        isUserConnected: true,
      },
    });
    if (!wasCreated) {
      model.isUserConnected = true;
      await model.save();
    }
    return model;
  }

  public static async unregisterServer(modelUid: string) {
    const model = await ModelServerDb.findOne({
      where: {
        modelUid,
      },
    });
    if (!model) {
      log.warn(
        `Server for model ${modelUid} was attempted to be unregistered but not found`,
      );
      return;
    }
    model.isUserConnected = false;
    await model.save();
  }

  public static updateServer(
    modelUid: string,
    serverAddress: string,
    serverPort: number,
  ) {
    return ModelServerDb.update(
      {
        serverAddress,
        serverPort,
        isUserConnected: true,
      },
      {
        where: {
          modelUid,
        },
      },
    );
  }

  public static deleteServerByModelUid(modelUid: string) {
    return ModelServerDb.destroy({
      where: {
        modelUid,
      },
    });
  }
}

export const initModelServer = async (connection: Sequelize) => {
  ModelServerDb.init(
    {
      modelUid: {
        type: DataTypes.STRING,
        allowNull: false,
        primaryKey: true,
        references: {
          model: MLModelDb,
          key: 'uid',
        },
      },
      serverAddress: {
        type: DataTypes.STRING,
        allowNull: true,
      },
      serverPort: {
        type: DataTypes.NUMBER,
        allowNull: true,
      },
      isUserConnected: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
      },
    },
    {
      sequelize: connection,
      tableName: 'servers',
    },
  );
};

export default ModelServerDb;
