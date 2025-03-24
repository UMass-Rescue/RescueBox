import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'jobs';
const MIGRATION_NAME = '0007_jobs_add_task_uid';

const migration0007JobsAddTaskUid = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'taskRoute');
    await queryInterface.addColumn(TABLE_NAME, 'taskUid', DataTypes.STRING);
    await queryInterface.changeColumn(TABLE_NAME, 'taskUid', {
      type: DataTypes.STRING,
      allowNull: false,
    });
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'taskRoute', DataTypes.STRING);
    await queryInterface.removeColumn(TABLE_NAME, 'taskUid');
  },
};

export default migration0007JobsAddTaskUid;
