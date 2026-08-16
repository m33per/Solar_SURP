"""
UI for exploring the Solar_SURP analysis results.

This file only builds a UI on top of the analysis logic that already lives
under Data_Analysis/ -- it does not reimplement or modify that logic. It
imports the following modules and calls their functions directly:
    Data_Analysis/EnergyComparisons/FindGoodDaysByIrradiance.py
                                        -> findSunsetTimeIndex, getGoodDays
    Data_Analysis/MathingIt/AnalyzeDropSlopes.py           -> getResults
    Data_Analysis/MathingIt/AnalyzeConcavity.py            -> getResults
    Data_Analysis/EnergyComparisons/VisualizeEnergies.py   -> makeGraph
    Data_Analysis/VisualizeIrradiance/IrradianceOneMonth.py -> showGraph
    Data_Analysis/VisualizeActivePowers/OneInverterOverTime.py -> showGraph
    Data_Analysis/VisualizeActivePowers/OneDayMultInverters.py -> makeGraph
    Data_Analysis/MathingIt/FindDropSlopes.py              -> generateCSV
    Data_Analysis/MathingIt/FindConcavity.py               -> generateCSV
    Data_Analysis/EnergyComparisons/CompareEnergy.py       -> makeFile

Some other scripts in Data_Analysis/ write/overwrite CSV files as a side
effect of merely being imported (e.g. the MakeAvgAPCSV.py files). Those are
intentionally NOT wired into this UI yet -- importing them here would
trigger those side effects on every app launch.
"""

import os
import sys
import json
import datetime
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.json"

# The analysis scripts use paths written relative to the project root
# (e.g. "Data\\ActivePower\\..."), so make sure that's the working directory
# no matter where main.py is launched from.
os.chdir(PROJECT_ROOT)

for rel_dir in (
    "Data_Analysis/EnergyComparisons",
    "Data_Analysis/MathingIt",
    "Data_Analysis/VisualizeIrradiance",
    "Data_Analysis/VisualizeActivePowers",
):
    full = str(PROJECT_ROOT / rel_dir)
    if full not in sys.path:
        sys.path.insert(0, full)

class _ThreadLocalStdout:
    """Installed once as sys.stdout so a background thread can capture its
    own print() output (from generateCSV()'s progress prints) without
    hijacking stdout for the whole process. contextlib.redirect_stdout
    swaps sys.stdout globally, which would swallow the main thread's (or
    any other thread's) output for as long as the background thread's
    capture is active -- this instead routes each thread's writes to
    whichever buffer that thread registered, falling back to the real
    stdout for everyone else."""

    def __init__(self, real_stdout):
        self._real_stdout = real_stdout
        self._local = threading.local()

    def set_buffer(self, buffer):
        self._local.buffer = buffer

    def _target(self):
        return getattr(self._local, "buffer", None) or self._real_stdout

    def write(self, text):
        return self._target().write(text)

    def flush(self):
        return self._target().flush()


sys.stdout = _ThreadLocalStdout(sys.stdout)

IMPORT_ERRORS = {}


def _try_import(module_name):
    try:
        return __import__(module_name)
    except Exception as exc:  # missing file, bad CSV path, etc.
        IMPORT_ERRORS[module_name] = str(exc)
        return None


FindGoodDaysByIrradiance = _try_import("FindGoodDaysByIrradiance")
AnalyzeDropSlopes = _try_import("AnalyzeDropSlopes")
AnalyzeConcavity = _try_import("AnalyzeConcavity")
VisualizeEnergies = _try_import("VisualizeEnergies")
IrradianceOneMonth = _try_import("IrradianceOneMonth")
OneInverterOverTime = _try_import("OneInverterOverTime")
OneDayMultInverters = _try_import("OneDayMultInverters")
FindDropSlopes = _try_import("FindDropSlopes")
FindConcavity = _try_import("FindConcavity")
CompareEnergy = _try_import("CompareEnergy")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)


def ensure_sunrise_key():
    """sunriseTimes isn't produced/consumed by any analysis script yet -- it's
    a placeholder column for future use, added the same way sunsetTimes
    already is (empty string per month)."""
    cfg = load_config()
    if "sunriseTimes" not in cfg:
        cfg["sunriseTimes"] = {month: "" for month in cfg["days"].keys()}
        save_config(cfg)


ensure_sunrise_key()

MONTHS = list(load_config()["days"].keys())


def parse_month_year(month_year):
    """'July2025' -> (2025, 7)"""
    dt = datetime.datetime.strptime(month_year, "%B%Y")
    return dt.year, dt.month


def parse_day_range(text):
    """'1-5, 7-10, 12' -> [1, 2, 3, 4, 5, 7, 8, 9, 10, 12]"""
    days = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str.strip()), int(end_str.strip())
            if start > end:
                raise ValueError(f"'{part}' has a start greater than its end.")
            days.update(range(start, end + 1))
        else:
            days.add(int(part))
    if not days:
        raise ValueError("No days given.")
    return sorted(days)


def resolve_day_input(day_text, month):
    """Parse a typed day-of-month (e.g. "15") into the "YYYY-MM-DD" format
    the Slopes/Concavities/SunsetEnergies CSVs use as column prefixes --
    shared by every section that lets the user type a bare day-of-month
    instead of picking from the configured good days (it doesn't have to be
    one of them). Shows its own warning and returns None on invalid input."""
    day_text = day_text.strip()
    if not day_text:
        messagebox.showwarning("Missing day", "Enter a day of the month.")
        return None
    try:
        day_num = int(day_text)
    except ValueError:
        messagebox.showwarning("Invalid day", f"'{day_text}' is not a valid integer day.")
        return None
    year, month_num = parse_month_year(month)
    try:
        return datetime.date(year, month_num, day_num).isoformat()
    except ValueError:
        messagebox.showwarning("Invalid day", f"{month} has no day {day_num}.")
        return None


