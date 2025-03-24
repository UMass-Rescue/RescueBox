import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'servers';
const MIGRATION_NAME = '0003_servers_add_col';

const migration0003ServersAddCol = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(
      TABLE_NAME,
      'isUserConnected',
      DataTypes.BOOLEAN,
    );
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'isUserConnected');
  },
};

export default migration0003ServersAddCol;
