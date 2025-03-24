import { TaskSchema } from '../generated_models';
import taskSchema1 from './task_schema1';
import taskSchema2 from './task_schema2';
import taskSchema3 from './task_schema3';
import taskSchema4 from './task_schema4';

const taskSchemas: TaskSchema[] = [
  taskSchema1,
  taskSchema2,
  taskSchema3,
  taskSchema4,
] satisfies TaskSchema[];

export default taskSchemas;
