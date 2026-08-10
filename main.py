"""
UI for exploring the Solar_SURP analysis results.

This file only builds a UI on top of the analysis logic that already lives
under Data_Analysis/ -- it does not reimplement or modify that logic. It
imports the following modules and calls their functions directly:
    Data_Analysis/EnergyComparisons/CalcEnergy.py         -> getEnergy
    Data_Analysis/EnergyComparisons/FindGoodDaysByIrradiance.py
                                        -> findSunsetTimeIndex, getGoodDays
    Data_Analysis/MathingIt/AnalyzeDropSlopes.py           -> getResults
    Data_Analysis/MathingIt/AnalyzeConcavity.py            -> getResults
    Data_Analysis/EnergyComparisons/VisualizeEnergies.py   -> makeGraph
    Data_Analysis/VisualizeIrradiance/IrradianceOneMonth.py -> showGraph
    Data_Analysis/VisualizeActivePowers/OneInverterOverTime.py -> showGraph

Some other scripts in Data_Analysis/ write/overwrite CSV files as a side
effect of merely being imported (e.g. the MakeAvgAPCSV.py files,
FindConcavity.py, FindDropSlopes.py, CompareEnergy.py). Those are
intentionally NOT wired into this UI yet -- importing them here would
trigger those side effects on every app launch.
"""

import os
import sys
import json
import datetime
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

IMPORT_ERRORS = {}


def _try_import(module_name):
    try:
        return __import__(module_name)
    except Exception as exc:  # missing file, bad CSV path, etc.
        IMPORT_ERRORS[module_name] = str(exc)
        return None


CalcEnergy = _try_import("CalcEnergy")
FindGoodDaysByIrradiance = _try_import("FindGoodDaysByIrradiance")
AnalyzeDropSlopes = _try_import("AnalyzeDropSlopes")
AnalyzeConcavity = _try_import("AnalyzeConcavity")
VisualizeEnergies = _try_import("VisualizeEnergies")
IrradianceOneMonth = _try_import("IrradianceOneMonth")
OneInverterOverTime = _try_import("OneInverterOverTime")
FindDropSlopes = _try_import("FindDropSlopes")
FindConcavity = _try_import("FindConcavity")


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
        self.day_box = ttk.Combobox(form, textvariable=self.day_var, values=[], state="readonly", width=15)
        self.day_box.grid(row=0, column=3, padx=4, pady=4)

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
        days = cfg["days"].get(self.month_var.get(), [])
        self.day_box.configure(values=days)
        self.day_var.set(days[0] if days else "")

    @staticmethod
    def _inverter_key(result_line):
        """'Inverter 46 -3.78 OUTLIER' -> 'Inverter 46'"""
        return " ".join(result_line.split()[:2])

    def _run_slopes(self):
        if AnalyzeDropSlopes is None:
            messagebox.showerror("Unavailable", f"AnalyzeDropSlopes failed to import:\n{IMPORT_ERRORS.get('AnalyzeDropSlopes')}")
            return
        month, day = self.month_var.get(), self.day_var.get()
        if not day:
            messagebox.showwarning("Missing day", "This month has no configured days to analyze.")
            return
        try:
            results = AnalyzeDropSlopes.getResults(month, day)
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
        month, day = self.month_var.get(), self.day_var.get()
        if not day:
            messagebox.showwarning("Missing day", "This month has no configured days to analyze.")
            return
        try:
            results = AnalyzeConcavity.getResults(month, day)
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


