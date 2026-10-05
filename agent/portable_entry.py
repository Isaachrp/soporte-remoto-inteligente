from agent.app.main import main
import sys

if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Agente detenido: revise configuracion y auditoria; no reintente escrituras.',file=sys.stderr)
        sys.exit(1)
