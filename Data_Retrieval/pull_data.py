"""
Standalone UI for checking which days in a month have no/low recorded data,
built on top of the existing logic in Data_Retrieval/. This file only
builds a UI -- it does not reimplement that logic. It imports:
    Automatic_Data_Request_Multiple_Files.py -> DataPull
        .seeNoAndLowDataDaysInv / .seeNoAndLowDataDaysIrradiance / .generateFiles

A fresh DataPull() instance is created for each check. That instance records
which days looked bad (self.badDays) and the month/year/time range checked,
so once a check finishes successfully (and wasn't cancelled), a "Generate
Files" button becomes available that reuses that *same* instance to fetch
real files for every remaining (non-bad) day, across every inverter (or the
irradiance sensor) -- confirmed via a popup first. generateFiles() removes
the bad days from the instance's own stored time range as its first step, so
it can only safely be called once per instance; this UI enforces that by
only ever re-enabling "Generate Files" from a fresh successful check, never
from Generate Files' own completion (success, error, or cancel alike).

Both checks (and Generate Files runs) can run at the same time across the
two CheckFrame instances. That's only correct because
seeNoAndLowDataDaysInv/seeNoAndLowDataDaysIrradiance/generateFiles all write
to files scoped to their own check type (TestInv.csv/TestIrr.csv, and
per-inverter/irradiance output paths) -- if two runs of the *same* check
type ever shared one output file, running them concurrently would corrupt
each other's results. Each CheckFrame therefore still has its own lock (see
CheckFrame._run_lock) so a cancelled-then-restarted run of the same check
type waits for its predecessor rather than racing it on that file; it's
only *different* check types that run in parallel.

Since none of the DataPull methods return a value -- they only print their
progress -- this UI needs to capture stdout per-run. contextlib.redirect_stdout
swaps sys.stdout for the whole process, which isn't safe with two runs going
in different threads at once, so instead a single _ThreadLocalStdout is
installed as sys.stdout exactly once and routes each thread's writes to
that thread's own LiveOutputWriter, which streams them into the output pane
live as they happen. Everything here is slow (a live network call per day,
or per inverter for Generate Files, each with a many-second timeout), so
every run happens in a background thread to keep the UI responsive. The
import of Automatic_Data_Request_Multiple_Files is deferred to first use on
a background thread (see get_data_request_module()) rather than happening
at module load, so this window always appears immediately even if something
upstream regresses to being slow/blocking on import again.

Cancel is cooperative: each run gets its own fresh threading.Event (see
CheckFrame._cancel_event), set as instance.cancel_event on the DataPull
instance before its method is called. Clicking Cancel sets that event.
DataPull's loops (in generateFiles and findDaysWithoutData) are expected to
check self.cancel_event.is_set() at the top of each iteration and stop early
-- that's on the Automatic_Data_Request_Multiple_Files.py side, since this
file doesn't touch that one. Cancel therefore takes effect after the
*current* item/network call finishes, not instantly (Python can't safely
force-stop a running thread from outside) -- if that check is ever missing
or removed there, Cancel silently degrades back to a soft cancel: the
button/status reset right away, but the orphaned call keeps running in the
background until it finishes on its own, still holding that frame's
_run_lock until it does.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Automatic_Data_Request_Multiple_Files.py uses paths written relative to the
# project root (e.g. "Data_Retrieval\\GetPowerData.py"), so make sure that's
# the working directory no matter where this is launched from.
os.chdir(PROJECT_ROOT)

MONTHS = [f"{i:02d}" for i in range(1, 13)]

# The import below is only safe to attempt once even if two checks start at
# the same time on first use, so it gets its own (very short-lived) lock,
# separate from each CheckFrame's own _run_lock.
_import_lock = threading.Lock()
_data_request_module = None
_data_request_error = None


def get_data_request_module():
    """Import Automatic_Data_Request_Multiple_Files, caching the result (or
    the error) so it's only attempted once. Call this from a background
    thread, not the UI thread -- see the module docstring for why."""
    global _data_request_module, _data_request_error
    with _import_lock:
        if _data_request_module is None and _data_request_error is None:
            try:
                import Automatic_Data_Request_Multiple_Files as module
                _data_request_module = module
            except Exception as exc:
                _data_request_error = str(exc)
        return _data_request_module, _data_request_error


class _ThreadLocalStdout:
    """Installed once as sys.stdout so multiple runs can stream live output
    concurrently. contextlib.redirect_stdout can't be used for this since it
    swaps sys.stdout for the whole process (not per-thread), which would
    corrupt output if two runs were mid-call at once. Each worker thread
    instead registers its own writer here via set_writer(), and
    write()/flush() route to whichever writer the *calling* thread
    registered -- falling back to the real stdout for anything printed
    from a thread that never registered one."""

    def __init__(self, real_stdout):
        self._real_stdout = real_stdout
        self._local = threading.local()

    def set_writer(self, writer):
        self._local.writer = writer

    def _target(self):
        return getattr(self._local, "writer", None) or self._real_stdout

    def write(self, text):
        return self._target().write(text)

    def flush(self):
        return self._target().flush()


sys.stdout = _ThreadLocalStdout(sys.stdout)


def make_output_pane(parent):
    frame = ttk.Frame(parent)
    text = tk.Text(frame, height=12, wrap="word", state="disabled")
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


def valid_year(year):
    return year.isdigit() and len(year) == 4


def parse_inverter_range(text):
    """'1-5, 8-10, 33' -> [1, 2, 3, 4, 5, 8, 9, 10, 33] (same range format as
    the Days fields elsewhere in this project). Blank/whitespace-only input
    returns [] rather than raising, since generateFiles() treats an empty
    invNums list as "all inverters"."""
    text = text.strip()
    if not text:
        return []
    nums = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start, end = int(start_str.strip()), int(end_str.strip())
            if start > end:
                raise ValueError(f"'{part}' has a start greater than its end.")
            nums.update(range(start, end + 1))
        else:
            nums.add(int(part))
    return sorted(nums)


class LiveOutputWriter:
    """File-like object that pushes each write() to a Tk Text widget as it
    happens, from a background thread -- but only while run_id still matches
    frame.current_run_id, so a cancelled/superseded run's late writes are
    silently dropped instead of corrupting a newer run's output."""

    def __init__(self, frame, run_id):
        self.frame = frame
        self.run_id = run_id
        self.wrote_anything = False

    def _is_current(self):
        return self.frame.current_run_id == self.run_id

    def write(self, text):
        if text and self._is_current():
            self.wrote_anything = True
            self.frame.after(0, self._append, text)
        return len(text)

    def flush(self):
        pass

    def _append(self, text):
        if not self._is_current():
            return
        self.frame.output.configure(state="normal")
        self.frame.output.insert("end", text)
        self.frame.output.see("end")
        self.frame.output.configure(state="disabled")