def good_days_summary(cfg, month):
    """'["2025-07-01", "2025-07-10"]' -> '1, 10' for a reference label next
    to a typed-day-of-month field."""
    good_days = cfg["days"].get(month, [])
    day_nums = sorted({int(d.split("-")[2]) for d in good_days})
    return ", ".join(str(n) for n in day_nums) if day_nums else "(none configured)"


def make_output_pane(parent, width=28):
    frame = ttk.Frame(parent)
    text = tk.Text(frame, height=14, width=width, wrap="word", state="disabled")
    scrollbar = ttk.Scrollbar(frame, command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, text


def show_output_popup(parent, title, text):
    """Show a scrollable read-only popup for print() output (e.g. progress
    from a slow analysis call) -- too long to fit in a plain messagebox.
    Returns (win, text_widget) so a caller doing slow work in a background
    thread can open this immediately with a placeholder and stream the real
    output into it live via a _LivePopupWriter -- calling this with the
    final text only *after* more synchronous work on the main thread isn't
    enough to make it appear promptly: a single win.update() only pumps
    Tk's queue at that instant, and Windows won't keep painting a
    just-created window while the process is then busy for a while outside
    the Tk event loop. Running the slow work in a thread instead keeps the
    mainloop free the whole time, which is what actually fixes that."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("560x420")
    pane, text_widget = make_output_pane(win)
    pane.pack(fill="both", expand=True, padx=8, pady=8)
    text_widget.configure(state="normal")
    text_widget.insert("1.0", text if text.strip() else "(no output)")
    text_widget.configure(state="disabled")
    ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 8))
    win.update()
    return win, text_widget


class _LivePopupWriter:
    """File-like object that streams print() output into an output popup's
    Text widget live, as each write happens -- rather than buffering
    everything and only showing it once the background work finishes. Each
    write is marshaled onto the UI thread via owner.after(0, ...) since this
    is written to from a background thread and Tkinter widgets aren't safe
    to touch from anywhere else. The popup's placeholder text is cleared on
    the first write; if the popup was already closed, writes are silently
    dropped (TclError) instead of erroring out the background thread."""

    def __init__(self, owner, text_widget):
        self._owner = owner
        self._text_widget = text_widget
        self._started = False

    def write(self, text):
        if text:
            self._owner.after(0, self._append, text)
        return len(text)

    def flush(self):
        pass

    def _append(self, text):
        try:
            self._text_widget.configure(state="normal")
            if not self._started:
                self._started = True
                self._text_widget.delete("1.0", "end")
            self._text_widget.insert("end", text)
            self._text_widget.see("end")
            self._text_widget.configure(state="disabled")
        except tk.TclError:
            pass  # popup was closed before this write arrived


def set_output(text_widget, content):
    text_widget.configure(state="normal")
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", content)
    text_widget.configure(state="disabled")


def close_stray_graph_windows():
    """Discard any Matplotlib figure left over from a failed graph attempt
    (e.g. an invalid day), so it doesn't reappear blank the next time a
    graph is shown successfully -- plt.show() displays every open figure,
    not just the newest one."""
    plt.close("all")


def call_with_temp_config_value(top_key, month, temp_value, func, *args):
    """Call func(*args) with config.json's [top_key][month] temporarily set
    to temp_value, restoring the original value afterward (even if func
    raises). Needed because AnalyzeDropSlopes.getResults()/
    AnalyzeConcavity.getResults() re-read config.json internally on every
    call rather than taking a cutoff as a parameter, and a UI-entered
    override must never be persisted to the file."""
    cfg = load_config()
    original = cfg[top_key][month]
    cfg[top_key][month] = temp_value
    save_config(cfg)
    try:
        return func(*args)
    finally:
        cfg2 = load_config()
        cfg2[top_key][month] = original
        save_config(cfg2)


def unavailable_notice(parent, module_name):
    ttk.Label(
        parent,
        text=(
            f"This tab is unavailable: '{module_name}' failed to import.\n"
            f"{IMPORT_ERRORS.get(module_name, '')}"
        ),
        foreground="#a33",
        wraplength=500,
        justify="left",
    ).pack(padx=10, pady=10, anchor="w")


class FlagsTab(ttk.Frame):
    """Drop-slope / concavity outlier flags, each in their own output box.

    Once both analyses have been run for the same month/day, a "Compare
    Analyses" button appears to show which flagged inverters overlap.
    """

    def __init__(self, parent):
        super().__init__(parent, padding=10)

        form = ttk.Frame(self)
        form.pack(fill="x")

        ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.month_var = tk.StringVar(value=MONTHS[0])
        month_box = ttk.Combobox(form, textvariable=self.month_var, values=MONTHS, state="readonly", width=15)
        month_box.grid(row=0, column=1, padx=4, pady=4)
        month_box.bind("<<ComboboxSelected>>", lambda e: self._on_month_change())

        ttk.Label(form, text="Day").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.day_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.day_var, width=6).grid(row=0, column=3, sticky="w", padx=4, pady=4)

        self.good_days_var = tk.StringVar()
        ttk.Label(form, text="Good days:").grid(row=0, column=4, sticky="w", padx=(12, 4), pady=4)
        ttk.Label(form, textvariable=self.good_days_var, foreground="#666", wraplength=260).grid(
            row=0, column=5, sticky="w", padx=4, pady=4
        )

        ttk.Label(form, text="Slope Cutoff").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.slope_cutoff_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.slope_cutoff_var, width=15).grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(form, text="Concavity Cutoff").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        self.concavity_cutoff_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.concavity_cutoff_var, width=15).grid(row=1, column=3, padx=4, pady=4)

        ttk.Label(
            self,
            text="Cutoffs auto-fill from Config Editor but are editable here for this run only -- they are never saved back to config.json.",
            foreground="#666",
            wraplength=650,
            justify="left",
        ).pack(anchor="w", pady=(0, 4))

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Drop Slope Outliers (needs day)", command=self._run_slopes).pack(side="left", padx=4)
        ttk.Button(btns, text="Concavity Outliers (needs day)", command=self._run_concavity).pack(side="left", padx=4)

        outputs_row = ttk.Frame(self)
        outputs_row.pack(fill="both", expand=True, pady=6)

        slope_frame = ttk.LabelFrame(outputs_row, text="Slope Results")
        slope_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))
        slope_pane, self.slope_output = make_output_pane(slope_frame)
        slope_pane.pack(fill="both", expand=True, padx=4, pady=4)

        concavity_frame = ttk.LabelFrame(outputs_row, text="Concavity Results")
        concavity_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))
        concavity_pane, self.concavity_output = make_output_pane(concavity_frame)
        concavity_pane.pack(fill="both", expand=True, padx=4, pady=4)

        self._last_slope = None  # (month, day, {inverter keys}) after a successful run
        self._last_concavity = None

        # Created here but not packed until _sync_compare_button decides
        # both analyses match on month/day.
        self.compare_button = ttk.Button(self, text="Compare Analyses", command=self._run_compare)

        self.compare_frame = ttk.LabelFrame(self, text="Comparison")
        compare_cols = ttk.Frame(self.compare_frame)
        compare_cols.pack(fill="both", expand=True, padx=4, pady=4)

        both_col = ttk.Frame(compare_cols)
        both_col.pack(side="left", fill="both", expand=True, padx=(0, 4))
        ttk.Label(both_col, text="Both").pack(anchor="w")
        both_pane, self.both_output = make_output_pane(both_col)
        both_pane.pack(fill="both", expand=True)

        slope_only_col = ttk.Frame(compare_cols)
        slope_only_col.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Label(slope_only_col, text="Slope Only").pack(anchor="w")
        slope_only_pane, self.slope_only_output = make_output_pane(slope_only_col)
        slope_only_pane.pack(fill="both", expand=True)

        concavity_only_col = ttk.Frame(compare_cols)
        concavity_only_col.pack(side="left", fill="both", expand=True, padx=(4, 0))
        ttk.Label(concavity_only_col, text="Concavity Only").pack(anchor="w")
        concavity_only_pane, self.concavity_only_output = make_output_pane(concavity_only_col)
        concavity_only_pane.pack(fill="both", expand=True)

        self._on_month_change()

    def _on_month_change(self):
        cfg = load_config()
        month = self.month_var.get()
        self.good_days_var.set(good_days_summary(cfg, month))
        self.slope_cutoff_var.set(cfg["slopeCutOffs"].get(month, 0))
        self.concavity_cutoff_var.set(cfg["d2CutOffs"].get(month, 0))

    @staticmethod
    def _inverter_key(result_line):
        """'Inverter 46 -3.78 OUTLIER' -> 'Inverter 46'"""
        return " ".join(result_line.split()[:2])

    def _run_slopes(self):
        if AnalyzeDropSlopes is None:
            messagebox.showerror("Unavailable", f"AnalyzeDropSlopes failed to import:\n{IMPORT_ERRORS.get('AnalyzeDropSlopes')}")
            return
        month = self.month_var.get()
        day = resolve_day_input(self.day_var.get(), month)
        if day is None:
            return
        try:
            slope_cutoff = float(self.slope_cutoff_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Slope Cutoff must be a number.")
            return
        try:
            results = call_with_temp_config_value(
                "slopeCutOffs", month, slope_cutoff, AnalyzeDropSlopes.getResults, month, day
            )
        except FileNotFoundError:
            messagebox.showerror("Data not found", f"No Slopes CSV found for {month}.")
            return
        except KeyError as exc:
            messagebox.showerror("Missing data", f"Missing expected column/config value: {exc}")
            return
        set_output(self.slope_output, "\n".join(results) if results else "No outliers found.")
        self._last_slope = (month, day, {self._inverter_key(r) for r in results})
        self._sync_compare_button()

    def _run_concavity(self):
        if AnalyzeConcavity is None:
            messagebox.showerror("Unavailable", f"AnalyzeConcavity failed to import:\n{IMPORT_ERRORS.get('AnalyzeConcavity')}")
            return
        month = self.month_var.get()
        day = resolve_day_input(self.day_var.get(), month)
        if day is None:
            return
        try:
            concavity_cutoff = float(self.concavity_cutoff_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Concavity Cutoff must be a number.")
            return
        try:
            results = call_with_temp_config_value(
                "d2CutOffs", month, concavity_cutoff, AnalyzeConcavity.getResults, month, day
            )
        except FileNotFoundError:
            messagebox.showerror("Data not found", f"No Concavities CSV found for {month}.")
            return
        except KeyError as exc:
            messagebox.showerror("Missing data", f"Missing expected column/config value: {exc}")
            return
        set_output(self.concavity_output, "\n".join(results) if results else "No outliers found.")
        self._last_concavity = (month, day, {self._inverter_key(r) for r in results})
        self._sync_compare_button()

    def _sync_compare_button(self):
        same_selection = (
            self._last_slope is not None
            and self._last_concavity is not None
            and self._last_slope[:2] == self._last_concavity[:2]
        )
        if same_selection:
            self.compare_button.pack(anchor="w", pady=(0, 6))
        else:
            self.compare_button.pack_forget()
            self.compare_frame.pack_forget()

    def _run_compare(self):
        _, _, slope_set = self._last_slope
        _, _, concavity_set = self._last_concavity

        both = sorted(slope_set & concavity_set)
        slope_only = sorted(slope_set - concavity_set)
        concavity_only = sorted(concavity_set - slope_set)

        set_output(self.both_output, "\n".join(both))
        set_output(self.slope_only_output, "\n".join(slope_only))
        set_output(self.concavity_only_output, "\n".join(concavity_only))

        self.compare_frame.pack(fill="both", expand=True, pady=(0, 6))


class MonthlyGraphsTab(ttk.Frame):
    """Whole-month line graphs (one line per day) for irradiance and for a
    single inverter's active power, plus the sunset energy comparison graph
    and the energy calculator underneath them."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)

        # Four stacked sections no longer fit in the window at once, so the
        # whole tab scrolls vertically -- everything below is built inside
        # `content` rather than directly on `self`.
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content = ttk.Frame(canvas)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(content_window, width=e.width))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        irr_frame = ttk.LabelFrame(content, text="Irradiance (whole month)")
        irr_frame.pack(fill="x", pady=(0, 10))
        if IrradianceOneMonth is None:
            unavailable_notice(irr_frame, "IrradianceOneMonth")
        else:
            row = ttk.Frame(irr_frame, padding=8)
            row.pack(fill="x")
            ttk.Label(row, text="Month").pack(side="left", padx=(0, 4))
            self.irr_month_var = tk.StringVar(value=MONTHS[0])
            ttk.Combobox(
                row, textvariable=self.irr_month_var, values=MONTHS, state="readonly", width=15
            ).pack(side="left", padx=4)

            days_row = ttk.Frame(irr_frame, padding=(8, 0, 8, 8))
            days_row.pack(fill="x")
            ttk.Label(days_row, text="Days").pack(side="left", padx=(0, 4))
            self.irr_days_var = tk.StringVar()
            ttk.Entry(days_row, textvariable=self.irr_days_var, width=30).pack(side="left", padx=4)
            ttk.Label(days_row, text="e.g. 1-5, 7-10, 12 (blank = all days)", foreground="#666").pack(
                side="left", padx=4
            )

            ttk.Button(irr_frame, text="Show Irradiance Graph", command=self._show_irradiance_graph).pack(
                anchor="w", padx=8, pady=(0, 8)
            )

        power_frame = ttk.LabelFrame(content, text="Inverter Active Power (whole month)")
        power_frame.pack(fill="x", pady=(0, 10))
        if OneInverterOverTime is None:
            unavailable_notice(power_frame, "OneInverterOverTime")
        else:
            row = ttk.Frame(power_frame, padding=8)
            row.pack(fill="x")
            ttk.Label(row, text="Month").pack(side="left", padx=(0, 4))
            self.power_month_var = tk.StringVar(value=MONTHS[0])
            ttk.Combobox(
                row, textvariable=self.power_month_var, values=MONTHS, state="readonly", width=15
            ).pack(side="left", padx=4)
            ttk.Label(row, text="Inverter").pack(side="left", padx=(12, 4))
            self.inv_var = tk.IntVar(value=1)
            ttk.Spinbox(row, from_=1, to=75, textvariable=self.inv_var, width=6).pack(side="left", padx=4)

            days_row = ttk.Frame(power_frame, padding=(8, 0, 8, 8))
            days_row.pack(fill="x")
            ttk.Label(days_row, text="Days").pack(side="left", padx=(0, 4))
            self.power_days_var = tk.StringVar()
            ttk.Entry(days_row, textvariable=self.power_days_var, width=30).pack(side="left", padx=4)
            ttk.Label(days_row, text="e.g. 1-5, 7-10, 12 (blank = all days)", foreground="#666").pack(
                side="left", padx=4
            )

            ttk.Button(power_frame, text="Show Power Graph", command=self._show_power_graph).pack(
                anchor="w", padx=8, pady=(0, 8)
            )

        multi_power_frame = ttk.LabelFrame(content, text="Active Power (multiple inverters, one day)")
        multi_power_frame.pack(fill="x", pady=(0, 10))
        if OneDayMultInverters is None:
            unavailable_notice(multi_power_frame, "OneDayMultInverters")
        else:
            form = ttk.Frame(multi_power_frame, padding=8)
            form.pack(fill="x")

            ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=4, pady=4)
            self.multi_power_month_var = tk.StringVar(value=MONTHS[0])
            month_box = ttk.Combobox(
                form, textvariable=self.multi_power_month_var, values=MONTHS, state="readonly", width=15
            )
            month_box.grid(row=0, column=1, padx=4, pady=4)
            month_box.bind("<<ComboboxSelected>>", lambda e: self._on_multi_power_month_change())

            ttk.Label(form, text="Day").grid(row=0, column=2, sticky="w", padx=4, pady=4)
            self.multi_power_day_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.multi_power_day_var, width=6).grid(
                row=0, column=3, sticky="w", padx=4, pady=4
            )

            self.multi_power_good_days_var = tk.StringVar()
            ttk.Label(form, text="Good days:").grid(row=0, column=4, sticky="w", padx=(12, 4), pady=4)
            ttk.Label(form, textvariable=self.multi_power_good_days_var, foreground="#666", wraplength=260).grid(
                row=0, column=5, sticky="w", padx=4, pady=4
            )

            ttk.Label(form, text="Inverters").grid(row=1, column=0, sticky="w", padx=4, pady=4)
            self.multi_power_inv_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.multi_power_inv_var, width=20).grid(
                row=1, column=1, columnspan=2, sticky="w", padx=4, pady=4
            )
            ttk.Label(form, text="e.g. 1-5, 8-10, 12 (blank = all)", foreground="#666").grid(
                row=1, column=3, columnspan=2, sticky="w", padx=4, pady=4
            )

            ttk.Button(
                multi_power_frame, text="Show Power Graph", command=self._show_multi_power_graph
            ).pack(anchor="w", padx=8, pady=(0, 8))

            self._on_multi_power_month_change()

        graph_frame = ttk.LabelFrame(content, text="Sunset Energy Comparison Graph")
        graph_frame.pack(fill="x", pady=(0, 10))
        if VisualizeEnergies is None:
            unavailable_notice(graph_frame, "VisualizeEnergies")
        else:
            form = ttk.Frame(graph_frame, padding=8)
            form.pack(fill="x")

            ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=4, pady=4)
            self.graph_month_var = tk.StringVar(value=MONTHS[0])
            month_box = ttk.Combobox(
                form, textvariable=self.graph_month_var, values=MONTHS, state="readonly", width=15
            )
            month_box.grid(row=0, column=1, padx=4, pady=4)
            month_box.bind("<<ComboboxSelected>>", lambda e: self._on_graph_month_change())

            ttk.Label(form, text="Day").grid(row=0, column=2, sticky="w", padx=4, pady=4)
            self.graph_day_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.graph_day_var, width=6).grid(
                row=0, column=3, sticky="w", padx=4, pady=4
            )

            self.graph_good_days_var = tk.StringVar()
            ttk.Label(form, text="Good days:").grid(row=0, column=4, sticky="w", padx=(12, 4), pady=4)
            ttk.Label(form, textvariable=self.graph_good_days_var, foreground="#666", wraplength=260).grid(
                row=0, column=5, sticky="w", padx=4, pady=4
            )

            # Not shown in the UI, but still tracked -- makeGraph() needs the
            # configured sunset curve time even though the field isn't visible.
            self.graph_time_var = tk.StringVar()

            ttk.Label(form, text="Inverters").grid(row=1, column=0, sticky="w", padx=4, pady=4)
            self.graph_inv_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.graph_inv_var, width=20).grid(
                row=1, column=1, columnspan=2, sticky="w", padx=4, pady=4
            )
            ttk.Label(form, text="e.g. 1-5, 8-10, 12 (blank = all)", foreground="#666").grid(
                row=1, column=3, columnspan=2, sticky="w", padx=4, pady=4
            )

            ttk.Button(graph_frame, text="Show Graph", command=self._show_graph).pack(
                anchor="w", padx=8, pady=(0, 8)
            )

            self._on_graph_month_change()

        ttk.Label(
            content,
            text="Each graph opens in a separate Matplotlib window (may block this window until closed).",
            foreground="#666",
            wraplength=650,
            justify="left",
        ).pack(anchor="w", pady=4)

    def _show_irradiance_graph(self):
        month = self.irr_month_var.get()
        days_text = self.irr_days_var.get().strip()
        if not days_text:
            days = None  # showGraph treats None as "all days"
        else:
            try:
                days = parse_day_range(days_text)
            except ValueError as exc:
                messagebox.showerror("Invalid days", f"Couldn't parse the days field: {exc}")
                return
        try:
            IrradianceOneMonth.showGraph(month, days)
        except FileNotFoundError:
            close_stray_graph_windows()
            messagebox.showerror("Data not found", f"No irradiance data found for {month}.")
        except IndexError:
            close_stray_graph_windows()
            messagebox.showerror("Invalid days", f"One or more of those days don't exist in {month}'s data.")
        except Exception as exc:
            close_stray_graph_windows()
            messagebox.showerror("Error", str(exc))

    def _show_power_graph(self):
        month = self.power_month_var.get()
        inv = self.inv_var.get()
        days_text = self.power_days_var.get().strip()
        if not days_text:
            days = None  # showGraph treats None as "all days"
        else:
            try:
                days = parse_day_range(days_text)
            except ValueError as exc:
                messagebox.showerror("Invalid days", f"Couldn't parse the days field: {exc}")
                return
        try:
            OneInverterOverTime.showGraph(month, inv, days)
        except FileNotFoundError:
            close_stray_graph_windows()
            messagebox.showerror("Data not found", f"No active power data found for Inverter {inv} in {month}.")
        except IndexError:
            close_stray_graph_windows()
            messagebox.showerror("Invalid days", f"One or more of those days don't exist in {month}'s data.")
        except Exception as exc:
            close_stray_graph_windows()
            messagebox.showerror("Error", str(exc))

    def _on_multi_power_month_change(self):
        cfg = load_config()
        month = self.multi_power_month_var.get()
        self.multi_power_good_days_var.set(good_days_summary(cfg, month))

    def _show_multi_power_graph(self):
        month = self.multi_power_month_var.get()
        day = resolve_day_input(self.multi_power_day_var.get(), month)
        if day is None:
            return

        inv_text = self.multi_power_inv_var.get().strip()
        if not inv_text:
            inv_nums = []
        else:
            try:
                inv_nums = parse_day_range(inv_text)
            except ValueError as exc:
                messagebox.showerror("Invalid inverters", f"Couldn't parse the inverters field: {exc}")
                return

        try:
            OneDayMultInverters.makeGraph(month, day, inv_nums)
        except FileNotFoundError:
            close_stray_graph_windows()
            messagebox.showerror("Data not found", f"No active power data found for {month}.")
        except Exception as exc:
            close_stray_graph_windows()
            messagebox.showerror("Error", str(exc))

    def _on_graph_month_change(self):
        cfg = load_config()
        month = self.graph_month_var.get()
        self.graph_good_days_var.set(good_days_summary(cfg, month))
        self.graph_time_var.set(cfg["sunsetTimes"].get(month, ""))

    def _show_graph(self):
        month = self.graph_month_var.get()
        time = self.graph_time_var.get().strip()
        inv_text = self.graph_inv_var.get().strip()

        day = resolve_day_input(self.graph_day_var.get(), month)
        if day is None:
            return

        if not time:
            messagebox.showwarning(
                "Missing sunset curve time", f"{month} has no sunset curve time set. Set one in the Config Editor tab."
            )
            return

        if not inv_text:
            inv_nums = []
        else:
            try:
                inv_nums = parse_day_range(inv_text)
            except ValueError as exc:
                messagebox.showerror("Invalid inverters", f"Couldn't parse the inverters field: {exc}")
                return

        try:
            VisualizeEnergies.makeGraph(month, day, time, inv_nums)
        except FileNotFoundError:
            close_stray_graph_windows()
            messagebox.showerror(
                "Data not found",
                f"No {month}SunsetEnergies.csv found. Generate it with CompareEnergy.py first.",
            )
        except KeyError as exc:
            close_stray_graph_windows()
            messagebox.showerror("Missing data", f"No column for '{day} {time}' in the energies CSV: {exc}")
        except Exception as exc:
            close_stray_graph_windows()
            messagebox.showerror("Error", str(exc))


