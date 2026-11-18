from agent.app.main import main
import sys

if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            from agent.app.gui import main as gui_main
            gui_main()
        else:
            main()
    except Exception:
        print('Agente detenido: revise configuracion y auditoria; no reintente escrituras.',file=sys.stderr)
        sys.exit(1)
