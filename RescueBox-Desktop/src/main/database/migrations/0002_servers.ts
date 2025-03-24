import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'servers';
const MIGRATION_NAME = '0002_servers';

const migration0002Servers = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.createTable(TABLE_NAME, {
      modelUid: {
        type: DataTypes.STRING,
        allowNull: false,
        primaryKey: true,
      },
      serverAddress: {
        type: DataTypes.STRING,
        allowNull: true,
      },
      serverPort: {
        type: DataTypes.NUMBER,
        allowNull: true,
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

export default migration0002Servers;