class GoodDaysDialog(tk.Toplevel):
    """Popup for editing one month's list of good days.

    The dialog already knows the year/month, so days are entered and shown
    as a plain day-of-month (e.g. "15") -- only valid calendar days are
    accepted and duplicates are rejected. "Suggest Good Days" runs the
    irradiance-based good-day finder for this month and just displays the
    results -- it never adds them itself; a day is only added when the user
    types it into "Add day of month" and clicks Add. Nothing is persisted
    to config.json until Save is clicked.

    Not modal (no grab_set), so the main window stays fully usable --
    including switching tabs -- while this dialog is open.
    """

    def __init__(self, parent, month_year, current_days, on_save):
        super().__init__(parent)
        self.title(f"Good Days - {month_year}")
        self.resizable(False, False)
        self.transient(parent)

        self.month_year = month_year
        self.year, self.month = parse_month_year(month_year)
        self.on_save = on_save

        list_row = ttk.Frame(self, padding=10)
        list_row.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(list_row, height=10, width=20)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_row, command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self._set_day_nums(int(day.split("-")[2]) for day in current_days)

        add_row = ttk.Frame(self, padding=(10, 0))
        add_row.pack(fill="x")
        ttk.Label(add_row, text="Add day of month:").pack(side="left")
        self.new_day_var = tk.StringVar()
        entry = ttk.Entry(add_row, textvariable=self.new_day_var, width=6)
        entry.pack(side="left", padx=4)
        entry.bind("<Return>", lambda e: self._add_day())
        entry.focus_set()
        ttk.Button(add_row, text="Add", command=self._add_day).pack(side="left", padx=4)

        ttk.Button(
            self, text="Suggest Good Days (by Irradiance)", command=self._suggest_good_days
        ).pack(anchor="w", padx=10, pady=(6, 0))
        self.status_var = tk.StringVar()
        ttk.Label(
            self, textvariable=self.status_var, foreground="#666", wraplength=260, justify="left"
        ).pack(anchor="w", padx=10, pady=(2, 0))

        btn_row = ttk.Frame(self, padding=10)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Remove Selected", command=self._remove_day).pack(side="left")
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(btn_row, text="Save", command=self._save).pack(side="right", padx=4)

    def _existing_day_nums(self):
        return {int(d) for d in self.listbox.get(0, "end")}

    def _set_day_nums(self, nums):
        self.listbox.delete(0, "end")
        for n in sorted(set(nums)):
            self.listbox.insert("end", f"{n:02d}")

    def _add_day(self):
        day_str = self.new_day_var.get().strip()
        if not day_str:
            return
        try:
            day_num = int(day_str)
        except ValueError:
            messagebox.showerror("Invalid day", "Enter a day number (e.g. 15).", parent=self)
            return
        try:
            datetime.date(self.year, self.month, day_num)
        except ValueError:
            messagebox.showerror("Invalid day", f"{day_num} isn't a valid day in {self.month_year}.", parent=self)
            return
        if day_num in self._existing_day_nums():
            messagebox.showerror("Duplicate", f"Day {day_num} is already in the list.", parent=self)
            return
        self._set_day_nums(self._existing_day_nums() | {day_num})
        self.new_day_var.set("")

    def _remove_day(self):
        for index in reversed(self.listbox.curselection()):
            self.listbox.delete(index)

    def _suggest_good_days(self):
        if FindGoodDaysByIrradiance is None:
            self.status_var.set("Unavailable: FindGoodDaysByIrradiance failed to import.")
            return
        cfg = load_config()
        sunset_time = cfg["sunsetTimes"].get(self.month_year, "").strip()
        if not sunset_time:
            self.status_var.set("Set a sunset curve time for this month first.")
            return
        filepath = PROJECT_ROOT / "Data" / "Irradiance" / f"{self.month_year}.csv"
        if not filepath.exists():
            self.status_var.set(f"No irradiance data found for {self.month_year}.")
            return
        try:
            import pandas as pd  # already a dependency of the imported modules
            df = pd.read_csv(filepath)
            sunset_index = FindGoodDaysByIrradiance.findSunsetTimeIndex(df, sunset_time)
            good_days = FindGoodDaysByIrradiance.getGoodDays(df, sunset_index)
        except Exception as exc:
            self.status_var.set(f"Error: {exc}")
            return

        suggested = sorted({int(day.split("-")[2]) for day in good_days})
        if not suggested:
            self.status_var.set("No good days found.")
            return
        self.status_var.set("Suggested: " + ", ".join(f"{n:02d}" for n in suggested))

    def _save(self):
        days_full = [f"{self.year:04d}-{self.month:02d}-{int(d):02d}" for d in self.listbox.get(0, "end")]
        self.on_save(days_full)
        self.destroy()


