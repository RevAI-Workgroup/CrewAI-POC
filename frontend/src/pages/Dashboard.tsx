
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