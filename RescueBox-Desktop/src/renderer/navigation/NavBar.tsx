import { NavBarItem, RegularTitleNavBar } from './NavBarItem';

const navBarPaths = {
  '/models': 'Models',
  '/jobs': 'Jobs',
};

function NavBar() {
  return (
    <div className="ml-2 flex flex-row space-x-4">
      {Object.entries(navBarPaths).map(([path, name]) => (
        <div key={path} className="">
          <NavBarItem path={path}>
            <RegularTitleNavBar path={path} name={name} />
          </NavBarItem>
        </div>
      ))}
    </div>
  );
}

export default NavBar;
