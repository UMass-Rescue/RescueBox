/* eslint-disable no-use-before-define */
import md5 from 'md5';
import {
  DataTypes,
  InferAttributes,
  InferCreationAttributes,
  Sequelize,
  Model,
  CreationOptional,
} from 'sequelize';
import { APIRoutes, AppMetadata } from 'src/shared/generated_models';

export function createModelId(
  appMetadata: AppMetadata,
  routes: APIRoutes,
): string {
  const routesString = JSON.stringify(routes) + JSON.stringify(appMetadata);
  return md5(routesString);
}

class MLModelDb extends Model<
  InferAttributes<MLModelDb>,
  InferCreationAttributes<MLModelDb>
> {
  declare uid: string;

  declare name: string;

  declare version: string;

  declare author: string;

  declare info: string;

  declare routes: APIRoutes;

  declare updatedAt: CreationOptional<Date>;

  declare isRemoved: boolean;

  public static getAllModels() {
    return MLModelDb.findAll();
  }

  public static getModelByUid(uid: string) {
    return MLModelDb.findOne({
      where: {
        uid,
      },
    });
  }

  public static getModelByModelInfoAndRoutes(
    appMetadata: AppMetadata,
    routes: APIRoutes,
  ) {
    const uid = createModelId(appMetadata, routes);
    return MLModelDb.findOne({
      where: {
        uid,
      },
    });
  }

  public static createModel(appMetadata: AppMetadata, routes: APIRoutes) {
    const uid = createModelId(appMetadata, routes);
    const { name, version, author } = appMetadata;
    return MLModelDb.create({
      uid,
      name,
      version,
      author,
      info: appMetadata.info,
      routes,
      isRemoved: false,
    });
  }

  public static createModels(
    modelData: { appMetadata: AppMetadata; routes: APIRoutes }[],
  ) {
    return Promise.all(
      modelData.map((m) => MLModelDb.createModel(m.appMetadata, m.routes)),
    );
  }

  public static deleteAllModels() {
    return MLModelDb.destroy({
      where: {},
    });
  }

  public static async removeModel(modelUid: string) {
    const model = await MLModelDb.findByPk(modelUid);
    if (!model) {
      throw new Error(`Model with uid ${modelUid} not found`);
    }
    model.isRemoved = true;
    return model.save();
  }

  public static async restoreModel(modelUid: string) {
    const model = await MLModelDb.findByPk(modelUid);
    if (!model) {
      throw new Error(`Model with uid ${modelUid} not found`);
    }
    model.isRemoved = false;
    return model.save();
  }
}
export const initMLModel = async (connection: Sequelize) => {
  MLModelDb.init(
    {
      uid: {
        type: DataTypes.STRING,
        allowNull: false,
        primaryKey: true,
      },
      name: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      version: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      author: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      info: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      routes: {
        type: DataTypes.STRING,
        allowNull: false,
        get() {
          return JSON.parse(
            // @ts-ignore
            this.getDataValue('routes') as unknown as APIRoutes,
          );
        },
        set(value) {
          // @ts-ignore
          this.setDataValue('routes', JSON.stringify(value));
        },
      },
      updatedAt: {
        type: DataTypes.DATE,
        allowNull: true,
      },
      isRemoved: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
      },
    },
    {
      sequelize: connection,
      modelName: 'mlmodels',
    },
  );
};

export default MLModelDb;