class ConfigTab(ttk.Frame):
    """Edits config.json -- this is project data, not analysis logic.

    All months are shown at once, in chronological order. Double-click a
    Sunrise/Sunset/Slope/Concavity cell to edit it inline; double-click a
    Good Days cell to open the day editor.
    """

    COLUMNS = ("month", "sunrise", "sunset", "slope", "d2", "gooddays")
    HEADINGS = {
        "month": "Month",
        "sunrise": "Sunrise Curve Time",
        "sunset": "Sunset Curve Time",
        "slope": "Slope Cutoff",
        "d2": "Concavity Cutoff",
        "gooddays": "Good Days",
    }
    CONFIG_KEYS = {
        "sunrise": "sunriseTimes",
        "sunset": "sunsetTimes",
        "slope": "slopeCutOffs",
        "d2": "d2CutOffs",
    }
    NUMERIC_COLUMNS = {"slope", "d2"}

    def __init__(self, parent):
        super().__init__(parent, padding=10)

        ttk.Label(
            self,
            text=(
                "Sunrise Curve Time is a placeholder for future use -- no analysis script reads it yet.\n"
                "Double-click a cell to edit it. Double-click Good Days to add/remove/suggest days."
            ),
            foreground="#666",
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Config.Treeview", rowheight=32, bordercolor="#999999", borderwidth=1, relief="solid")
        style.configure(
            "Config.Treeview.Heading",
            background="#4a4a4a",
            foreground="white",
            relief="raised",
            borderwidth=1,
        )
        # Pin heading colors so hovering/pressing a header doesn't switch to
        # the theme's lighter default state and make the white text unreadable.
        style.map(
            "Config.Treeview.Heading",
            background=[("active", "#4a4a4a"), ("pressed", "#4a4a4a")],
            foreground=[("active", "white"), ("pressed", "white")],
        )

        self.tree = ttk.Treeview(
            tree_frame, columns=self.COLUMNS, show="headings", height=12, style="Config.Treeview"
        )
        widths = {"month": 100, "sunrise": 100, "sunset": 100, "slope": 90, "d2": 110, "gooddays": 320}
        for col in self.COLUMNS:
            self.tree.heading(col, text=self.HEADINGS[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#dcdcdc")

        scrollbar = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        scrollbar.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Clicking anywhere that isn't a row/cell in this table clears the
        # selection highlight, instead of leaving the last-clicked row
        # highlighted indefinitely.
        self.winfo_toplevel().bind_all("<Button-1>", self._on_global_click, add="+")

        self.tree.bind("<Double-1>", self._on_double_click)

        self._editor = None  # active inline-edit Entry, if any

        self._reload()

    def _reload(self):
        cfg = load_config()
        self.tree.delete(*self.tree.get_children())
        for i, month in enumerate(MONTHS):
            good_days = cfg["days"].get(month, [])
            self.tree.insert(
                "", "end", iid=month,
                values=(
                    month,
                    cfg.get("sunriseTimes", {}).get(month, ""),
                    cfg["sunsetTimes"].get(month, ""),
                    cfg["slopeCutOffs"].get(month, 0),
                    cfg["d2CutOffs"].get(month, 0),
                    ", ".join(good_days),
                ),
                tags=("oddrow" if i % 2 else "evenrow",),
            )

    def _on_global_click(self, event):
        if not self.tree.winfo_exists():
            return
        if event.widget is self.tree and self.tree.identify("region", event.x, event.y) == "cell":
            return  # let the tree's normal row-selection behavior happen
        if self.tree.selection():
            self.tree.selection_remove(*self.tree.selection())

    def _on_double_click(self, event):
        if self._editor is not None:
            return  # already editing a cell
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not row_id or not col_id:
            return
        col_name = self.COLUMNS[int(col_id.replace("#", "")) - 1]

        if col_name == "month":
            return
        if col_name == "gooddays":
            self._open_good_days_dialog(row_id)
            return
        self._start_cell_edit(row_id, col_id, col_name)

    def _start_cell_edit(self, row_id, col_id, col_name):
        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox

        entry = ttk.Entry(self.tree)
        entry.insert(0, self.tree.set(row_id, col_name))
        entry.select_range(0, "end")
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        self._editor = entry

        def commit(event=None):
            if self._editor is None:
                return
            self._commit_cell_edit(row_id, col_name, entry.get().strip())

        def cancel(event=None):
            self._destroy_editor()

        entry.bind("<Return>", commit)
        entry.bind("<FocusOut>", commit)
        entry.bind("<Escape>", cancel)

    def _destroy_editor(self):
        if self._editor is not None:
            self._editor.destroy()
            self._editor = None

    def _commit_cell_edit(self, row_id, col_name, new_value):
        if col_name in self.NUMERIC_COLUMNS:
            try:
                new_value = float(new_value)
            except ValueError:
                messagebox.showerror("Invalid input", f"{self.HEADINGS[col_name]} must be a number.")
                self._destroy_editor()
                return

        cfg = load_config()
        old_value = cfg[self.CONFIG_KEYS[col_name]].get(row_id)
        self._destroy_editor()

        if new_value == old_value:
            # Unchanged -- e.g. the user clicked into the cell and clicked
            # back out without editing it. Skip the save and (for sunset)
            # skip regenerating the Slopes/Concavity/SunsetEnergies CSVs,
            # since nothing actually changed.
            return

        cfg[self.CONFIG_KEYS[col_name]][row_id] = new_value
        save_config(cfg)

        self.tree.set(row_id, col_name, new_value)

        if col_name == "sunset":
            self._regenerate_analysis_csvs(row_id, on_done=lambda: self._regenerate_energy_file(row_id))

    def _open_good_days_dialog(self, month):
        cfg = load_config()
        current_days = cfg["days"].get(month, [])

        def on_save(new_days):
            cfg2 = load_config()
            cfg2["days"][month] = new_days
            save_config(cfg2)
            self.tree.set(month, "gooddays", ", ".join(new_days))
            # Not regenerating Slopes/Concavity or SunsetEnergies CSVs here:
            # generateCSV()/makeFile() now compute for every day present in
            # the data, not just the configured good days, so they no longer
            # depend on this list. Only a sunset curve time change re-runs
            # them (see _commit_cell_edit).

        GoodDaysDialog(self, month, current_days, on_save)

    def _regenerate_analysis_csvs(self, month, on_done=None):
        """Rebuild Slopes/{month}.csv and Concavities/{month}.csv for the
        current sunset time, since AnalyzeDropSlopes/AnalyzeConcavity read
        those files rather than computing on the fly. Only triggered by a
        sunset curve time change -- both generateCSV() functions now compute
        for every day present in the inverter data, not just the configured
        good days, so a good-days change no longer needs to re-run them.

        FindConcavity.generateCSV() reads Slopes/{month}.csv itself, so it
        must only run once FindDropSlopes.generateCSV() has finished
        successfully -- the sequential calls below, both inside the same
        try block, already guarantee that (an exception from the first call
        skips the second). Both functions print their own per-inverter
        progress, which can take a while, so that output is captured and
        shown in a popup -- run in a background thread so the popup can
        actually appear and render right away instead of sitting invisible
        until this whole (possibly slow) call returns to the mainloop.
        on_done(), if given, runs afterward on the UI thread regardless of
        success/failure, once the popup has been updated -- used to chain
        _regenerate_energy_file() after this instead of racing it."""
        missing = [
            name
            for name, mod in (
                ("FindDropSlopes", FindDropSlopes),
                ("FindConcavity", FindConcavity),
            )
            if mod is None
        ]
        if missing:
            messagebox.showerror(
                "Unavailable",
                "Can't regenerate Slopes/Concavity CSVs -- "
                + "; ".join(f"{name}: {IMPORT_ERRORS.get(name)}" for name in missing),
            )
            if on_done:
                on_done()
            return

        cfg = load_config()
        sunset_time = cfg["sunsetTimes"].get(month, "").strip()
        if not sunset_time:
            messagebox.showwarning(
                "Missing sunset curve time",
                f"Set a sunset curve time for {month} before its Slopes/Concavity CSVs can be regenerated.",
            )
            if on_done:
                on_done()
            return

        _win, text_widget = show_output_popup(
            self,
            "Slopes/Concavity regeneration output",
            "Running -- this can take a while (calculating slopes/concavity for every inverter)...",
        )

        def work():
            error = None
            writer = _LivePopupWriter(self, text_widget)
            sys.stdout.set_buffer(writer)
            try:
                FindDropSlopes.generateCSV(month, sunset_time)
                FindConcavity.generateCSV(month)
            except Exception as exc:
                error = str(exc)
            finally:
                sys.stdout.set_buffer(None)

            def finish():
                if error:
                    messagebox.showerror(
                        "Regeneration failed",
                        f"Couldn't regenerate Slopes/Concavity CSVs for {month}:\n{error}",
                    )
                if on_done:
                    on_done()

            self.after(0, finish)

        threading.Thread(target=work, daemon=True).start()

    def _regenerate_energy_file(self, month):
        """Rebuild {month}SunsetEnergies.csv, since the sunset energy graph
        reads that file rather than computing on the fly. Only triggered by
        a sunset curve time change -- CompareEnergy.makeFile() now computes
        energy for every day in the month (not just the configured good
        days), so a good-days change no longer needs to re-run it."""
        if CompareEnergy is None:
            messagebox.showerror(
                "Unavailable",
                f"Can't regenerate the SunsetEnergies CSV -- CompareEnergy: {IMPORT_ERRORS.get('CompareEnergy')}",
            )
            return

        cfg = load_config()
        sunset_time = cfg["sunsetTimes"].get(month, "").strip()
        if not sunset_time:
            messagebox.showwarning(
                "Missing sunset curve time",
                f"Set a sunset curve time for {month} before its SunsetEnergies CSV can be regenerated.",
            )
            return

        try:
            CompareEnergy.makeFile(month)
        except Exception as exc:
            messagebox.showerror(
                "Regeneration failed",
                f"Couldn't regenerate the SunsetEnergies CSV for {month}:\n{exc}",
            )


def main():
    root = tk.Tk()
    root.title("Solar SURP Data Analysis")
    root.geometry("1050x700")

    # 'clam' is used instead of the Windows-native default theme because
    # that native theme ignores custom Treeview colors (heading background,
    # row striping) needed by the Config Editor tab. clam's own default
    # background is a tan/gray, so it's overridden to white below -- the
    # Config Editor's own deliberate header/row colors (set directly on its
    # Config.Treeview style) are unaffected by this.
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", background="white", fieldbackground="white")
    for widget_style in (
        "TFrame", "TLabelframe", "TLabelframe.Label", "TLabel",
        "TNotebook", "TNotebook.Tab", "TButton", "TCheckbutton", "TRadiobutton",
    ):
        style.configure(widget_style, background="white")
    root.configure(background="white")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    notebook.add(MonthlyGraphsTab(notebook), text="Graphs")
    notebook.add(FlagsTab(notebook), text="Shady")
    notebook.add(ConfigTab(notebook), text="Config Editor")

    root.mainloop()


if __name__ == "__main__":
    main()