def run_captured(frame, run_id, work_fn, on_success=None, clear_output=True):
    """Call work_fn() in a background thread, streaming any printed output
    to frame.output live. If frame.current_run_id no longer matches run_id
    by the time this finishes (Cancel was clicked, or a newer run started),
    nothing here touches the UI. Otherwise, once work_fn() returns without
    raising, on_success() (if given) is called on the UI thread -- used to
    reveal "Generate Files" only after a check completes cleanly.

    clear_output controls whether the pane is wiped before this run starts;
    Generate Files passes False so its output appends after the check's
    results instead of erasing them.

    "Generate Files" is deliberately never re-enabled by this function
    itself (only run_button is) -- see the module docstring for why running
    generateFiles() twice on the same DataPull instance isn't safe.

    Only serialized against other runs of this *same* frame (frame._run_lock)
    -- a different CheckFrame's run can proceed concurrently."""
    frame.run_button.configure(state="disabled")
    if hasattr(frame, "generate_button"):
        frame.generate_button.configure(state="disabled")
    frame.cancel_button.configure(state="normal")
    frame.status_var.set("Running -- this can take a while (a live network call per day/item)...")
    if clear_output:
        set_output(frame.output, "")

    def work():
        writer = LiveOutputWriter(frame, run_id)
        error = None
        with frame._run_lock:
            if frame.current_run_id != run_id:
                return  # cancelled while waiting for a prior run of this frame to finish
            try:
                sys.stdout.set_writer(writer)
                try:
                    work_fn()
                finally:
                    sys.stdout.set_writer(None)
            except Exception as exc:
                error = str(exc)

        def finish():
            if frame.current_run_id != run_id:
                return  # cancelled/superseded meanwhile -- don't touch the UI
            frame.run_button.configure(state="normal")
            frame.cancel_button.configure(state="disabled")
            frame.status_var.set("")
            if error:
                writer._append(f"\nError: {error}")
                messagebox.showerror("Error", error)
            else:
                if not writer.wrote_anything:
                    if clear_output:
                        set_output(frame.output, "(no output)")
                    else:
                        writer._append("(no output)")
                if on_success:
                    on_success()

        frame.after(0, finish)

    threading.Thread(target=work, daemon=True).start()


