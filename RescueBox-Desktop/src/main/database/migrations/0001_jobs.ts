import { QueryInterface, DataTypes } from 'sequelize';
import { JobStatus } from 'src/main/models/job';

const TABLE_NAME = 'jobs';
const MIGRATION_NAME = '0001_jobs';

const migration0001Jobs = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.createTable(TABLE_NAME, {
      uid: {
        type: DataTypes.STRING,
        allowNull: false,
        primaryKey: true,
      },
      modelUid: {
        type: DataTypes.STRING,
        allowNull: false,
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
      inputs: {
        type: DataTypes.TEXT,
        allowNull: false,
        get() {
          return JSON.parse(this.getDataValue('inputs') as unknown as string);
        },
        set(value) {
          this.setDataValue('inputs', JSON.stringify(value) as any);
        },
      },
      outputs: {
        type: DataTypes.TEXT,
        allowNull: false,
        get() {
          return JSON.parse(this.getDataValue('outputs') as unknown as string);
        },
        set(value) {
          // @ts-ignore
          this.setDataValue('outputs', JSON.stringify(value));
        },
      },
      parameters: {
        type: DataTypes.TEXT,
        allowNull: false,
        get() {
          return JSON.parse(
            this.getDataValue('parameters') as unknown as string,
          );
        },
        set(value) {
          // @ts-ignore
          this.setDataValue('parameters', JSON.stringify(value));
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
      createdAt: {
        type: DataTypes.DATE,
      },
      updatedAt: {
        type: DataTypes.DATE,
      },
    });
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.dropTable(TABLE_NAME);
  },
};

export default migration0001Jobs;
