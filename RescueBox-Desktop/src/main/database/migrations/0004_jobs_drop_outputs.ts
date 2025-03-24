import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'jobs';
const MIGRATION_NAME = '0004_jobs_drop_outputs';

const migration0004JobsDropOutputs = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'outputs');
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'outputs', {
      type: DataTypes.TEXT,
      allowNull: false,
      get() {
        return JSON.parse(this.getDataValue('outputs') as unknown as string);
      },
      set(value) {
        // @ts-ignore
        this.setDataValue('outputs', JSON.stringify(value));
      },
    });
  },
};

export default migration0004JobsDropOutputs;
