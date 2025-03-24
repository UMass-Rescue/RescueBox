import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'tasks';
const MIGRATION_NAME = '0008_tasks';

const migration0008Tasks = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.createTable(TABLE_NAME, {
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
      },
      shortTitle: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      taskRoute: {
        type: DataTypes.STRING,
        allowNull: false,
      },
      taskOrder: {
        type: DataTypes.NUMBER,
        allowNull: false,
      },
      taskSchema: {
        type: DataTypes.TEXT,
        allowNull: false,
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

export default migration0008Tasks;
