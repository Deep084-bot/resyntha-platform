import { cn } from "@/lib/utils";

export interface PageTitleProps {
  children: React.ReactNode;
  className?: string;
  as?: "h1" | "h2" | "h3";
}

export function PageTitle({ children, className, as: Tag = "h1" }: PageTitleProps) {
  return (
    <Tag className={cn("text-xl font-semibold text-text-primary", className)}>
      {children}
    </Tag>
  );
}
