# claude-agent-infra

Toolkit para desplegar un usuario restringido compatible con Claude Code en entornos servidor Linux, Proxmox VE y Docker.

Incluye el script de instalación, un `CLAUDE.md` genérico y una skill técnica lista para usar con Claude Code.

---

## ¿Qué incluye?

| Fichero | Descripción |
|---|---|
| `setup.py` | Script interactivo Python que crea el usuario, configura SSH y genera la whitelist sudoers |
| `CLAUDE.md` | Configuración genérica para Claude Code: modos, zonas rojas, idioma, perfiles |
| `proxmox_linux_skill.md` | Skill técnica: cómo Claude trabaja con Linux genérico y Proxmox de forma segura |

---

## Compatibilidad

| Entorno | Estado |
|---|---|
| Proxmox VE 8+ | ✅ |
| Debian 12+ | ✅ |
| Ubuntu Server 22.04+ / 24.04 | ✅ |
| Docker host (Debian-based) | ✅ |
| CentOS / RHEL / Alpine | ❌ |

---

## Requisitos previos

- Python 3 instalado en el servidor
- Acceso root al servidor
- `visudo` disponible (`sudo` instalado)
- Cliente SSH configurado en tu máquina (Windows/Mac/Linux)

---

## Instalación

### 1. Clona el repo en el servidor

```bash
git clone https://github.com/<tu-usuario>/claude-agent-infra.git
cd claude-agent-infra
```

### 2. Ejecuta el script como root

```bash
sudo python3 setup.py
```

El script preguntará de forma interactiva:

```
Entorno detectado: Proxmox VE
¿Confirmar entorno? [1-3]: 1

Nombre de usuario restringido [claude]:
Usuario admin con sudo total (ENTER para omitir):

¿Generar nueva clave o añadir existente?
  1. Generar nueva clave ed25519
  2. Añadir clave pública existente
```

### 3. Copia la clave privada a tu máquina

```bash
# Desde tu máquina Windows/Mac
scp root@<IP_SERVIDOR>:/root/claude_keys/claude_key ~/.ssh/claude_key
```

### 4. Prueba la conexión

```bash
ssh claude@<IP_SERVIDOR>
```

---

## Configuración Claude Code

### Coloca los ficheros en tu máquina

```
~/.claude/CLAUDE.md                        ← copia o adapta el CLAUDE.md del repo
~/.claude/skills/proxmox-linux/
    └── proxmox_linux_skill.md             ← copia la skill del repo
```

### Configura el alias SSH (opcional pero recomendado)

```
# ~/.ssh/config
Host mi-servidor
    HostName <IP_SERVIDOR>
    User claude
    IdentityFile ~/.ssh/claude_key
```

---

## Modos disponibles en Claude Code

| Modo | Modelo default | Cuándo usarlo |
|---|---|---|
| `plan` | Haiku | Diseñar, analizar, proponer — Claude no ejecuta nada |
| `interactivo` | Sonnet | Primera vez / riesgo / troubleshooting — confirma por bloque |
| `auto` | Sonnet | Rutinas conocidas / solo lectura — ejecuta sin pausas |
| `super` | Opus | Sin restricciones — triple verificación obligatoria |

### Override de modelo

Por defecto Claude usa el modelo asignado a cada modo. Si quieres usar otro modelo, indícalo después del modo:

```
modo plan              → Haiku (default)
modo plan sonnet       → fuerza Sonnet en modo PLAN
modo auto haiku        → fuerza Haiku en modo AUTO
modo interactivo opus  → fuerza Opus en modo INTERACTIVO
```

> `super` no admite override — siempre usa Opus.

---

## Zonas rojas

Claude **nunca ejecutará** sin confirmación explícita:

- `pct destroy` / `qm destroy` / `zfs destroy`
- `rm -rf` en rutas críticas
- Edición directa de `/etc/sudoers`
- Creación/borrado de usuarios sin revisión
- Cambios de red o firewall que puedan cortar acceso SSH

---

## Licencia

MIT — úsalo, adáptalo, compártelo.
