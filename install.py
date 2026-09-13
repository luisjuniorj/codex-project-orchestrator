#!/usr/bin/env python3
"""Install a project-scoped Codex configuration. Never calls a model or the network."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ é necessário.")

import tomllib

try:
    import tomlkit
except ImportError:
    raise SystemExit("Dependência ausente. Execute: python -m pip install -r requirements.txt")

VERSION = "0.3.0"
TOOL = "codex-project-orchestrator"
INSTALL_PROFILE = "orchestration"
# Kept only so intact 0.1/0.2 installations can still be inspected, upgraded,
# and uninstalled. New installations expose a single configuration.
LEGACY_STATE_MODES = frozenset({"orchestration", "everyday", "economy"})
PRIMARY_CONFIG = ("gpt-5.6-sol", "max", True)
MAX_CONCURRENT_THREADS = 8
TEMPLATES = Path(__file__).resolve().parent / "templates"
STATE_DIR = ".codex/.project-orchestrator"
STATE_FILE = f"{STATE_DIR}/state.json"
LOCK_FILE = f"{STATE_DIR}/install.lock"
CONFIG = ".codex/config.toml"
IGNORE = ".codex/.gitignore"
ROLES = {
    "cpo_explorer": ("gpt-5.6-luna", "max"),
    "cpo_worker": ("gpt-5.6-luna", "max"),
    "cpo_investigator": ("gpt-5.6-luna", "max"),
    "cpo_reviewer": ("gpt-6-astra", "max"),
}
AGENT_FILES = {f".codex/agents/{name}.toml" for name in ROLES}
ALLOWED_FILES = AGENT_FILES | {CONFIG, IGNORE, "AGENTS.md", "AGENTS.override.md"}
POLICY_BEGIN = "<!-- codex-project-orchestrator:begin -->"
POLICY_END = "<!-- codex-project-orchestrator:end -->"
IGNORE_BEGIN = "# codex-project-orchestrator:begin"
IGNORE_END = "# codex-project-orchestrator:end"


class InstallError(Exception):
    """An actionable preflight or transaction failure."""


@dataclass(frozen=True)
class Snapshot:
    content: bytes | None
    mode: int = 0o644


@dataclass(frozen=True)
class Change:
    relative: str
    before: Snapshot
    after: Snapshot


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def project_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    home = Path.home().resolve()
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser().resolve()
    if not root.is_dir():
        raise InstallError("--project deve apontar para uma pasta de projeto existente.")
    if root == Path(root.anchor) or root == home or root.is_relative_to(codex_home):
        raise InstallError("Escolha um projeto; a raiz do sistema, a pasta pessoal e CODEX_HOME não são destinos permitidos.")
    if root.name == ".codex":
        raise InstallError("Informe a raiz do projeto, não sua pasta .codex.")
    return root


def local_path(root: Path, relative: str) -> Path:
    """Validate a typed relative path and reject links in every existing component."""
    rel = PurePosixPath(relative)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts or "\\" in relative:
        raise InstallError("Caminho inválido nos metadados da instalação.")
    path = root
    for index, part in enumerate(rel.parts):
        path = path / part
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        is_junction = getattr(path, "is_junction", lambda: False)()
        is_reparse_point = bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        if stat.S_ISLNK(info.st_mode) or is_junction or is_reparse_point:
            raise InstallError(f"Link ou junction não permitido no destino: {relative}")
        if index < len(rel.parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise InstallError(f"Um componente do caminho não é uma pasta: {relative}")
        if stat.S_ISREG(info.st_mode) and info.st_nlink > 1:
            raise InstallError(f"Arquivo com hard links não permitido: {relative}")
    return path


def snapshot(root: Path, relative: str) -> Snapshot:
    path = local_path(root, relative)
    if not path.exists():
        return Snapshot(None)
    if not path.is_file():
        raise InstallError(f"Era esperado um arquivo: {relative}")
    return Snapshot(path.read_bytes(), stat.S_IMODE(path.stat().st_mode))


def same(left: Snapshot, right: Snapshot) -> bool:
    return left.content == right.content and (
        left.content is None or os.name == "nt" or left.mode == right.mode
    )


def mkdirs(root: Path, path: Path, created: list[Path]) -> None:
    missing = []
    while path != root and not path.exists():
        missing.append(path)
        path = path.parent
    for directory in reversed(missing):
        local_path(root, directory.relative_to(root).as_posix())
        directory.mkdir(mode=0o700 if ".project-orchestrator" in directory.parts else 0o755)
        created.append(directory)


def atomic_write(root: Path, relative: str, value: Snapshot, created: list[Path]) -> None:
    path = local_path(root, relative)
    if value.content is None:
        path.unlink(missing_ok=True)
        return
    mkdirs(root, path.parent, created)
    descriptor, temporary = tempfile.mkstemp(prefix=".cpo-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(value.content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, value.mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def remove_empty(directories: list[Path]) -> None:
    for directory in sorted(set(directories), key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


@contextmanager
def project_lock(root: Path):
    created: list[Path] = []
    lock = local_path(root, LOCK_FILE)
    mkdirs(root, lock.parent, created)
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        remove_empty(created)
        raise InstallError("Há um install.lock. Aguarde a outra execução; consulte a documentação se ela foi interrompida.")
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink(missing_ok=True)
        remove_empty(created)


def commit(root: Path, changes: list[Change]) -> None:
    """Atomically replace each file and roll back completed writes on normal failures."""
    written: list[Change] = []
    created: list[Path] = []
    try:
        for change in changes:
            if not same(snapshot(root, change.relative), change.before):
                raise InstallError(f"Arquivo mudou durante a operação: {change.relative}")
            if same(change.before, change.after):
                continue
            atomic_write(root, change.relative, change.after, created)
            written.append(change)
    except BaseException as error:
        failed = []
        for change in reversed(written):
            if failed and change.before.content is None and PurePosixPath(change.relative).is_relative_to(STATE_DIR):
                # Retain new recovery data if a project file could not be restored.
                continue
            try:
                if not same(snapshot(root, change.relative), change.after):
                    failed.append(change.relative)
                    continue
                atomic_write(root, change.relative, change.before, created)
            except OSError:
                failed.append(change.relative)
        remove_empty(created)
        if failed:
            raise InstallError("Rollback incompleto; preserve os backups e confira: " + ", ".join(failed)) from error
        raise


def original_path(relative: str) -> str:
    if relative not in ALLOWED_FILES:
        raise InstallError("Arquivo desconhecido no manifesto de instalação.")
    return f"{STATE_DIR}/original/{relative}"


def load_state(root: Path) -> dict | None:
    raw = snapshot(root, STATE_FILE).content
    if raw is None:
        return None
    try:
        state = json.loads(raw)
        if state["schema"] != 1 or state["tool"] != TOOL or state["mode"] not in LEGACY_STATE_MODES:
            raise ValueError("schema")
        if state["instructions"] not in {"AGENTS.md", "AGENTS.override.md"}:
            raise ValueError("instructions")
        expected = AGENT_FILES | {CONFIG, IGNORE, state["instructions"]}
        if set(state["files"]) != expected:
            raise ValueError("files")
        if not isinstance(state["created_dirs"], list) or not set(state["created_dirs"]) <= {".codex", ".codex/agents"}:
            raise ValueError("directories")
        for relative, entry in state["files"].items():
            if type(entry["existed"]) is not bool:
                raise ValueError("existed")
            for key in ("original_mode", "installed_mode"):
                if type(entry[key]) is not int or not 0 <= entry[key] <= 0o777:
                    raise ValueError("mode")
            for key in ("installed_sha256",):
                if not isinstance(entry[key], str) or len(entry[key]) != 64:
                    raise ValueError("digest")
            if entry["existed"]:
                backup = snapshot(root, original_path(relative)).content
                if backup is None or digest(backup) != entry["original_sha256"]:
                    raise InstallError(f"Backup ausente ou alterado: {relative}")
        return state
    except (KeyError, TypeError, ValueError) as error:
        raise InstallError("Metadados inválidos. Preserve .codex/.project-orchestrator e consulte a recuperação manual.") from error


def original(root: Path, state: dict, relative: str) -> Snapshot:
    entry = state["files"][relative]
    data = snapshot(root, original_path(relative)).content if entry["existed"] else None
    return Snapshot(data, entry["original_mode"])


def drift(root: Path, state: dict) -> list[str]:
    changed = []
    for relative, entry in state["files"].items():
        current = snapshot(root, relative)
        if current.content is None or digest(current.content) != entry["installed_sha256"]:
            changed.append(relative)
        elif os.name != "nt" and current.mode != entry["installed_mode"]:
            changed.append(relative)
    return changed


def instructions_file(root: Path) -> str:
    override = snapshot(root, "AGENTS.override.md").content
    return "AGENTS.override.md" if override is not None and override.strip() else "AGENTS.md"


def append_block(data: bytes | None, body: str, begin: str, end: str) -> bytes:
    """Append a delimited installer block, without interpreting human instructions."""
    text = (data or b"").decode("utf-8")
    if begin in text or end in text:
        raise InstallError("Já existe um bloco deste instalador sem um estado correspondente. Confira a instalação manual.")
    newline = "\r\n" if "\r\n" in text else "\n"
    separator = "" if not text or text.endswith(newline * 2) else newline if text.endswith(newline) else newline * 2
    block = newline.join([begin, body.strip().replace("\r\n", "\n").replace("\n", newline), end, ""])
    return (text + separator + block).encode("utf-8")


def render_config(data: bytes | None) -> bytes:
    try:
        document = tomlkit.parse((data or b"").decode("utf-8"))
    except (ValueError, tomlkit.exceptions.ParseError) as error:
        raise InstallError("O config.toml existente não é um TOML UTF-8 válido.") from error
    if "agents" not in document:
        document["agents"] = tomlkit.table()
    agents = document["agents"]
    if not isinstance(agents, Mapping):
        raise InstallError("A chave agents precisa ser uma tabela TOML.")
    if set(agents) & set(ROLES):
        raise InstallError("Há papéis cpo_* declarados em [agents]. Resolva essa colisão antes de instalar.")
    model, effort, enabled = PRIMARY_CONFIG
    document["model"] = model
    document["model_reasoning_effort"] = effort
    agents["enabled"] = enabled
    agents.pop("max_threads", None)  # Native legacy alias for the same controlled limit.
    agents["max_concurrent_threads_per_session"] = MAX_CONCURRENT_THREADS
    agents["default_subagent_model"] = "gpt-5.6-luna"
    agents["default_subagent_reasoning_effort"] = "max"
    result = tomlkit.dumps(document).encode("utf-8")
    parsed = tomllib.loads(result.decode("utf-8"))
    parsed_agents = parsed["agents"]
    if (
        parsed["model"] != model
        or parsed["model_reasoning_effort"] != effort
        or parsed_agents["enabled"] is not enabled
        or parsed_agents["max_concurrent_threads_per_session"] != MAX_CONCURRENT_THREADS
        or parsed_agents["default_subagent_reasoning_effort"] != "max"
    ):
        raise InstallError("Falha ao validar a configuração gerada.")
    return result


def role_templates() -> dict[str, bytes]:
    files = {}
    for name, (model, effort) in ROLES.items():
        data = (TEMPLATES / "agents" / f"{name}.toml").read_bytes()
        try:
            parsed = tomllib.loads(data.decode("utf-8"))
        except (ValueError, UnicodeError) as error:
            raise InstallError(f"Template TOML inválido: {name}") from error
        if parsed.get("name") != name or parsed.get("model") != model or parsed.get("model_reasoning_effort") != effort:
            raise InstallError(f"Template incompatível com a política de modelos: {name}")
        if not parsed.get("description") or not parsed.get("developer_instructions"):
            raise InstallError(f"Template incompleto: {name}")
        files[f".codex/agents/{name}.toml"] = data
    return files


def check_other_agents(root: Path) -> None:
    folder = local_path(root, ".codex/agents")
    if folder.exists() and not folder.is_dir():
        raise InstallError(".codex/agents precisa ser uma pasta.")
    if not folder.exists():
        return
    for path in folder.glob("*.toml"):
        relative = path.relative_to(root).as_posix()
        if relative in AGENT_FILES:
            continue
        try:
            content = snapshot(root, relative).content
            if content is None:
                raise InstallError(f"Agente mudou durante a inspeção: {relative}")
            parsed = tomllib.loads(content.decode("utf-8"))
        except (ValueError, UnicodeError) as error:
            raise InstallError(f"Agente existente inválido: {relative}") from error
        if not isinstance(parsed.get("name"), str):
            raise InstallError(f"Agente existente sem nome válido: {relative}")
        if parsed.get("name") in ROLES:
            raise InstallError(f"Nome de agente cpo_* já utilizado em {relative}")


def installation_plan(root: Path, missing_dirs: list[str]) -> tuple[list[Change], list[str]]:
    state = load_state(root)
    instruction = instructions_file(root)
    if state:
        changed = drift(root, state)
        if changed:
            raise InstallError("Arquivos alterados após a instalação; nada foi sobrescrito: " + ", ".join(changed))
        if state["instructions"] != instruction:
            raise InstallError("O arquivo de instruções ativo mudou. Reverta essa mudança ou faça a recuperação manual antes de reinstalar.")
    check_other_agents(root)
    roles = role_templates()
    managed = [CONFIG, instruction, IGNORE, *sorted(roles)]
    current = {relative: snapshot(root, relative) for relative in managed}
    if state is None:
        collisions = [relative for relative in roles if current[relative].content is not None]
        if collisions:
            raise InstallError("Agentes de destino já existem sem estado deste instalador: " + ", ".join(collisions))
    originals = {relative: original(root, state, relative) if state else current[relative] for relative in managed}
    desired = {
        CONFIG: render_config(current[CONFIG].content),
        instruction: append_block(originals[instruction].content, (TEMPLATES / "policy.md").read_text(encoding="utf-8"), POLICY_BEGIN, POLICY_END),
        IGNORE: append_block(originals[IGNORE].content, "/.project-orchestrator/", IGNORE_BEGIN, IGNORE_END),
        **roles,
    }
    changes: list[Change] = []
    entries = {}
    # Write recovery data before modifying any project instruction or configuration.
    for relative in managed:
        prior = originals[relative]
        if prior.content is not None and state is None:
            backup_relative = original_path(relative)
            before_backup = snapshot(root, backup_relative)
            if before_backup.content is not None:
                raise InstallError("Há backups sem manifesto. Consulte a recuperação manual antes de continuar.")
            changes.append(Change(backup_relative, before_backup, Snapshot(prior.content, 0o600)))
        after = Snapshot(desired[relative], current[relative].mode)
        entries[relative] = {
            "existed": prior.content is not None,
            "original_mode": prior.mode,
            "original_sha256": digest(prior.content) if prior.content is not None else None,
            "installed_sha256": digest(after.content),
            "installed_mode": after.mode,
        }
    changes.extend(Change(relative, current[relative], Snapshot(desired[relative], current[relative].mode)) for relative in managed)
    new_state = {
        "schema": 1, "tool": TOOL, "version": VERSION, "mode": INSTALL_PROFILE,
        "instructions": instruction, "files": entries,
        "created_dirs": state["created_dirs"] if state else missing_dirs,
    }
    changes.append(Change(STATE_FILE, snapshot(root, STATE_FILE), Snapshot((json.dumps(new_state, indent=2, sort_keys=True) + "\n").encode(), 0o600)))
    return [change for change in changes if not same(change.before, change.after)], managed


def describe(changes: list[Change], managed: list[str]) -> None:
    for change in changes:
        if change.relative not in managed:
            continue
        action = "remover" if change.after.content is None else "criar" if change.before.content is None else "atualizar"
        print(f"  {action}: {change.relative}")


def install(project: str | Path, *, dry_run: bool = False) -> int:
    root = project_root(project)
    missing = [rel for rel in (".codex", ".codex/agents") if not local_path(root, rel).exists()]
    if dry_run:
        if local_path(root, LOCK_FILE).exists():
            raise InstallError("Há uma operação em andamento ou um lock pendente.")
        changes, managed = installation_plan(root, missing)
        print(f"Prévia — {root}\nSol, Luna e Astra em max; até {MAX_CONCURRENT_THREADS} auxiliares. Nenhum arquivo será alterado.")
        describe(changes, managed)
        if changes:
            print(f"  estado e backups locais: {STATE_DIR}/")
        else:
            print("Configuração já está atualizada.")
        return 0
    with project_lock(root):
        changes, managed = installation_plan(root, missing)
        commit(root, changes)
        print(f"Projeto: {root}\nConfiguração de orquestração instalada; até {MAX_CONCURRENT_THREADS} auxiliares.")
        describe(changes, managed)
        print("Instalação concluída." if changes else "Configuração já está atualizada; nenhum arquivo gerenciado mudou.")
    return 0


def status(project: str | Path) -> int:
    root = project_root(project)
    if local_path(root, LOCK_FILE).exists():
        raise InstallError("Há uma operação em andamento ou um lock pendente.")
    state = load_state(root)
    if state is None:
        print("Sem instalação registrada neste projeto. Arquivos instalados manualmente não são registrados.")
        return 1
    changed = drift(root, state)
    if instructions_file(root) != state["instructions"]:
        changed.append("arquivo de instruções ativo")
    print(f"Projeto: {root}\nVersão instalada: {state.get('version', 'não registrada')}")
    if state["mode"] != INSTALL_PROFILE:
        print(f"Modo legado registrado: {state['mode']}")
    if changed:
        print("Divergências em disco: " + ", ".join(changed))
        return 2
    # Read the installed configuration: newer installer defaults do not describe
    # a project that has not yet been upgraded.
    config = tomllib.loads(snapshot(root, CONFIG).content.decode("utf-8"))
    model, effort = config["model"], config["model_reasoning_effort"]
    agents = config["agents"]
    helpers = f"habilitados; teto {agents['max_concurrent_threads_per_session']}" if agents["enabled"] else "desabilitados"
    print(f"Principal: {model} / {effort}\nAuxiliares: {helpers}\nLuna: max")
    if state.get("version") != VERSION:
        print(f"Instalador disponível: {VERSION}. Use install --dry-run para conferir a atualização.")
    print("Arquivos em disco conferem com a instalação. Isso não verifica a sessão ativa do Codex.")
    return 0


def uninstall(project: str | Path, dry_run: bool = False) -> int:
    root = project_root(project)

    def plan():
        state = load_state(root)
        if state is None:
            raise InstallError("Não há instalação registrada para restaurar.")
        changed = drift(root, state)
        if changed:
            raise InstallError("Desinstalação interrompida para preservar edições posteriores: " + ", ".join(changed))
        managed = list(state["files"])
        changes = [Change(rel, snapshot(root, rel), original(root, state, rel)) for rel in managed]
        for rel, entry in state["files"].items():
            if entry["existed"]:
                backup = original_path(rel)
                changes.append(Change(backup, snapshot(root, backup), Snapshot(None)))
        changes.append(Change(STATE_FILE, snapshot(root, STATE_FILE), Snapshot(None)))
        return state, changes, managed

    if dry_run:
        if local_path(root, LOCK_FILE).exists():
            raise InstallError("Há uma operação em andamento ou um lock pendente.")
        _, changes, managed = plan()
        print(f"Prévia de restauração — {root}. Nenhum arquivo será alterado.")
        describe(changes, managed)
        return 0
    with project_lock(root):
        state, changes, managed = plan()
        commit(root, changes)
        describe(changes, managed)
        cleanup = []
        for rel in state["files"]:
            folder = local_path(root, original_path(rel)).parent
            while folder != root / STATE_DIR:
                cleanup.append(folder)
                folder = folder.parent
        remove_empty(cleanup)
    remove_empty([root / STATE_DIR, *(root / rel for rel in state["created_dirs"])])
    print("Estado anterior à primeira instalação restaurado. Nenhuma configuração global foi alterada.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configuração de agentes Codex exclusivamente por projeto.")
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "status", "uninstall"):
        sub = commands.add_parser(command)
        sub.add_argument("--project", required=True, help="Pasta existente do projeto; nunca usa o diretório atual implicitamente.")
        if command != "status":
            sub.add_argument("--dry-run", action="store_true", help="Mostrar o plano sem gravar arquivos.")
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            return install(args.project, dry_run=args.dry_run)
        if args.command == "uninstall":
            return uninstall(args.project, args.dry_run)
        return status(args.project)
    except (InstallError, OSError, UnicodeError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
