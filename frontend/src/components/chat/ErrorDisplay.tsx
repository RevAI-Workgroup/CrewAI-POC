import React from 'react';
import { AlertCircle, RefreshCw, X } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type ErrorType = 'network' | 'validation' | 'execution' | 'authentication' | 'general';

export interface ErrorDisplayProps {
  error: string | Error;
  type?: ErrorType;
  onRetry?: () => void;
  onDismiss?: () => void;
  retryLabel?: string;
  className?: string;
  showDismiss?: boolean;
  inline?: boolean;
}

const ERROR_STYLES: Record<ErrorType, string> = {
  network: 'border-orange-200 bg-orange-50 text-orange-800',
  validation: 'border-yellow-200 bg-yellow-50 text-yellow-800', 
  execution: 'border-red-200 bg-red-50 text-red-800',
  authentication: 'border-purple-200 bg-purple-50 text-purple-800',
  general: 'border-gray-200 bg-gray-50 text-gray-800',
};

const ERROR_ICONS: Record<ErrorType, React.ComponentType<{ className?: string }>> = {
  network: AlertCircle,
  validation: AlertCircle,
  execution: AlertCircle,
  authentication: AlertCircle,
  general: AlertCircle,
};

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  type = 'general',
  onRetry,
  onDismiss,
  retryLabel = 'Try Again',
  className,
  showDismiss = true,
  inline = false,
}) => {
  const errorMessage = error instanceof Error ? error.message : error;
  const IconComponent = ERROR_ICONS[type];
  
  if (inline) {
    return (
      <div className={cn(
        'flex items-center gap-2 text-sm p-2 rounded border',
        ERROR_STYLES[type],
        className
      )}>
        <IconComponent className="h-4 w-4 flex-shrink-0" />
        <span className="flex-1">{errorMessage}</span>
        {onRetry && (
          <Button
            size="sm"
            variant="ghost"
            onClick={onRetry}
            className="h-6 px-2 text-xs"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            {retryLabel}
          </Button>
        )}
        {showDismiss && onDismiss && (
          <Button
            size="sm"
            variant="ghost"
            onClick={onDismiss}
            className="h-6 px-1"
          >
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>
    );
  }

  return (
    <Alert className={cn(ERROR_STYLES[type], className)}>
      <IconComponent className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>{errorMessage}</span>
        <div className="flex gap-2 ml-4">
          {onRetry && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onRetry}
              className="h-8 px-3"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              {retryLabel}
            </Button>
          )}
          {showDismiss && onDismiss && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onDismiss}
              className="h-8 px-2"
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};

// Specific error components for common scenarios
export const NetworkError: React.FC<Omit<ErrorDisplayProps, 'type'>> = (props) => (
  <ErrorDisplay {...props} type="network" />
);

export const ValidationError: React.FC<Omit<ErrorDisplayProps, 'type'>> = (props) => (
  <ErrorDisplay {...props} type="validation" />
);

export const ExecutionError: React.FC<Omit<ErrorDisplayProps, 'type'>> = (props) => (
  <ErrorDisplay {...props} type="execution" />
);

export const AuthenticationError: React.FC<Omit<ErrorDisplayProps, 'type'>> = (props) => (
  <ErrorDisplay {...props} type="authentication" />
); 