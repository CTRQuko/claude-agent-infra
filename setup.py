#!/usr/bin/env python3
"""
setup.py — claude-agent-infra
Crea usuario restringido para Claude Code en entornos Debian-based.
Compatible: Proxmox VE / Debian / Ubuntu / Docker host
Requiere: root
"""

import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path

# ─── COLORES ──────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def ok(msg): print(f"{GREEN}✅ {msg}{RESET}")
def err(msg): print(f"{RED}❌ {msg}{RESET}")
def warn(msg): print(f"{YELLOW}⚠️  {msg}{RESET}")
def info(msg): print(f"{CYAN}→  {msg}{RESET}")

# ─── IDIOMA ───────────────────────────────────────────────────────────────────

LANG = "ES"

T = {
    "ES": {
        "header_title":     "claude-agent-infra — Setup usuario restringido",
        "header_compat":    "Compatible: Proxmox VE / Debian / Ubuntu / Docker",
        "lang_prompt":      "Selecciona idioma / Select language [1-2]: ",
        "s1_title":         "VERIFICACIÓN DEL ENTORNO",
        "s1_checking":      "Verificando herramientas mínimas necesarias:",
        "s1_all_ok":        "Todas las herramientas están disponibles.",
        "s1_missing":       "Faltan las siguientes herramientas:",
        "s1_install_ask":   "¿Instalar automáticamente con apt? [s/N]: ",
        "s1_install_abort": "Instalación cancelada. Instala las herramientas manualmente y vuelve a ejecutar el script.",
        "s1_installed":     "Herramientas instaladas correctamente.",
        "s1_tool_sudo":     "paquete sudo (visudo, sudoers)",
        "s1_tool_useradd":  "gestión de usuarios",
        "s1_tool_ssh":      "generación de claves SSH",
        "s2_title":         "ENTORNO DE DESTINO",
        "s2_detected":      "Entorno detectado:",
        "s2_confirm":       "¿Confirmar entorno?",
        "s2_opts":          ["Proxmox VE", "Debian/Ubuntu base", "Docker host"],
        "s3_title":         "USUARIO RESTRINGIDO",
        "s3_prompt":        "Nombre de usuario restringido",
        "s3_exists":        "El usuario '{u}' ya existe.",
        "s3_exists2":       "Se configurará SSH y sudoers en su home existente: {h}",
        "s3_created":       "Usuario '{u}' creado con home {h}",
        "s4_title":         "USUARIO ADMINISTRADOR  (opcional)",
        "s4_info1":         "Usuario administrador con sudo total",
        "s4_info2":         "  → Introduce un usuario existente (se añadirá sudo + SSH)",
        "s4_info3":         "  → O un nombre nuevo (se creará con sudo total)",
        "s4_prompt":        "Nombre de usuario admin [ENTER para omitir]",
        "s4_exists":        "El usuario '{u}' ya existe.",
        "s4_exists2":       "Se configurará sudo en su home existente: /home/{u}",
        "s4_has_key":       "'{u}' ya tiene clave SSH configurada.",
        "s4_has_key2":      "Recuerda usar esa clave para conectarte como '{u}'.",
        "s4_created":       "Usuario admin '{u}' creado.",
        "s5_title":         "CLAVES SSH",
        "s5_cfg":           "Configurando clave SSH para usuario '{u}':",
        "s5_gen_choice":    "¿Generar nueva clave o añadir existente?",
        "s5_gen_opts":      ["Generar nueva clave ed25519", "Añadir clave pública existente"],
        "s5_keydir":        "Directorio para guardar las claves",
        "s5_key_exists":    "La clave '{k}' ya existe — se sobreescribirá.",
        "s5_priv":          "Clave privada: {k}",
        "s5_pub":           "Clave pública: {k}",
        "s5_copy":          "Copia la clave privada a tu máquina: {k}",
        "s5_add_hint":      "  Opciones: ruta al fichero .pub o pegar la clave directamente",
        "s5_add_prompt":    "Ruta al fichero .pub o clave pública: ",
        "s5_add_empty":     "No introdujiste nada. Introduce una ruta a fichero .pub o pega la clave directamente.",
        "s5_add_dir":       "'{e}' es un directorio, no un fichero. Introduce la ruta completa al fichero .pub.",
        "s5_add_invalid":   "Formato de clave pública no válido. Debe empezar por ssh-ed25519, ssh-rsa o ecdsa-sha2.",
        "s5_add_ok":        "Clave pública validada.",
        "s5_installed":     "Clave instalada en {k}",
        "sudoers_gen":      "Generando y validando sudoers...",
        "sudoers_ok":       "Sudoers aplicado: {f}",
        "sudoers_err":      "El fichero sudoers no pasó la validación de visudo:",
        "sudoers_exc":      "Error aplicando sudoers: {e}",
        "sudoers_admin":    "Sudoers admin aplicado para '{u}'.",
        "cmd_fail":         "Comando falló: {c}",
        "verify_title":     "VERIFICACIÓN FINAL",
        "verify_user":      "Usuario {u}:",
        "verify_ssh":       "SSH authorized_keys:",
        "verify_sudoers":   "Sudoers (primeras 5 líneas):",
        "done_title":       "INSTALACIÓN COMPLETA",
        "done_connect":     "Prueba conexión desde tu máquina:",
        "done_warn":        "Recuerda copiar la clave privada a tu máquina antes de borrar el directorio de claves.",
        "cancelled":        "Instalación cancelada.",
        "invalid_opt":      "Opción no válida, intenta de nuevo.",
    },
    "EN": {
        "header_title":     "claude-agent-infra — Restricted user setup",
        "header_compat":    "Compatible: Proxmox VE / Debian / Ubuntu / Docker",
        "lang_prompt":      "Selecciona idioma / Select language [1-2]: ",
        "s1_title":         "ENVIRONMENT CHECK",
        "s1_checking":      "Checking required tools:",
        "s1_all_ok":        "All tools are available.",
        "s1_missing":       "The following tools are missing:",
        "s1_install_ask":   "Install automatically with apt? [y/N]: ",
        "s1_install_abort": "Installation cancelled. Install the tools manually and re-run the script.",
        "s1_installed":     "Tools installed successfully.",
        "s1_tool_sudo":     "sudo package (visudo, sudoers)",
        "s1_tool_useradd":  "user management",
        "s1_tool_ssh":      "SSH key generation",
        "s2_title":         "TARGET ENVIRONMENT",
        "s2_detected":      "Detected environment:",
        "s2_confirm":       "Confirm environment?",
        "s2_opts":          ["Proxmox VE", "Debian/Ubuntu base", "Docker host"],
        "s3_title":         "RESTRICTED USER",
        "s3_prompt":        "Restricted username",
        "s3_exists":        "User '{u}' already exists.",
        "s3_exists2":       "SSH and sudoers will be configured in existing home: {h}",
        "s3_created":       "User '{u}' created with home {h}",
        "s4_title":         "ADMIN USER  (optional)",
        "s4_info1":         "Admin user with full sudo access",
        "s4_info2":         "  → Enter an existing user (sudo + SSH will be added)",
        "s4_info3":         "  → Or a new name (will be created with full sudo)",
        "s4_prompt":        "Admin username [ENTER to skip]",
        "s4_exists":        "User '{u}' already exists.",
        "s4_exists2":       "sudo will be configured in existing home: /home/{u}",
        "s4_has_key":       "'{u}' already has an SSH key configured.",
        "s4_has_key2":      "Remember to use that key to connect as '{u}'.",
        "s4_created":       "Admin user '{u}' created.",
        "s5_title":         "SSH KEYS",
        "s5_cfg":           "Configuring SSH key for user '{u}':",
        "s5_gen_choice":    "Generate new key or add existing?",
        "s5_gen_opts":      ["Generate new ed25519 key", "Add existing public key"],
        "s5_keydir":        "Directory to save the keys",
        "s5_key_exists":    "Key '{k}' already exists — it will be overwritten.",
        "s5_priv":          "Private key: {k}",
        "s5_pub":           "Public key: {k}",
        "s5_copy":          "Copy the private key to your machine: {k}",
        "s5_add_hint":      "  Options: path to .pub file or paste the key directly",
        "s5_add_prompt":    "Path to .pub file or public key: ",
        "s5_add_empty":     "Nothing entered. Provide a path to a .pub file or paste the key directly.",
        "s5_add_dir":       "'{e}' is a directory, not a file. Enter the full path to the .pub file.",
        "s5_add_invalid":   "Invalid public key format. Must start with ssh-ed25519, ssh-rsa or ecdsa-sha2.",
        "s5_add_ok":        "Public key validated.",
        "s5_installed":     "Key installed in {k}",
        "sudoers_gen":      "Generating and validating sudoers...",
        "sudoers_ok":       "Sudoers applied: {f}",
        "sudoers_err":      "Sudoers file failed visudo validation:",
        "sudoers_exc":      "Error applying sudoers: {e}",
        "sudoers_admin":    "Admin sudoers applied for '{u}'.",
        "cmd_fail":         "Command failed: {c}",
        "verify_title":     "FINAL VERIFICATION",
        "verify_user":      "User {u}:",
        "verify_ssh":       "SSH authorized_keys:",
        "verify_sudoers":   "Sudoers (first 5 lines):",
        "done_title":       "SETUP COMPLETE",
        "done_connect":     "Test the connection from your machine:",
        "done_warn":        "Remember to copy the private key to your machine before deleting the keys directory.",
        "cancelled":        "Installation cancelled.",
        "invalid_opt":      "Invalid option, try again.",
    },
}

