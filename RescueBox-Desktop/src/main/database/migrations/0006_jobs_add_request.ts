import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'jobs';
const MIGRATION_NAME = '0006_jobs_add_request';

const migration0006JobsAddRequest = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'inputs');
    await queryInterface.removeColumn(TABLE_NAME, 'parameters');
    await queryInterface.addColumn(TABLE_NAME, 'request', {
      type: DataTypes.TEXT,
      allowNull: false,
      get() {
        return JSON.parse(this.getDataValue('request') as unknown as string);
      },
      set(value) {
        // @ts-ignore
        this.setDataValue('request', JSON.stringify(value));
      },
    });
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'request');
    await queryInterface.addColumn(TABLE_NAME, 'inputs', {
      type: DataTypes.TEXT,
      allowNull: false,
      get() {
        return JSON.parse(this.getDataValue('inputs') as unknown as string);
      },
      set(value) {
        // @ts-ignore
        this.setDataValue('inputs', JSON.stringify(value));
      },
    });
    await queryInterface.addColumn(TABLE_NAME, 'parameters', {
      type: DataTypes.TEXT,
      allowNull: false,
      get() {
        return JSON.parse(this.getDataValue('parameters') as unknown as string);
      },
      set(value) {
        // @ts-ignore
        this.setDataValue('parameters', JSON.stringify(value));
      },
    });
  },
};

export default migration0006JobsAddRequest;
