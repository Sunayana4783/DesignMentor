"use client";
import { MASTERY_COLORS, MASTERY_LABELS } from "@/types";

interface Props {
  score: number;
  level: string;
  showLabel?: boolean;
  height?: string;
}

export default function MasteryBar({ score, level, showLabel = true, height = "h-2" }: Props) {
  const color = MASTERY_COLORS[level] ?? "#475569";
  const label = MASTERY_LABELS[level] ?? level;

  return (
    <div className="w-full space-y-1">
      {showLabel && (
        <div className="flex justify-between text-xs text-slate-400">
          <span>{label}</span>
          <span>{score.toFixed(0)}%</span>
        </div>
      )}
      <div className={`w-full bg-surface-border rounded-full ${height} overflow-hidden`}>
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${Math.min(score, 100)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
