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

# ─── UTILIDADES ───────────────────────────────────────────────────────────────

def run(cmd, check=True):
    """Ejecuta comando y devuelve (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        err(f"Comando falló: {cmd}")
        err(result.stderr.strip())
        sys.exit(1)
    return result

def ask(prompt, default=None):
    """Pregunta al usuario con valor por defecto opcional."""
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    return input(f"{prompt}: ").strip()

def ask_choice(prompt, options):
    """Pregunta con opciones numeradas, devuelve la seleccionada."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        try:
            choice = int(input(f"{prompt} [1-{len(options)}]: ").strip())
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except ValueError:
            pass
        warn("Opción no válida, intenta de nuevo.")

REQUIRED_TOOLS = [
    ("sudo",    "sudo",   "paquete sudo (visudo, sudoers)"),
    ("useradd", "passwd", "gestión de usuarios"),
    ("ssh-keygen", "openssh-client", "generación de claves SSH"),
]

def check_root():
    if os.geteuid() != 0:
        err("Este script debe ejecutarse como root.")
        err("Usa: sudo python3 setup.py")
        sys.exit(1)

def check_and_install_deps():
    """Verifica herramientas mínimas e instala las que falten."""
    missing = []
    for binary, pkg, desc in REQUIRED_TOOLS:
        if not shutil.which(binary):
            missing.append((binary, pkg, desc))

    print()
    info("Verificando herramientas mínimas necesarias:")
    for binary, pkg, desc in REQUIRED_TOOLS:
        found = shutil.which(binary) is not None
        status = f"{GREEN}✅{RESET}" if found else f"{RED}❌{RESET}"
        print(f"  {status} {binary:15s} — {desc}")

    if not missing:
        ok("Todas las herramientas están disponibles.")
        return

    print()
    warn("Faltan las siguientes herramientas:")
    for binary, pkg, desc in missing:
        print(f"  ❌ {binary} ({pkg}) — {desc}")
    print()
    confirm = input("¿Instalar automáticamente con apt? [s/N]: ").strip().lower()
    if confirm not in ("s", "si", "sí", "y", "yes"):
        err("Instalación cancelada. Instala las herramientas manualmente y vuelve a ejecutar el script.")
        sys.exit(1)

    run("apt-get update -qq")
    pkgs = " ".join(pkg for _, pkg, _ in missing)
    run(f"apt-get install -y {pkgs}")
    ok("Herramientas instaladas correctamente.")

def detect_os():
    """Detecta si es Proxmox, Docker host o Debian/Ubuntu base."""
    is_proxmox = Path("/usr/sbin/pct").exists() or Path("/usr/sbin/qm").exists()
    is_docker = shutil.which("docker") is not None
    if is_proxmox:
        return "proxmox"
    if is_docker:
        return "docker"
    return "debian"

# ─── WHITELIST SUDOERS ────────────────────────────────────────────────────────

