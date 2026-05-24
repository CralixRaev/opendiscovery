import asyncio
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from nmap_scan import NmapScanError, NmapScanResult, scan_target


class ScannerGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("OpenDiscovery Scanner")
        self.minsize(820, 560)

        self._event_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._scan_thread: threading.Thread | None = None
        self._scan_result: NmapScanResult | None = None

        self.target_var = tk.StringVar(value="127.0.0.1/32")
        self.nmap_binary_var = tk.StringVar(value="nmap")
        self.status_var = tk.StringVar(value="Ready")
        self.summary_var = tk.StringVar(value="No scan results yet")

        self._build_ui()
        self.after(100, self._poll_events)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        controls = ttk.Frame(self, padding=(12, 12, 12, 8))
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=0)

        ttk.Label(controls, text="Target").grid(row=0, column=0, sticky="w", padx=(0, 8))
        target_entry = ttk.Entry(controls, textvariable=self.target_var)
        target_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        target_entry.bind("<Return>", lambda _event: self.start_scan())

        ttk.Label(controls, text="Nmap").grid(row=0, column=2, sticky="w", padx=(0, 8))
        ttk.Entry(controls, width=14, textvariable=self.nmap_binary_var).grid(
            row=0,
            column=3,
            sticky="ew",
            padx=(0, 12),
        )

        self.scan_button = ttk.Button(controls, text="Scan", command=self.start_scan)
        self.scan_button.grid(row=0, column=4, sticky="ew", padx=(0, 8))

        ttk.Button(controls, text="Clear", command=self.clear_results).grid(
            row=0,
            column=5,
            sticky="ew",
            padx=(0, 8),
        )
        self.save_button = ttk.Button(
            controls,
            text="Save JSON",
            command=self.save_result,
            state=tk.DISABLED,
        )
        self.save_button.grid(row=0, column=6, sticky="ew")

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))

        hosts_frame = ttk.Frame(body)
        hosts_frame.columnconfigure(0, weight=1)
        hosts_frame.rowconfigure(0, weight=1)
        body.add(hosts_frame, weight=3)

        self.hosts_tree = ttk.Treeview(
            hosts_frame,
            columns=("hostname", "ports"),
            show="tree headings",
            selectmode="browse",
        )
        self.hosts_tree.heading("#0", text="IP")
        self.hosts_tree.heading("hostname", text="Hostname")
        self.hosts_tree.heading("ports", text="Open ports")
        self.hosts_tree.column("#0", width=180, stretch=False)
        self.hosts_tree.column("hostname", width=220, stretch=True)
        self.hosts_tree.column("ports", width=220, stretch=True)
        self.hosts_tree.grid(row=0, column=0, sticky="nsew")
        self.hosts_tree.bind("<<TreeviewSelect>>", self._show_selected_host)

        hosts_scroll = ttk.Scrollbar(hosts_frame, orient=tk.VERTICAL, command=self.hosts_tree.yview)
        hosts_scroll.grid(row=0, column=1, sticky="ns")
        self.hosts_tree.configure(yscrollcommand=hosts_scroll.set)

        details_frame = ttk.Frame(body, padding=(12, 0, 0, 0))
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(1, weight=1)
        body.add(details_frame, weight=2)

        ttk.Label(details_frame, textvariable=self.summary_var).grid(row=0, column=0, sticky="ew")
        self.details_text = tk.Text(details_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        details_scroll = ttk.Scrollbar(
            details_frame,
            orient=tk.VERTICAL,
            command=self.details_text.yview,
        )
        details_scroll.grid(row=1, column=1, sticky="ns", pady=(8, 0))
        self.details_text.configure(yscrollcommand=details_scroll.set)

        status = ttk.Frame(self, padding=(12, 0, 12, 12))
        status.grid(row=2, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def start_scan(self) -> None:
        if self._scan_thread is not None and self._scan_thread.is_alive():
            return

        target = self.target_var.get().strip()
        nmap_binary = self.nmap_binary_var.get().strip() or "nmap"
        if not target:
            messagebox.showerror("Missing target", "Enter an IP address or CIDR network.")
            return

        self._set_scan_running(True)
        self.clear_results(reset_status=False)
        self.status_var.set(f"Scanning {target}...")

        self._scan_thread = threading.Thread(
            target=self._run_scan_worker,
            args=(target, nmap_binary),
            daemon=True,
        )
        self._scan_thread.start()

    def clear_results(self, *, reset_status: bool = True) -> None:
        self._scan_result = None
        for item_id in self.hosts_tree.get_children():
            self.hosts_tree.delete(item_id)
        self._set_details("")
        self.summary_var.set("No scan results yet")
        self.save_button.configure(state=tk.DISABLED)
        if reset_status:
            self.status_var.set("Ready")

    def save_result(self) -> None:
        if self._scan_result is None:
            return

        filename = filedialog.asksaveasfilename(
            title="Save scan result",
            initialfile="scan-result.json",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not filename:
            return

        Path(filename).write_text(
            json.dumps(_result_to_dict(self._scan_result), indent=2),
            encoding="utf-8",
        )
        self.status_var.set(f"Saved {filename}")

    def _run_scan_worker(self, target: str, nmap_binary: str) -> None:
        try:
            result = asyncio.run(scan_target(target, nmap_binary=nmap_binary))
        except (ValueError, NmapScanError) as exc:
            self._event_queue.put(("error", str(exc)))
        except Exception as exc:  # noqa: BLE001 - surface unexpected GUI worker failures.
            self._event_queue.put(("error", f"Unexpected scan error: {exc}"))
        else:
            self._event_queue.put(("result", result))

    def _poll_events(self) -> None:
        try:
            while True:
                event_name, payload = self._event_queue.get_nowait()
                if event_name == "result":
                    self._show_result(payload)
                elif event_name == "error":
                    self._show_error(str(payload))
        except queue.Empty:
            pass

        self.after(100, self._poll_events)

    def _show_result(self, result: object) -> None:
        if not isinstance(result, NmapScanResult):
            self._show_error("Scanner returned an invalid result.")
            return

        self._scan_result = result
        total_ports = sum(len(host.open_ports or []) for host in result.alive_hosts)
        self.summary_var.set(
            f"{len(result.alive_hosts)} alive host(s), {total_ports} open port(s)",
        )

        for host in result.alive_hosts:
            ports = ", ".join(
                f"{port.number}/{port.service_name}" for port in host.open_ports or []
            )
            item_id = self.hosts_tree.insert(
                "",
                tk.END,
                text=host.ip,
                values=(host.hostname or "", ports),
            )
            for port in host.open_ports or []:
                self.hosts_tree.insert(
                    item_id,
                    tk.END,
                    text=f"{port.number}/tcp",
                    values=(port.service_name, ""),
                )

        self._set_scan_running(False)
        self.save_button.configure(state=tk.NORMAL)
        self.status_var.set(f"Finished scan for {result.target}")

    def _show_error(self, message: str) -> None:
        self._set_scan_running(False)
        self.status_var.set("Scan failed")
        self._set_details(message)
        messagebox.showerror("Scan failed", message)

    def _show_selected_host(self, _event: tk.Event) -> None:
        if self._scan_result is None:
            return

        selected = self.hosts_tree.selection()
        if not selected:
            return

        item_id = selected[0]
        parent_id = self.hosts_tree.parent(item_id)
        host_ip = self.hosts_tree.item(parent_id or item_id, "text")
        host = next(
            (candidate for candidate in self._scan_result.alive_hosts if candidate.ip == host_ip),
            None,
        )
        if host is None:
            return

        lines = [f"IP: {host.ip}"]
        if host.hostname:
            lines.append(f"Hostname: {host.hostname}")
        lines.append("")
        lines.append("Open TCP ports:")
        if host.open_ports:
            lines.extend(f"- {port.number}: {port.service_name}" for port in host.open_ports)
        else:
            lines.append("- none")
        self._set_details("\n".join(lines))

    def _set_scan_running(self, is_running: bool) -> None:
        state = tk.DISABLED if is_running else tk.NORMAL
        self.scan_button.configure(state=state)

    def _set_details(self, value: str) -> None:
        self.details_text.configure(state=tk.NORMAL)
        self.details_text.delete("1.0", tk.END)
        if value:
            self.details_text.insert(tk.END, value)
        self.details_text.configure(state=tk.DISABLED)


def _result_to_dict(result: NmapScanResult) -> dict:
    return {
        "target": result.target,
        "alive_hosts": [
            {
                "ip": host.ip,
                "hostname": host.hostname,
                "open_ports": [
                    {
                        "number": port.number,
                        "service_name": port.service_name,
                    }
                    for port in host.open_ports or []
                ],
            }
            for host in result.alive_hosts
        ],
    }


def main() -> None:
    ScannerGui().mainloop()


if __name__ == "__main__":
    main()