class CheckFrame(ttk.LabelFrame):
    """Shared scaffolding for a panel that runs a slow check, streams its
    output live, offers Cancel/Clear, and -- once a check succeeds -- offers
    a confirmed "Generate Files" follow-up using that same DataPull
    instance. Subclasses build their own input form, then call
    _build_controls() to add the buttons, status line, and output pane."""

    def __init__(self, parent, title, is_inverter):
        super().__init__(parent, text=title)
        self.current_run_id = 0
        self._run_lock = threading.Lock()
        self._is_inverter = is_inverter
        self._data_pull = None  # the DataPull instance from the last successful check
        self._cancel_event = None  # threading.Event for whichever run is currently in flight

    def _build_controls(self, run_text, run_command):
        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=8, pady=(0, 4))

        self.run_button = ttk.Button(btn_row, text=run_text, command=run_command)
        self.run_button.pack(side="left")

        self.cancel_button = ttk.Button(btn_row, text="Cancel", command=self._cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=(6, 0))

        self.clear_button = ttk.Button(btn_row, text="Clear Output", command=self._clear)
        self.clear_button.pack(side="left", padx=(6, 0))

        self.generate_button = ttk.Button(
            btn_row, text="Generate Files", command=self._generate_files, state="disabled"
        )
        self.generate_button.pack(side="left", padx=(6, 0))

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, foreground="#666", wraplength=650, justify="left").pack(
            anchor="w", padx=8
        )

        pane, self.output = make_output_pane(self)
        pane.pack(fill="both", expand=True, padx=8, pady=8)

    def _clear(self):
        set_output(self.output, "")

    def _cancel(self):
        self.current_run_id += 1  # invalidates the in-flight run's writer/finish callback
        if self._cancel_event is not None:
            self._cancel_event.set()
        self.run_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.status_var.set(
            "Cancelling -- will stop after the current item/network call finishes."
        )

    def start_run(self, work_fn, on_success=None, clear_output=True):
        self.current_run_id += 1
        self._cancel_event = threading.Event()
        run_captured(self, self.current_run_id, work_fn, on_success, clear_output)

    def _generate_kwargs_and_kind(self):
        """Hook for subclasses that need to pass extra keyword arguments to
        generateFiles() and describe them in the confirmation popup. Returns
        (extra_kwargs, kind_description), or (None, None) if validation
        failed (the subclass is expected to have already shown its own
        warning in that case). Defaults to no extra arguments."""
        return {}, ("all inverters" if self._is_inverter else "irradiance")

    def _generate_files(self):
        instance = self._data_pull
        if instance is None:
            return
        extra_kwargs, kind = self._generate_kwargs_and_kind()
        if extra_kwargs is None:
            return  # subclass already showed a validation warning
        if not messagebox.askyesno(
            "Generate Files",
            f"Generate data files for {instance.month} {instance.year} ({kind})?\n\n"
            "This fetches and writes real data for every day the check didn't flag "
            "as no-data/low-data, and can take a while.",
        ):
            return

        def work_fn():
            instance.cancel_event = self._cancel_event
            instance.generateFiles(self._is_inverter, **extra_kwargs)

        # no on_success (one-shot per instance); clear_output=False so this
        # appends after the check's own results instead of erasing them
        self.start_run(work_fn, clear_output=False)


