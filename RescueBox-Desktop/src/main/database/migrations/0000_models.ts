import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'mlmodels';
const MIGRATION_NAME = '0000_models';

const migration0000Models = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.createTable(TABLE_NAME, {
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
        allowNull: true,
      },
      lastUpdated: {
        type: DataTypes.DATE,
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

export default migration0000Models;
