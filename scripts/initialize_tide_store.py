"""Initialize persistent observation tables; no synthetic observations."""
from services.orchestrator.tide_store import initialize

if __name__ == '__main__':
    initialize()
    print('KHOA tide storage initialized')