class InverterCheckFrame(CheckFrame):
    def __init__(self, parent):
        super().__init__(parent, "No/Low Data Days -- Inverter", is_inverter=True)

        form = ttk.Frame(self, padding=8)
        form.pack(fill="x")

        ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.month_var = tk.StringVar(value=MONTHS[0])
        ttk.Combobox(
            form, textvariable=self.month_var, values=MONTHS, state="readonly", width=6
        ).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(form, text="Year").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.year_var = tk.StringVar(value="2025")
        ttk.Entry(form, textvariable=self.year_var, width=8).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(form, text="Inverter").grid(row=0, column=4, sticky="w", padx=4, pady=4)
        self.inv_var = tk.IntVar(value=1)
        ttk.Spinbox(form, from_=1, to=75, textvariable=self.inv_var, width=6).grid(
            row=0, column=5, padx=4, pady=4
        )

        ttk.Label(form, text="Generate Inverters").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.inv_range_var = tk.StringVar(value="")
        ttk.Entry(form, textvariable=self.inv_range_var, width=24).grid(
            row=1, column=1, columnspan=3, sticky="w", padx=4, pady=4
        )
        ttk.Label(form, text="e.g. 1-5, 8-10, 33 (blank = all)", foreground="#666").grid(
            row=1, column=4, columnspan=2, sticky="w", padx=4, pady=4
        )

        self._build_controls("Check Inverter Data", self._run)

    def _generate_kwargs_and_kind(self):
        try:
            inv_nums = parse_inverter_range(self.inv_range_var.get())
        except ValueError as exc:
            messagebox.showwarning("Invalid inverter range", str(exc))
            return None, None
        kind = f"inverters {', '.join(str(n) for n in inv_nums)}" if inv_nums else "all inverters"
        return {"invNums": inv_nums}, kind

    def _run(self):
        year = self.year_var.get().strip()
        if not valid_year(year):
            messagebox.showwarning("Invalid year", "Enter a 4-digit year (e.g. 2025).")
            return
        month = self.month_var.get()
        inv = self.inv_var.get()

        def work_fn():
            module, import_error = get_data_request_module()
            if import_error:
                raise RuntimeError(
                    f"Automatic_Data_Request_Multiple_Files failed to import: {import_error}"
                )
            instance = module.DataPull()
            instance.cancel_event = self._cancel_event
            instance.seeNoAndLowDataDaysInv(month, year, inv)
            self._data_pull = instance

        self.start_run(work_fn, on_success=lambda: self.generate_button.configure(state="normal"))


class IrradianceCheckFrame(CheckFrame):
    def __init__(self, parent):
        super().__init__(parent, "No/Low Data Days -- Irradiance", is_inverter=False)

        form = ttk.Frame(self, padding=8)
        form.pack(fill="x")

        ttk.Label(form, text="Month").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.month_var = tk.StringVar(value=MONTHS[0])
        ttk.Combobox(
            form, textvariable=self.month_var, values=MONTHS, state="readonly", width=6
        ).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(form, text="Year").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.year_var = tk.StringVar(value="2025")
        ttk.Entry(form, textvariable=self.year_var, width=8).grid(row=0, column=3, padx=4, pady=4)

        self._build_controls("Check Irradiance Data", self._run)

    def _run(self):
        year = self.year_var.get().strip()
        if not valid_year(year):
            messagebox.showwarning("Invalid year", "Enter a 4-digit year (e.g. 2025).")
            return
        month = self.month_var.get()

        def work_fn():
            module, import_error = get_data_request_module()
            if import_error:
                raise RuntimeError(
                    f"Automatic_Data_Request_Multiple_Files failed to import: {import_error}"
                )
            instance = module.DataPull()
            instance.cancel_event = self._cancel_event
            instance.seeNoAndLowDataDaysIrradiance(month, year)
            self._data_pull = instance

        self.start_run(work_fn, on_success=lambda: self.generate_button.configure(state="normal"))


def main():
    root = tk.Tk()
    root.title("Pull Data - No/Low Data Day Checker")
    root.geometry("700x650")

    ttk.Style().theme_use("clam")

    outer = ttk.Frame(root, padding=10)
    outer.pack(fill="both", expand=True)

    InverterCheckFrame(outer).pack(fill="both", expand=True, pady=(0, 10))
    IrradianceCheckFrame(outer).pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