def t(key, **kwargs):
    """Devuelve cadena traducida al idioma activo."""
    s = T[LANG].get(key, key)
    return s.format(**kwargs) if kwargs else s

# ─── UTILIDADES ───────────────────────────────────────────────────────────────

def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        err(t("cmd_fail", c=cmd))
        err(result.stderr.strip())
        sys.exit(1)
    return result

def ask(prompt, default=None):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def ask_choice(prompt, options):
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        try:
            choice = int(input(f"{prompt} [1-{len(options)}]: ").strip())
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        warn(t("invalid_opt"))

def select_language():
    global LANG
    print()
    print("  1. Español")
    print("  2. English")
    while True:
        try:
            choice = int(input(t("lang_prompt")).strip())
            if choice in (1, 2):
                LANG = "ES" if choice == 1 else "EN"
                return
        except ValueError:
            pass

# ─── DEPENDENCIAS ─────────────────────────────────────────────────────────────

def required_tools():
    return [
        ("sudo",       "sudo",          t("s1_tool_sudo")),
        ("useradd",    "passwd",        t("s1_tool_useradd")),
        ("ssh-keygen", "openssh-client",t("s1_tool_ssh")),
    ]

def check_and_install_deps():
    tools = required_tools()
    missing = [(b, p, d) for b, p, d in tools if not shutil.which(b)]

    print()
    info(t("s1_checking"))
    print()
    for binary, pkg, desc in tools:
        found = shutil.which(binary) is not None
        status = f"{GREEN}✅ {RESET}" if found else f"{RED}❌ {RESET}"
        print(f"  {status} {binary:15s} — {desc}")
    print()

    if not missing:
        ok(t("s1_all_ok"))
        return

    print()
    warn(t("s1_missing"))
    for binary, pkg, desc in missing:
        print(f"  ❌  {binary} ({pkg}) — {desc}")
    print()
    confirm = input(t("s1_install_ask")).strip().lower()
    if confirm not in ("s", "si", "sí", "y", "yes"):
        err(t("s1_install_abort"))
        sys.exit(1)

    run("apt-get update -qq")
    pkgs = " ".join(p for _, p, _ in missing)
    run(f"apt-get install -y {pkgs}")
    ok(t("s1_installed"))