class EnergyGraphsTab(ttk.Frame):
    """Energy Calculator + Sunset Energy Comparison Graph, stacked in one tab."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)

        calc_frame = ttk.LabelFrame(self, text="Energy Calculator")
        calc_frame.pack(fill="x", pady=(0, 10))
        if CalcEnergy is None:
            unavailable_notice(calc_frame, "CalcEnergy")
        else:
            form = ttk.Frame(calc_frame, padding=8)
            form.pack(fill="x")

            ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=4, pady=4)
            self.calc_month_var = tk.StringVar(value=MONTHS[0])
            month_box = ttk.Combobox(
                form, textvariable=self.calc_month_var, values=MONTHS, state="readonly", width=15
            )
            month_box.grid(row=0, column=1, padx=4, pady=4)
            month_box.bind("<<ComboboxSelected>>", lambda e: self._on_calc_month_change())

            ttk.Label(form, text="Inverter").grid(row=0, column=2, sticky="w", padx=4, pady=4)
            self.calc_inv_var = tk.IntVar(value=1)
            ttk.Spinbox(form, from_=1, to=75, textvariable=self.calc_inv_var, width=6).grid(
                row=0, column=3, padx=4, pady=4
            )

            ttk.Label(form, text="Day (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=4, pady=4)
            self.calc_day_var = tk.StringVar()
            self.calc_day_box = ttk.Combobox(form, textvariable=self.calc_day_var, values=[], width=15)
            self.calc_day_box.grid(row=1, column=1, padx=4, pady=4)

            ttk.Label(form, text="Start Time (HH:MM:SS)").grid(row=1, column=2, sticky="w", padx=4, pady=4)
            self.calc_time_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.calc_time_var, width=12).grid(row=1, column=3, padx=4, pady=4)

            ttk.Button(form, text="Calculate Energy", command=self._calculate).grid(
                row=2, column=0, columnspan=4, pady=8
            )

            self.calc_result_var = tk.StringVar(value="")
            ttk.Label(calc_frame, textvariable=self.calc_result_var, font=("Segoe UI", 11, "bold")).pack(
                anchor="w", padx=8, pady=(0, 8)
            )

            self._on_calc_month_change()

        graph_frame = ttk.LabelFrame(self, text="Sunset Energy Comparison Graph")
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
            self.graph_day_box = ttk.Combobox(
                form, textvariable=self.graph_day_var, values=[], state="readonly", width=15
            )
            self.graph_day_box.grid(row=0, column=3, padx=4, pady=4)

            ttk.Label(form, text="Sunset Time").grid(row=1, column=0, sticky="w", padx=4, pady=4)
            self.graph_time_var = tk.StringVar()
            ttk.Entry(form, textvariable=self.graph_time_var, width=12, state="readonly").grid(
                row=1, column=1, padx=4, pady=4
            )

            ttk.Label(form, text="First Inverter").grid(row=1, column=2, sticky="w", padx=4, pady=4)
            self.first_inv_var = tk.IntVar(value=1)
            ttk.Spinbox(form, from_=1, to=75, textvariable=self.first_inv_var, width=6).grid(
                row=1, column=3, padx=4, pady=4
            )

            ttk.Label(form, text="Last Inverter").grid(row=1, column=4, sticky="w", padx=4, pady=4)
            self.last_inv_var = tk.IntVar(value=75)
            ttk.Spinbox(form, from_=1, to=75, textvariable=self.last_inv_var, width=6).grid(
                row=1, column=5, padx=4, pady=4
            )

            ttk.Button(graph_frame, text="Show Graph", command=self._show_graph).pack(
                anchor="w", padx=8, pady=(0, 4)
            )

            ttk.Label(
                graph_frame,
                text=(
                    "Opens in a separate Matplotlib window (may block this window until closed).\n"
                    "Bar colors (red = flagged inverter) are hardcoded in VisualizeEnergies.py for "
                    "July2025 only — they won't be meaningful for other months."
                ),
                foreground="#666",
                wraplength=650,
                justify="left",
            ).pack(anchor="w", padx=8, pady=(0, 8))

            self._on_graph_month_change()

    def _on_calc_month_change(self):
        cfg = load_config()
        month = self.calc_month_var.get()
        days = cfg["days"].get(month, [])
        self.calc_day_box.configure(values=days)
        if days:
            self.calc_day_var.set(days[0])
        sunset = cfg["sunsetTimes"].get(month, "")
        if sunset:
            self.calc_time_var.set(sunset)

    def _calculate(self):
        month = self.calc_month_var.get()
        inv = self.calc_inv_var.get()
        day = self.calc_day_var.get().strip()
        start_time = self.calc_time_var.get().strip()
        if not day or not start_time:
            messagebox.showwarning("Missing input", "Please provide both a day and a start time.")
            return
        try:
            energy = CalcEnergy.getEnergy(month, inv, day, start_time)
        except FileNotFoundError as exc:
            messagebox.showerror("Data not found", f"Could not read data for this selection:\n{exc}")
            return
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.calc_result_var.set(f"Energy produced: {energy:.3f}")

    def _on_graph_month_change(self):
        cfg = load_config()
        month = self.graph_month_var.get()
        days = cfg["days"].get(month, [])
        self.graph_day_box.configure(values=days)
        self.graph_day_var.set(days[0] if days else "")
        self.graph_time_var.set(cfg["sunsetTimes"].get(month, ""))

    def _show_graph(self):
        month = self.graph_month_var.get()
        day = self.graph_day_var.get().strip()
        time = self.graph_time_var.get().strip()
        first_inv = self.first_inv_var.get()
        last_inv = self.last_inv_var.get()
        if not day:
            messagebox.showwarning("Missing input", "This month has no configured days to choose from.")
            return
        if not time:
            messagebox.showwarning(
                "Missing sunset time", f"{month} has no sunset time set. Set one in the Config Editor tab."
            )
            return
        if first_inv > last_inv:
            messagebox.showwarning("Invalid range", "First Inverter must be <= Last Inverter.")
            return
        try:
            VisualizeEnergies.makeGraph(month, day, time, first_inv, last_inv)
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


class MonthlyGraphsTab(ttk.Frame):
    """Whole-month line graphs (one line per day) for irradiance and for a
    single inverter's active power."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)

        irr_frame = ttk.LabelFrame(self, text="Irradiance (whole month)")
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

        power_frame = ttk.LabelFrame(self, text="Inverter Active Power (whole month)")
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

        ttk.Label(
            self,
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
            self.status_var.set("Set a sunset time for this month first.")
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
        "sunrise": "Sunrise Time",
        "sunset": "Sunset Time",
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
                "Sunrise Time is a placeholder for future use -- no analysis script reads it yet.\n"
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
        cfg[self.CONFIG_KEYS[col_name]][row_id] = new_value
        save_config(cfg)

        self.tree.set(row_id, col_name, new_value)
        self._destroy_editor()

        if col_name == "sunset":
            self._regenerate_analysis_csvs(row_id, cfg["days"].get(row_id, []))

    def _open_good_days_dialog(self, month):
        cfg = load_config()
        current_days = cfg["days"].get(month, [])

        def on_save(new_days):
            cfg2 = load_config()
            cfg2["days"][month] = new_days
            save_config(cfg2)
            self.tree.set(month, "gooddays", ", ".join(new_days))
            self._regenerate_analysis_csvs(month, new_days)

        GoodDaysDialog(self, month, current_days, on_save)

    def _regenerate_analysis_csvs(self, month, days):
        """Rebuild Slopes/{month}.csv and Concavities/{month}.csv for the
        current good days, since AnalyzeDropSlopes/AnalyzeConcavity read
        those files rather than computing on the fly."""
        if FindDropSlopes is None or FindConcavity is None:
            messagebox.showerror(
                "Unavailable",
                "Can't regenerate Slopes/Concavity CSVs -- "
                f"{IMPORT_ERRORS.get('FindDropSlopes') or IMPORT_ERRORS.get('FindConcavity')}",
            )
            return
        if not days:
            return  # nothing to compute

        cfg = load_config()
        sunset_time = cfg["sunsetTimes"].get(month, "").strip()
        if not sunset_time:
            messagebox.showwarning(
                "Missing sunset time",
                f"Set a sunset time for {month} before its Slopes/Concavity CSVs can be regenerated.",
            )
            return

        try:
            import pandas as pd  # already a dependency of the imported modules

            FindDropSlopes.generateCSV(month, days, sunset_time)
            slopes_path = PROJECT_ROOT / "Data_Analysis" / "MathingIt" / "Slopes" / f"{month}.csv"
            df_st = pd.read_csv(slopes_path)
            FindConcavity.generateCSV(month, df_st, days)
        except Exception as exc:
            messagebox.showerror(
                "Regeneration failed",
                f"Couldn't regenerate Slopes/Concavity CSVs for {month}:\n{exc}",
            )


def main():
    root = tk.Tk()
    root.title("Solar SURP Data Analysis")
    root.geometry("1050x700")

    # 'clam' is used instead of the Windows-native default theme because
    # that native theme ignores custom Treeview colors (heading background,
    # row striping) needed by the Config Editor tab.
    ttk.Style().theme_use("clam")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    notebook.add(MonthlyGraphsTab(notebook), text="Graphs")
    notebook.add(EnergyGraphsTab(notebook), text="Energy Graphs")
    notebook.add(FlagsTab(notebook), text="Shady")
    notebook.add(ConfigTab(notebook), text="Config Editor")

    root.mainloop()


if __name__ == "__main__":
    main()
