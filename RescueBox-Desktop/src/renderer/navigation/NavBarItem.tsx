import { NavLink } from 'react-router-dom';
import React, { ReactNode } from 'react';
import { cn } from '../lib/utils';

export function RegularTitleNavBar({
  path,
  name,
}: {
  path: string;
  name: string;
}) {
  return (
    <span key={path} className="relative sm:text-lg lg:text-xl font-bold">
      <span className="absolute hidden group-[.is-active]:block -bottom-2 sm:-bottom-2 lg:-bottom-3 inset-x-0 bg-blue-500 h-0.5 rounded-full transition-opacity duration-150" />
      {name}
    </span>
  );
}

export function ImageTitleNavBar({
  children,
  path,
}: {
  children: ReactNode;
  path: string;
}) {
  return (
    <span key={path} className="relative sm:text-lg lg:text-xl font-bold">
      <span className="absolute hidden group-[.is-active]:block -bottom-2 inset-x-0 bg-blue-500 h-0.5 rounded-full transition-opacity duration-150" />
      {children}
    </span>
  );
}

interface NavBarItemProps {
  path: string;
  // eslint-disable-next-line react/require-default-props
  children?: ReactNode; // Special prop to allow nested children
}

// eslint-disable-next-line react/function-component-definition
export const NavBarItem: React.FC<NavBarItemProps> = ({
  path,
  children = undefined,
}) => {
  return (
    <NavLink
      key={path}
      to={path}
      className={({ isActive }) =>
        cn(
          'group px-4 py-2 text-center hover:bg-slate-200 rounded-md flex items-center justify-center transition-all',
          isActive ? 'is-active text-blue-500 hover:text-blue-400' : '',
        )
      }
    >
      {children}
    </NavLink>
  );
};
