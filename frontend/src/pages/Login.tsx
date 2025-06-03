export function LoginPage() {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Welcome Back</h1>
        <p className="text-muted-foreground mt-2">
          Enter your passphrase to continue
        </p>
      </div>
      
      {/* TODO: Replace with actual login form component */}
      <div className="border rounded-lg p-6">
        <p className="text-center text-muted-foreground">
          Login form will be implemented in Task 2-9
        </p>
      </div>
    </div>
  );
}

export function RegisterPage() {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Get Started</h1>
        <p className="text-muted-foreground mt-2">
          Create your account with a pseudo name
        </p>
      </div>
      
      {/* TODO: Replace with actual register form component */}
      <div className="border rounded-lg p-6">
        <p className="text-center text-muted-foreground">
          Registration form will be implemented in Task 2-8
        </p>
      </div>
    </div>
  );
}

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="border rounded-lg p-6">
          <h3 className="font-semibold mb-2">Recent Graphs</h3>
          <p className="text-muted-foreground">
            Your latest CrewAI graphs will appear here
          </p>
        </div>
        <div className="border rounded-lg p-6">
          <h3 className="font-semibold mb-2">Quick Actions</h3>
          <p className="text-muted-foreground">
            Create new graphs and manage existing ones
          </p>
        </div>
      </div>
    </div>
  );
}

export function GraphsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">My Graphs</h1>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md">
          New Graph
        </button>
      </div>
      <div className="border rounded-lg p-6">
        <p className="text-center text-muted-foreground">
          Graph list and management will be implemented in Tasks 2-20 to 2-24
        </p>
      </div>
    </div>
  );
} 