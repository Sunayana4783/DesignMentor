import { clsx } from "clsx";

const variants = {
  default:  "bg-surface-border text-slate-300",
  success:  "bg-green-900/40 text-green-400 border border-green-800",
  warning:  "bg-yellow-900/40 text-yellow-400 border border-yellow-800",
  danger:   "bg-red-900/40 text-red-400 border border-red-800",
  brand:    "bg-brand-900/40 text-brand-400 border border-brand-800",
};

interface Props {
  children: React.ReactNode;
  variant?: keyof typeof variants;
  className?: string;
}

export default function Badge({ children, variant = "default", className }: Props) {
  return (
    <span className={clsx("inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium", variants[variant], className)}>
      {children}
    </span>
  );
}
