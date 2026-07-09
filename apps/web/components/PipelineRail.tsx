"use client";

import { PIPELINE_STAGES, type PipelineStage } from "@lvpp/shared";

/** The studio's signature: a film-strip stage rail. The current stage glows
 *  like a tally light; completed stages are exposed frames. */
export function PipelineRail({
  status,
  onSelect,
  compact = false,
}: {
  status: PipelineStage;
  onSelect?: (stage: PipelineStage) => void;
  compact?: boolean;
}) {
  const currentIndex = PIPELINE_STAGES.indexOf(status);
  return (
    <ol
      className={`flex items-center ${compact ? "gap-[3px]" : "gap-1"}`}
      aria-label={`Pipeline stage: ${status}`}
    >
      {PIPELINE_STAGES.map((stage, i) => {
        const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "todo";
        const frame = (
          <span
            title={stage}
            className={`block rounded-[2px] transition-all ${
              compact ? "h-2 w-3" : "h-3 w-5"
            } ${
              state === "done"
                ? "bg-accent/45"
                : state === "current"
                  ? "bg-accent shadow-[0_0_10px_var(--color-accent)]"
                  : "border border-edge bg-surface-2/40"
            }`}
          />
        );
        return (
          <li key={stage} className="flex flex-col items-center gap-1">
            {onSelect ? (
              <button
                onClick={() => onSelect(stage)}
                aria-label={`Set stage to ${stage}`}
                className="rounded focus-visible:outline-2 focus-visible:outline-accent"
              >
                {frame}
              </button>
            ) : (
              frame
            )}
            {!compact && (
              <span
                className={`font-mono text-[9px] leading-none ${
                  state === "current" ? "text-accent" : "text-muted/60"
                }`}
              >
                {stage.slice(0, 4)}
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
