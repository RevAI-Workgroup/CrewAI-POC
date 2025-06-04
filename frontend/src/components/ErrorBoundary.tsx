import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';

export function ErrorBoundary() {
  const error = useRouteError();

  // Handle known route errors (like 404, 500, etc.)
  if (isRouteErrorResponse(error)) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <AlertTriangle className="h-12 w-12 text-destructive" />
            </div>
            <CardTitle className="text-2xl">
              {error.status === 404 ? 'Page Not Found' : 'Something Went Wrong'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-muted-foreground">
              {error.status === 404
                ? "The page you're looking for doesn't exist."
                : error.statusText || 'An unexpected error occurred.'}
            </p>
            
            {error.status === 404 && (
              <p className="text-sm text-muted-foreground">
                The graph you're trying to access may have been deleted or you may not have permission to view it.
              </p>
            )}

            <div className="flex flex-col sm:flex-row gap-2 justify-center">
              <Button asChild variant="default">
                <Link to="/">
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </Link>
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Handle unexpected JavaScript errors
  const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
  
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <AlertTriangle className="h-12 w-12 text-destructive" />
          </div>
          <CardTitle className="text-2xl">Application Error</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-muted-foreground">
            Something unexpected happened. Please try refreshing the page.
          </p>
          
          {process.env.NODE_ENV === 'development' && (
            <details className="text-left">
              <summary className="text-sm font-medium cursor-pointer">
                Error Details (Development)
              </summary>
              <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto">
                {errorMessage}
              </pre>
            </details>
          )}

          <div className="flex flex-col sm:flex-row gap-2 justify-center">
            <Button asChild variant="default">
              <Link to="/">
                <Home className="h-4 w-4 mr-2" />
                Go Home
              </Link>
            </Button>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Page
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 