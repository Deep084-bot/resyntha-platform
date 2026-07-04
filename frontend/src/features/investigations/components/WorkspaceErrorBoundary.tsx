import { Component } from "react";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface WorkspaceErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class WorkspaceErrorBoundary extends Component<
  WorkspaceErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: WorkspaceErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          className="flex h-full flex-col items-center justify-center gap-4 p-6"
          role="alert"
        >
          <AlertTriangle className="h-12 w-12 text-destructive" />
          <p className="text-lg font-medium text-text-primary">
            Something went wrong
          </p>
          <p className="max-w-md text-center text-sm text-text-muted">
            {this.state.error?.message ??
              "An unexpected error occurred in this workspace."}
          </p>
          <Button variant="outline" onClick={this.handleRetry}>
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
