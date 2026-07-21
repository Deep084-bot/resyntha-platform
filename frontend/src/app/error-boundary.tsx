import { Component } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface GlobalErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class GlobalErrorBoundary extends Component<
  GlobalErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: GlobalErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Global error boundary caught:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6">
          <div
            className="flex max-w-md flex-col items-center gap-4 text-center"
            role="alert"
          >
            <AlertTriangle className="h-16 w-16 text-destructive" />
            <h1 className="text-xl font-bold text-text-primary">
              Something went wrong
            </h1>
            <p className="text-sm text-text-muted">
              An unexpected error occurred. Please try reloading the page.
            </p>
            
            <Button
              variant="default"
              onClick={this.handleReload}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Reload page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
