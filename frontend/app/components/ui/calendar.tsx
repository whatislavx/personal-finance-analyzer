"use client";

import * as React from "react";
import { DayPicker } from "react-day-picker";

import { cn } from "./utils";

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}: React.ComponentProps<typeof DayPicker>) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn(
        "w-full rounded-xl border border-slate-700/70 bg-slate-900 p-3",
        className
      )}
      classNames={{
        months: "flex flex-col gap-3",
        month: "space-y-2",
        month_caption: "relative flex items-center justify-center pb-2 pt-1",
        caption_label: "text-sm font-semibold text-slate-100",
        nav: "absolute inset-x-0 top-1 flex items-center justify-between",
        button_previous:
          "inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-700 bg-slate-800/70 text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-700 hover:text-slate-100",
        button_next:
          "inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-700 bg-slate-800/70 text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-700 hover:text-slate-100",
        chevron: "h-4 w-4 fill-slate-300",
        month_grid: "w-full border-collapse",
        weekdays: "grid grid-cols-7",
        weekday:
          "mb-1 h-8 w-8 place-self-center text-center text-xs font-semibold uppercase tracking-wide text-slate-300",
        weeks: "space-y-1",
        week: "grid grid-cols-7",
        day: "flex items-center justify-center",
        day_button:
          "h-9 w-9 rounded-md bg-transparent p-0 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700/70 hover:text-white",
        selected:
          "bg-violet-600 text-white hover:bg-violet-500 focus:bg-violet-600",
        today:
          "border border-violet-400/80 bg-violet-500/10 text-violet-200",
        outside: "text-slate-500 opacity-60",
        disabled: "cursor-not-allowed text-slate-600 opacity-40",
        hidden: "invisible",
        ...classNames,
      }}
      {...props}
    />
  );
}

export { Calendar };
