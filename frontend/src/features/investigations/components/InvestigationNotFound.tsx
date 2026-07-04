import { Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";

export function InvestigationNotFound() {
  return (
    <div
      className="flex h-full flex-col items-center justify-center gap-4 p-6"
      role="alert"
    >
      <FileQuestion className="h-12 w-12 text-text-muted" />
      <p className="text-lg font-medium text-text-primary">
        Investigation not found
      </p>
      <p className="text-sm text-text-muted">
        The investigation you&apos;re looking for doesn&apos;t exist or has
        been deleted.
      </p>
      <Link
        to="/"
        className="text-sm text-accent-default transition-colors hover:underline"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
