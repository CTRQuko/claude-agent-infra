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
    print()
    for binary, pkg, desc in REQUIRED_TOOLS:
        found = shutil.which(binary) is not None
        status = f"{GREEN}✅ {RESET}" if found else f"{RED}❌ {RESET}"
        print(f"  {status} {binary:15s} — {desc}")
    print()

    if not missing:
        ok("Todas las herramientas están disponibles.")
        return

    print()
    warn("Faltan las siguientes herramientas:")
    for binary, pkg, desc in missing:
        print(f"  ❌  {binary} ({pkg}) — {desc}")
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

def setup_ssh_key(user, home, key_owner="root"):
    """Gestiona clave SSH: generar o añadir existente.
    key_owner: usuario que custodia la clave privada generada (root para usuario restringido, el propio admin para admin).
    """
    ssh_dir = Path(home) / ".ssh"
    auth_keys = ssh_dir / "authorized_keys"

    print()
    info(f"Configurando clave SSH para usuario '{user}':")
    action = ask_choice("¿Generar nueva clave o añadir existente?", [
        "Generar nueva clave ed25519",
        "Añadir clave pública existente"
    ])

    if action.startswith("Generar"):
        if key_owner == "root":
            default_dir = "/root/claude_keys"
        else:
            default_dir = f"/home/{key_owner}/keys"
        key_dir = ask("Directorio para guardar las claves", default=default_dir)
        Path(key_dir).mkdir(parents=True, exist_ok=True)
        key_path = f"{key_dir}/{user}_key"
        if Path(key_path).exists():
            warn(f"La clave '{key_path}' ya existe — se sobreescribirá.")
            Path(key_path).unlink()
            Path(f"{key_path}.pub").unlink(missing_ok=True)
        run(f'ssh-keygen -t ed25519 -f "{key_path}" -N "" -C "{user}@agent"')
        pub_key = Path(f"{key_path}.pub").read_text().strip()
        run(f"chown -R {key_owner}:{key_owner} {key_dir}")
        run(f"chmod 700 {key_dir}")
        run(f"chmod 600 {key_path}")
        run(f"chmod 644 {key_path}.pub")
        ok(f"Clave privada: {key_path}")
        ok(f"Clave pública: {key_path}.pub")
        warn(f"Copia la clave privada a tu máquina: {key_path}")
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
    print("  claude-agent-infra — Setup usuario restringido")
    print("  Compatible: Proxmox VE / Debian / Ubuntu / Docker")
    print(SEP)
    print()

    check_root()

    # 1/5 Verificación entorno
    section(1, 5, "VERIFICACIÓN DEL ENTORNO")
    check_and_install_deps()

    # 2/5 Entorno
    section(2, 5, "ENTORNO DE DESTINO")
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

    # 3/5 Usuario restringido
    section(3, 5, "USUARIO RESTRINGIDO")
    user = ask("Nombre de usuario restringido", default="claude")
    home = f"/home/{user}"
    if run(f"id {user}", check=False).returncode == 0:
        warn(f"⚠️  El usuario '{user}' ya existe.")
        warn(f"   Se configurará SSH y sudoers en su home existente: {home}")
    else:
        run(f"useradd -m -s /bin/bash {user}")
        ok(f"Usuario '{user}' creado con home {home}")

    # 4/5 Usuario admin
    section(4, 5, "USUARIO ADMINISTRADOR  (opcional)")
    info("Usuario administrador con sudo total")
    info("  → Introduce un usuario existente (se añadirá sudo + SSH)")
    info("  → O un nombre nuevo (se creará con sudo total)")
    admin = ask("Nombre de usuario admin [ENTER para omitir]", default="").strip()
    admin_has_key = False
    if admin:
        if run(f"id {admin}", check=False).returncode == 0:
            warn(f"⚠️  El usuario '{admin}' ya existe.")
            warn(f"   Se configurará sudo en su home existente: /home/{admin}")
            # Comprobar si ya tiene authorized_keys
            auth_keys_path = Path(f"/home/{admin}/.ssh/authorized_keys")
            if auth_keys_path.exists() and auth_keys_path.stat().st_size > 0:
                info(f"  → '{admin}' ya tiene clave SSH configurada.")
                warn(f"   Recuerda usar esa clave para conectarte como '{admin}'.")
                admin_has_key = True
        else:
            run(f"useradd -m -s /bin/bash {admin}")
            ok(f"Usuario admin '{admin}' creado.")

    # 5/5 Claves SSH + sudoers
    section(5, 5, "CLAVES SSH")
    setup_ssh_key(user, home, key_owner="root")
    if admin and not admin_has_key:
        setup_ssh_key(admin, f"/home/{admin}", key_owner=admin)

    print()
    print(DASH)
    info("Generando y validando sudoers...")
    sudoers_content = build_sudoers(user, env)
    apply_sudoers(user, sudoers_content)
    if admin:
        admin_sudoers = f"# {admin} — root total\n{admin} ALL=(ALL) NOPASSWD: ALL\n"
        apply_sudoers(admin, admin_sudoers)
        ok(f"Sudoers admin aplicado para '{admin}'.")

    # Verificación final
    print()
    print(SEP)
    print("  VERIFICACIÓN FINAL")
    print(DASH)
    print()
    info(f"Usuario {user}:")
    run(f"id {user}", check=False)
    info("SSH authorized_keys:")
    run(f"ls -la /home/{user}/.ssh/", check=False)
    info("Sudoers (primeras 5 líneas):")
    run(f"head -5 /etc/sudoers.d/{user}", check=False)

    print()
    print(SEP)
    ok("INSTALACIÓN COMPLETA")
    print(DASH)
    print()
    info(f"Prueba conexión desde tu máquina:")
    print(f"    ssh {user}@<IP_NODO>")
    print()
    warn("Recuerda copiar la clave privada a tu máquina antes de borrar el directorio de claves.")
    print()
    print(SEP)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstalación cancelada.")
        sys.exit(0)
