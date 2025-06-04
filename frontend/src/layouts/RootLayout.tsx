import { Outlet } from 'react-router-dom';

export function RootLayout() {
  return (
    <div className='min-h-screen bg-background'>
      <Outlet />
    </div>
  );
}

export function AuthLayout() {
  return (
    <div className='min-h-screen flex items-center justify-center bg-background'>
      <div className='w-full max-w-md space-y-6'>
        <Outlet />
      </div>
    </div>
  );
}
