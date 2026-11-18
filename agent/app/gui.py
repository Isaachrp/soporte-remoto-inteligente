"""Portable read-only RouterOS diagnostic interface."""
import json
import queue
import threading
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from agent.app.router import NativeRouter
from shared.snapshot import Snapshot


class DiagnosticRouter:
    """Read-only interface over plain API; existing TLS executor is unchanged."""
    snapshot = NativeRouter.snapshot
    close = NativeRouter.close

    def __init__(self, host, username, password):
        from librouteros import connect
        self.api = connect(host=host, username=username, password=password, port=8728, timeout=5)


def collect(host, username, password, factory=DiagnosticRouter):
    router = factory(host, username, password)
    try:
        snapshot = Snapshot.model_validate(router.snapshot()).model_dump()
        return {'schema': 'router-diagnostic/1', 'created_at': datetime.now(timezone.utc).isoformat(),
                'read_only': True, 'mode': 'real', 'snapshot': snapshot}
    finally:
        router.close()


def main():
    root = tk.Tk()
    root.title('Soporte MikroTik · Diagnóstico del cliente')
    root.geometry('650x780')
    root.minsize(650, 780)
    root.configure(bg='#f4f4f4')
    root.option_add('*Font', 'Arial 11')
    panel = tk.Frame(root, bg='white', padx=30, pady=24)
    panel.pack(fill='both', expand=True, padx=24, pady=24)
    tk.Label(panel, text='Diagnóstico del MikroTik', bg='white', fg='#333', font=('Arial', 19, 'bold')).pack(anchor='w')
    tk.Label(panel, text='Conecta, consulta y guarda la información para el técnico.\nSolo lectura: no modifica la configuración del router.', bg='white', justify='left', wraplength=530).pack(anchor='w', pady=14)
    fields = {}
    for key, label in [('host', 'IP o nombre del router'), ('user', 'Usuario RouterOS'), ('password', 'Contraseña')]:
        tk.Label(panel, text=label, bg='white').pack(anchor='w', pady=(8, 4))
        value = tk.StringVar()
        entry = tk.Entry(panel, textvariable=value, show='*' if key == 'password' else '', bg='#f9f9f9', relief='solid', bd=1)
        entry.pack(fill='x', ipady=7)
        fields[key] = value
    tk.Label(panel, text='API RouterOS: TCP 8728, sin cifrado. Usa una red local\nconfiable o VPN. No requiere certificado ni servidor central.', bg='white', justify='left').pack(anchor='w', pady=8)
    status = tk.StringVar(value='Introduce los datos de conexión.')
    tk.Label(panel, textvariable=status, bg='#edf6ed', fg='#333', wraplength=520, justify='left', padx=12, pady=12).pack(fill='x', pady=8)
    events = queue.Queue()
    report = None
    def worker(values):
        try:
            events.put(('ok', collect(*values)))
        except Exception:
            events.put(('error', None))
    def diagnose():
        nonlocal report
        report = None
        save.configure(state='disabled')
        host, user, password = [fields[k].get().strip() if k != 'password' else fields[k].get() for k in ('host', 'user', 'password')]
        if not all((host, user, password)):
            status.set('Completa IP, usuario y contraseña.')
            return
        fields['password'].set('')
        connect.configure(state='disabled')
        status.set('Consultando identidad, versión y tablas de configuración…')
        threading.Thread(target=worker, args=((host, user, password),), daemon=True).start()
    def poll():
        nonlocal report
        try:
            kind, data = events.get_nowait()
            connect.configure(state='normal')
            if kind == 'ok':
                report = data
                status.set('Diagnóstico completo: ' + data['snapshot']['identity'] + ' · RouterOS ' + data['snapshot']['version'] + '. Ya puedes guardar el JSON.')
                save.configure(state='normal')
            else:
                status.set('No se pudo completar el diagnóstico. Revisa IP, usuario, contraseña, permisos y acceso a API 8728. No se generó un informe incompleto.')
        except queue.Empty:
            pass
        root.after(150, poll)
    def export():
        if report is None:
            return
        path = filedialog.asksaveasfilename(title='Guardar diagnóstico para el servidor', initialfile='diagnostico-router.json', defaultextension='.json', filetypes=[('JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
                status.set('JSON guardado. Entrégalo al técnico para cargarlo en el sistema central.')
            except OSError:
                messagebox.showerror('No se pudo guardar', 'Selecciona una carpeta con permiso de escritura.')
    connect = tk.Button(panel, text='Conectar y diagnosticar', command=diagnose, bg='#4caf50', fg='white', relief='flat', pady=10)
    connect.pack(fill='x', pady=5)
    save = tk.Button(panel, text='Guardar diagnóstico JSON', command=export, state='disabled', bg='#4caf50', fg='white', relief='flat', pady=10)
    save.pack(fill='x', pady=5)
    root.after(150, poll)
    root.mainloop()

if __name__ == '__main__':
    main()
