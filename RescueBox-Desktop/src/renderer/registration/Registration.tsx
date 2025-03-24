import { Outlet } from 'react-router-dom';
import RegistrationTable from './RegistrationTable';

function Registration() {
  return (
    <div className="flex flex-col items-center m-3">
      <RegistrationTable />
      <Outlet />
    </div>
  );
}

export default Registration;
