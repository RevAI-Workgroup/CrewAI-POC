
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