def build_sudoers(user, env):
    """Genera contenido sudoers según entorno."""
    lines = [
        f"# Whitelist claude-agent-infra — {user} — entorno: {env}",
        f'Defaults:{user} env_keep += "PATH MAIL MAILTO HOME SHELL"',
        "",
        "# Sistema base",
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
        "# Configuración controlada",
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
            "# Proxmox LXC/VM (sin destroy)",
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
            "# Proxmox templates y storage (RO)",
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
    """Valida con visudo y aplica sudoers."""
    tmp = Path(tempfile.mktemp(prefix="sudoers_"))
    try:
        tmp.write_text(content)
        result = run(f"visudo -c -f {tmp}", check=False)
        if result.returncode != 0:
            err("El fichero sudoers no pasó la validación de visudo:")
            err(result.stderr.strip())
            tmp.unlink(missing_ok=True)
            sys.exit(1)
        dest = Path(f"/etc/sudoers.d/{user}")
        shutil.move(str(tmp), str(dest))
        dest.chmod(0o440)
        ok(f"Sudoers aplicado: {dest}")
    except Exception as e:
        tmp.unlink(missing_ok=True)
        err(f"Error aplicando sudoers: {e}")
        sys.exit(1)

# ─── SSH ──────────────────────────────────────────────────────────────────────

def setup_ssh_key(user, home):
    """Gestiona clave SSH: generar o añadir existente."""
    ssh_dir = Path(home) / ".ssh"
    auth_keys = ssh_dir / "authorized_keys"

    print()
    info("Configuración de clave SSH:")
    action = ask_choice("¿Generar nueva clave o añadir existente?", [
        "Generar nueva clave ed25519",
        "Añadir clave pública existente"
    ])

    if action.startswith("Generar"):
        default_dir = "/root/claude_keys"
        key_dir = ask("Directorio para guardar las claves", default=default_dir)
        Path(key_dir).mkdir(parents=True, exist_ok=True)
        key_path = f"{key_dir}/{user}_key"
        run(f'ssh-keygen -t ed25519 -f "{key_path}" -N "" -C "{user}@agent"')
        pub_key = Path(f"{key_path}.pub").read_text().strip()
        run(f"chown -R root:root {key_dir}")
        run(f"chmod 700 {key_dir}")
        run(f"chmod 600 {key_path}")
        run(f"chmod 644 {key_path}.pub")
        ok(f"Clave privada: {key_path}")
        ok(f"Clave pública: {key_path}.pub")
        warn(f"Copia la clave privada a tu máquina Windows: {key_path}")
    else:
        print("  Opciones: ruta al fichero .pub o pegar la clave directamente")
        while True:
            entrada = input("Ruta al fichero .pub o clave pública: ").strip()
            if not entrada:
                warn("No introdujiste nada. Introduce una ruta a fichero .pub o pega la clave directamente.")
                continue
            p = Path(entrada)
            if p.exists() and p.is_dir():
                warn(f"'{entrada}' es un directorio, no un fichero. Introduce la ruta completa al fichero .pub.")
                continue
            if p.exists() and p.is_file():
                pub_key = p.read_text().strip()
            else:
                pub_key = entrada
            if not pub_key.startswith(("ssh-ed25519", "ssh-rsa", "ecdsa-sha2")):
                warn("Formato de clave pública no válido. Debe empezar por ssh-ed25519, ssh-rsa o ecdsa-sha2.")
                continue
            ok("Clave pública validada.")
            break

    # Instalar clave
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    with open(auth_keys, "a") as f:
        f.write(pub_key + "\n")
    auth_keys.chmod(0o600)
    run(f"chown -R {user}:{user} {ssh_dir}")
    ok(f"Clave instalada en {auth_keys}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 60)
    print("  claude-agent-infra — Setup usuario restringido")
    print("  Compatible: Proxmox VE / Debian / Ubuntu / Docker")
    print("=" * 60)
    print()

    check_root()
    check_and_install_deps()

    # Detectar entorno
    detected = detect_os()
    env_names = {"proxmox": "Proxmox VE", "docker": "Docker host", "debian": "Debian/Ubuntu base"}
    info(f"Entorno detectado: {env_names[detected]}")
    env_choice = ask_choice("¿Confirmar entorno?", [
        "Proxmox VE",
        "Debian/Ubuntu base",
        "Docker host"
    ])
    env_map = {"Proxmox VE": "proxmox", "Debian/Ubuntu base": "debian", "Docker host": "docker"}
    env = env_map[env_choice]

    # Usuario restringido
    print()
    user = ask("Nombre de usuario restringido", default="claude")
    if run(f"id {user}", check=False).returncode == 0:
        warn(f"El usuario '{user}' ya existe. Se actualizará SSH y sudoers.")
        home = f"/home/{user}"
    else:
        run(f"useradd -m -s /bin/bash {user}")
        home = f"/home/{user}"
        ok(f"Usuario '{user}' creado con home {home}")

    # Usuario admin opcional
    print()
    info("Usuario administrador humano (el 'dueño' del servidor, ej: admin, devops)")
    info("  → sudo total sin restricciones, completamente distinto del usuario restringido")
    admin = ask("Nombre de usuario admin [ENTER para omitir]", default="").strip()
    if admin:
        if run(f"id {admin}", check=False).returncode != 0:
            run(f"useradd -m -s /bin/bash {admin}")
            ok(f"Usuario admin '{admin}' creado.")

    # SSH
    setup_ssh_key(user, home)
    if admin:
        print()
        info(f"Configurando SSH para usuario admin '{admin}':")
        setup_ssh_key(admin, f"/home/{admin}")

    # Sudoers usuario restringido
    print()
    info("Generando y validando sudoers...")
    sudoers_content = build_sudoers(user, env)
    apply_sudoers(user, sudoers_content)

    # Sudoers admin
    if admin:
        admin_sudoers = f"# {admin} — root total\n{admin} ALL=(ALL) NOPASSWD: ALL\n"
        apply_sudoers(admin, admin_sudoers)
        ok(f"Sudoers admin aplicado para '{admin}'.")

    # Verificación final
    print()
    print("=" * 60)
    print("  VERIFICACIÓN FINAL")
    print("=" * 60)
    print()
    info(f"Usuario {user}:")
    run(f"id {user}", check=False)
    info("SSH authorized_keys:")
    run(f"ls -la /home/{user}/.ssh/", check=False)
    info("Sudoers (primeras 5 líneas):")
    run(f"head -5 /etc/sudoers.d/{user}", check=False)

    print()
    print("=" * 60)
    ok("INSTALACIÓN COMPLETA")
    print("=" * 60)
    print()
    info(f"Prueba conexión desde tu máquina:")
    print(f"    ssh {user}@<IP_NODO>")
    print()
    warn("Recuerda copiar la clave privada a tu máquina Windows antes de borrar /root/claude_keys/")
    print()

if __name__ == "__main__":
    main()
