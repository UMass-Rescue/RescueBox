import log from 'electron-log/main';
import { Sequelize } from 'sequelize';
import { SequelizeStorage, Umzug } from 'umzug';
import migration0000Models from './0000_models';
import migration0001Jobs from './0001_jobs';
import migration0002Servers from './0002_servers';
import migration0003ServersAddCol from './0003_servers_add_col';
import migration0004JobsDropOutputs from './0004_jobs_drop_outputs';
import migration0005JobsAddTaskRoute from './0005_jobs_add_task_route';
import migration0007JobsAddTaskUid from './0007_jobs_add_task_uid';
import migration0008Tasks from './0008_tasks';
import migration0006JobsAddRequest from './0006_jobs_add_request';
import migration0009ModelsReviseSchema from './0009_models_revise_schema';
import migration0010ShiftTaskSchemaFromTasksToJobs from './0010_shift_task_schema_from_tasks_to_jobs';
import migration0011ModelsAddIsRemoved from './0011_models_add_is_removed';

export default function getMigrationsUmzug(sequelize: Sequelize) {
  return new Umzug({
    storage: new SequelizeStorage({ sequelize }),
    context: sequelize.getQueryInterface(),
    migrations: [
      migration0000Models,
      migration0001Jobs,
      migration0002Servers,
      migration0003ServersAddCol,
      migration0004JobsDropOutputs,
      migration0005JobsAddTaskRoute,
      migration0006JobsAddRequest,
      migration0007JobsAddTaskUid,
      migration0008Tasks,
      migration0009ModelsReviseSchema,
      migration0010ShiftTaskSchemaFromTasksToJobs,
      migration0011ModelsAddIsRemoved,
    ],
    logger: log,
  });
}