# ─── DETECCIÓN OS ─────────────────────────────────────────────────────────────

def detect_os():
    is_proxmox = Path("/usr/sbin/pct").exists() or Path("/usr/sbin/qm").exists()
    is_docker = shutil.which("docker") is not None
    if is_proxmox:
        return "proxmox"
    if is_docker:
        return "docker"
    return "debian"

# ─── WHITELIST SUDOERS ────────────────────────────────────────────────────────

def build_sudoers(user, env):
    lines = [
        f"# Whitelist claude-agent-infra — {user} — env: {env}",
        f'Defaults:{user} env_keep += "PATH MAIL MAILTO HOME SHELL"',
        "",
        "# Base system",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl start *",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl stop *",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl restart *",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl reload *",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl enable *",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl disable *",
        f"{user} ALL=(ALL) NOPASSWD: /bin/systemctl status *",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/apt update",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/apt upgrade -s",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/journalctl",
        f"{user} ALL=(ALL) NOPASSWD: /bin/cat /var/log/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/update-initramfs -u",
        f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/sysctl -p *",
        "",
        "# Controlled configuration",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/fstab",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/msmtprc",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/apt/apt.conf.d/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/sysctl.d/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/systemd/journald.conf.d/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/systemd/system/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/ssh/sshd_config.d/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/fail2ban/jail.d/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/tee /etc/modprobe.d/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/mkdir -p /etc/systemd/journald.conf.d",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/mkdir -p /etc/ssh/sshd_config.d",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/mkdir -p /etc/fail2ban/jail.d",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/mkdir -p /root/.ssh",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/install -m * /usr/local/bin/*",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/chmod * /etc/msmtprc",
        f"{user} ALL=(ALL) NOPASSWD: /usr/bin/chmod * /root/.ssh/*",
    ]

    if env == "proxmox":
        lines += [
            "",
            "# Proxmox LXC/VM (no destroy)",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct list",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct status *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct config *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct start *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct stop *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct exec * -- *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct set *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pct create *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm list",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm status *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm config *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm start *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm stop *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm reset *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/qm terminal *",
            "",
            "# Proxmox templates and storage (RO)",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/pveam list",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/pveam download *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pveversion",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pvecm status",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/pvesh get *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/proxmox-boot-tool refresh",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pvesm status",
            f"{user} ALL=(ALL) NOPASSWD: /usr/sbin/pvesm list",
        ]

    if env == "docker":
        lines += [
            "",
            "# Docker",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker ps",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker ps *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker images",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker logs *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker inspect *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker restart *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker stop *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker start *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker pull *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/bin/docker compose *",
            f"{user} ALL=(ALL) NOPASSWD: /usr/local/bin/docker-compose *",
        ]

    return "\n".join(lines) + "\n"

def apply_sudoers(user, content):
    tmp = Path(tempfile.mktemp(prefix="sudoers_"))
    try:
        tmp.write_text(content)
        result = run(f"visudo -c -f {tmp}", check=False)
        if result.returncode != 0:
            err(t("sudoers_err"))
            err(result.stderr.strip())
            tmp.unlink(missing_ok=True)
            sys.exit(1)
        dest = Path(f"/etc/sudoers.d/{user}")
        shutil.move(str(tmp), str(dest))
        dest.chmod(0o440)
        ok(t("sudoers_ok", f=dest))
    except Exception as e:
        tmp.unlink(missing_ok=True)
        err(t("sudoers_exc", e=e))
        sys.exit(1)

# ─── SSH ──────────────────────────────────────────────────────────────────────

def setup_ssh_key(user, home, key_owner="root"):
    ssh_dir = Path(home) / ".ssh"
    auth_keys = ssh_dir / "authorized_keys"

    print()
    info(t("s5_cfg", u=user))
    action = ask_choice(t("s5_gen_choice"), t("s5_gen_opts"))

    if action == t("s5_gen_opts")[0]:
        default_dir = "/root/claude_keys" if key_owner == "root" else f"/home/{key_owner}/keys"
        key_dir = ask(t("s5_keydir"), default=default_dir)
        Path(key_dir).mkdir(parents=True, exist_ok=True)
        key_path = f"{key_dir}/{user}_key"
        if Path(key_path).exists():
            warn(t("s5_key_exists", k=key_path))
            Path(key_path).unlink()
            Path(f"{key_path}.pub").unlink(missing_ok=True)
        run(f'ssh-keygen -t ed25519 -f "{key_path}" -N "" -C "{user}@agent"')
        pub_key = Path(f"{key_path}.pub").read_text().strip()
        run(f"chown -R {key_owner}:{key_owner} {key_dir}")
        run(f"chmod 700 {key_dir}")
        run(f"chmod 600 {key_path}")
        run(f"chmod 644 {key_path}.pub")
        ok(t("s5_priv", k=key_path))
        ok(t("s5_pub", k=f"{key_path}.pub"))
        warn(t("s5_copy", k=key_path))
    else:
        print(t("s5_add_hint"))
        while True:
            entrada = input(t("s5_add_prompt")).strip()
            if not entrada:
                warn(t("s5_add_empty"))
                continue
            p = Path(entrada)
            if p.exists() and p.is_dir():
                warn(t("s5_add_dir", e=entrada))
                continue
            if p.exists() and p.is_file():
                pub_key = p.read_text().strip()
            else:
                pub_key = entrada
            if not pub_key.startswith(("ssh-ed25519", "ssh-rsa", "ecdsa-sha2")):
                warn(t("s5_add_invalid"))
                continue
            ok(t("s5_add_ok"))
            break

    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    with open(auth_keys, "a") as f:
        f.write(pub_key + "\n")
    auth_keys.chmod(0o600)
    run(f"chown -R {user}:{user} {ssh_dir}")
    ok(t("s5_installed", k=auth_keys))

# ─── MAIN ─────────────────────────────────────────────────────────────────────

SEP  = "=" * 60
DASH = "-" * 60

def section(n, total, title):
    print()
    print(SEP)
    print(f"  [ {n}/{total} ] {title}")
    print(DASH)

def main():
    print()
    print(SEP)
    print("  claude-agent-infra")
    print("  Proxmox VE / Debian / Ubuntu / Docker")
    print(SEP)

    # Selección de idioma
    select_language()

    print()
    print(SEP)
    print(f"  {t('header_title')}")
    print(f"  {t('header_compat')}")
    print(SEP)
    print()

    # 1/5 Verificación entorno
    section(1, 5, t("s1_title"))
    check_and_install_deps()

    # 2/5 Entorno
    section(2, 5, t("s2_title"))
    detected = detect_os()
    env_names = {"proxmox": "Proxmox VE", "docker": "Docker host", "debian": "Debian/Ubuntu base"}
    info(f"{t('s2_detected')} {env_names[detected]}")
    env_choice = ask_choice(t("s2_confirm"), t("s2_opts"))
    env_map = {"Proxmox VE": "proxmox", "Debian/Ubuntu base": "debian", "Docker host": "docker"}
    env = env_map[env_choice]

    # 3/5 Usuario restringido
    section(3, 5, t("s3_title"))
    user = ask(t("s3_prompt"), default="claude")
    home = f"/home/{user}"
    if run(f"id {user}", check=False).returncode == 0:
        warn(f"⚠️  {t('s3_exists', u=user)}")
        warn(f"   {t('s3_exists2', h=home)}")
    else:
        run(f"useradd -m -s /bin/bash {user}")
        ok(t("s3_created", u=user, h=home))

    # 4/5 Usuario admin
    section(4, 5, t("s4_title"))
    info(t("s4_info1"))
    info(t("s4_info2"))
    info(t("s4_info3"))
    admin = ask(t("s4_prompt"), default="").strip()
    admin_has_key = False
    if admin:
        if run(f"id {admin}", check=False).returncode == 0:
            warn(f"⚠️  {t('s4_exists', u=admin)}")
            warn(f"   {t('s4_exists2', u=admin)}")
            auth_keys_path = Path(f"/home/{admin}/.ssh/authorized_keys")
            if auth_keys_path.exists() and auth_keys_path.stat().st_size > 0:
                info(f"  → {t('s4_has_key', u=admin)}")
                warn(f"   {t('s4_has_key2', u=admin)}")
                admin_has_key = True
        else:
            run(f"useradd -m -s /bin/bash {admin}")
            ok(t("s4_created", u=admin))

    # 5/5 Claves SSH + sudoers
    section(5, 5, t("s5_title"))
    setup_ssh_key(user, home, key_owner="root")
    if admin and not admin_has_key:
        setup_ssh_key(admin, f"/home/{admin}", key_owner=admin)

    print()
    print(DASH)
    info(t("sudoers_gen"))
    sudoers_content = build_sudoers(user, env)
    apply_sudoers(user, sudoers_content)
    if admin:
        admin_sudoers = f"# {admin} — full sudo\n{admin} ALL=(ALL) NOPASSWD: ALL\n"
        apply_sudoers(admin, admin_sudoers)
        ok(t("sudoers_admin", u=admin))

    # Verificación final
    print()
    print(SEP)
    print(f"  {t('verify_title')}")
    print(DASH)
    print()
    info(t("verify_user", u=user))
    run(f"id {user}", check=False)
    info(t("verify_ssh"))
    run(f"ls -la /home/{user}/.ssh/", check=False)
    info(t("verify_sudoers"))
    run(f"head -5 /etc/sudoers.d/{user}", check=False)

    print()
    print(SEP)
    ok(t("done_title"))
    print(DASH)
    print()
    info(t("done_connect"))
    print(f"    ssh {user}@<IP_NODO>")
    print()
    warn(t("done_warn"))
    print()
    print(SEP)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{T[LANG].get('cancelled', 'Cancelled.')}")
        sys.exit(0)
