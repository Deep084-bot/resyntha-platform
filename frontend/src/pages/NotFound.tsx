import { FileQuestion } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4">
      <FileQuestion className="h-16 w-16 text-text-muted" />
      <h1 className="text-2xl font-semibold text-text-primary">404</h1>
      <p className="text-sm text-text-muted">
        The page you're looking for doesn't exist.
      </p>
      <Button variant="outline" asChild>
        <Link to="/">Back to Dashboard</Link>
      </Button>
    </div>
  );
}
