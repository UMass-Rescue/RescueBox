import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'jobs';
const MIGRATION_NAME = '0005_jobs_add_task_route';

const migration0005JobsAddTaskRoute = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'taskRoute', DataTypes.STRING);
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'taskRoute');
  },
};

export default migration0005JobsAddTaskRoute;
