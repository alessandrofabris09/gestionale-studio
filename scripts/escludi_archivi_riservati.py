"""Esclude dall'indice Git quattro archivi riservati, conservandone copie locali.

Non crea commit, non effettua push e non riscrive la cronologia.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ['db.sqlite3', 'db_vecchio.sqlite3', 'backup_render.json', 'dati_backup.json']

def git(*args):
    return subprocess.run(['git', '-c', 'safe.directory=' + ROOT.as_posix(), '-C', str(ROOT), *args], capture_output=True, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    # Non aggiungere automaticamente eccezioni globali o operare in altri repository.
    top = Path(git('rev-parse', '--show-toplevel').stdout.decode().strip()).resolve()
    if top != ROOT.resolve():
        raise SystemExit('Cartella repository non corrispondente: operazione interrotta.')
    git('check-ignore', '--', '.local-test/verifica-esclusione')
    tracked = git('ls-files', '-z', '--', *TARGETS).stdout.decode().split('\0')
    tracked = [name for name in tracked if name]
    if not tracked:
        print('Gli archivi sono gia esclusi dall\'indice Git.')
        return
    if not set(tracked).issubset(TARGETS):
        raise SystemExit('Percorsi inattesi: operazione interrotta.')
    backup = ROOT / '.local-test' / ('archivi-git-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(parents=True, exist_ok=False)
    for name in tracked:
        source = ROOT / name
        if source.is_file():
            shutil.copy2(source, backup / name)
        else:
            # Recupera anche il db.sqlite3 gia mancante dalla copia di lavoro.
            (backup / name).write_bytes(git('show', 'HEAD:' + name).stdout)
    print('Copie di sicurezza conservate in:', backup)
    if args.prepare_only:
        print('Preparazione completata; indice Git non modificato.')
        return
    try:
        git('rm', '--cached', '--ignore-unmatch', '--', *tracked)
    except subprocess.CalledProcessError:
        raise SystemExit('Git non ha modificato l\'indice. Verifica i permessi o eventuali modifiche gia in staging. Le copie sono al sicuro; non e stato usato --force.')
    remaining = git('ls-files', '-z', '--', *TARGETS).stdout
    if remaining:
        raise SystemExit('Verifica non riuscita: alcuni archivi sono ancora tracciati.')
    print('Archivi esclusi dall\'indice. File locali conservati; nessun commit o push.')

if __name__ == '__main__':
    main()
