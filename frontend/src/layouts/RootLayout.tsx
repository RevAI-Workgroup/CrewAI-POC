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

export function AppLayout() {
  return (
    <div className='min-h-screen bg-background'>
      {/* TODO: Add Header and Sidebar components when implemented */}
      <div className='flex'>
        {/* Sidebar placeholder */}
        <div className='w-64 bg-muted/10 min-h-screen'>
          <div className='p-4'>
            <h2 className='text-lg font-semibold'>CrewAI Builder</h2>
          </div>
        </div>

        {/* Main content */}
        <main className='flex-1 p-6'>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
