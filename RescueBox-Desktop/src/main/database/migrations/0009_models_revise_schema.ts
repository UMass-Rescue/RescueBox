import { QueryInterface, DataTypes } from 'sequelize';

const TABLE_NAME = 'mlmodels';
const MIGRATION_NAME = '0009_models_revise_schema';

const migration0009ModelsReviseSchema = {
  name: MIGRATION_NAME,
  async up({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.removeColumn(TABLE_NAME, 'lastUpdated');
    await queryInterface.changeColumn(TABLE_NAME, 'author', {
      type: DataTypes.STRING,
      allowNull: false,
    });
    // routes
    await queryInterface.addColumn(TABLE_NAME, 'routes', {
      type: DataTypes.STRING,
      allowNull: true,
    });
    await queryInterface.changeColumn(TABLE_NAME, 'routes', {
      type: DataTypes.STRING,
      allowNull: false,
    });
    // info
    await queryInterface.addColumn(TABLE_NAME, 'info', {
      type: DataTypes.STRING,
      allowNull: true,
    });
    await queryInterface.changeColumn(TABLE_NAME, 'info', {
      type: DataTypes.STRING,
      allowNull: false,
    });
  },
  async down({ context: queryInterface }: { context: QueryInterface }) {
    await queryInterface.addColumn(TABLE_NAME, 'lastUpdated', {
      type: DataTypes.DATE,
      allowNull: false,
    });
    await queryInterface.changeColumn(TABLE_NAME, 'author', {
      type: DataTypes.STRING,
      allowNull: true,
    });
    // routes
    await queryInterface.removeColumn(TABLE_NAME, 'routes');
    // info
    await queryInterface.removeColumn(TABLE_NAME, 'info');
  },
};

export default migration0009ModelsReviseSchema;
