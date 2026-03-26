# Skill: Entorno Linux + Proxmox (genérico)

## 0. Propósito

Esta skill describe cómo trabajar de forma segura con:
- Servidores Linux genéricos (por ejemplo: `linux-app-1`, `linux-db-1`).
- Nodos Proxmox que gestionan VMs y LXCs (por ejemplo: `proxmox-node-1`, `proxmox-node-2`).

No contiene datos reales de rutas, usuarios, IPs ni contraseñas.
El usuario debe proporcionar esos detalles en cada proyecto o sesión.


---

## 1. Clasificación de la tarea

Claude, antes de proponer comandos o cambios, clasifica:

1. ¿La tarea se refiere a…?
   - A) Una aplicación/servicio dentro de un sistema operativo Linux concreto  
     → Clasifica como **LINUX_GENERIC**.
   - B) Gestión de VMs/LXCs, snapshots, storage o red desde un hipervisor Proxmox  
     → Clasifica como **PROXMOX_CLUSTER**.

2. Si no está claro:
   - Pregunta: “¿Es una tarea sobre un servidor Linux dentro de una VM/LXC o sobre el hipervisor Proxmox (gestión de VMs/LXCs)?”


---

## 2. Reglas generales (ambos perfiles)

- No inventes usuarios, hosts, IPs ni rutas:
  - Usa nombres descriptivos genéricos (`proxmox-node-1`, `linux-app-1`) hasta que el usuario indique los reales.
- Siempre que propongas comandos:
  - Indica en qué host deben ejecutarse.
  - Especifica si requieren privilegios `sudo`.
- Antes de ejecutar cambios que puedan afectar servicio:
  - Indica el posible impacto.
  - Propón un plan de verificación posterior (logs, estado de servicio, etc.).

Zonas rojas compartidas:
- Nada de `rm -rf` en rutas amplias o poco específicas.
- Nada de `destroy` de recursos (VMs, LXCs, volúmenes) sin confirmación muy explícita del usuario.
- Nada de editar `/etc/sudoers` directamente; usar ficheros en `/etc/sudoers.d/` solo si el usuario lo indica.


---

## 3. Perfil LINUX_GENERIC

### 3.1. Suposiciones

- Servidores Linux accesibles vía SSH con un usuario no-root.
- Ese usuario puede tener o no `sudo`; no lo asumas:
  - Pregunta si tiene permisos `sudo` antes de proponer comandos con `sudo`.

Ejemplos de hosts:
- `linux-app-1` — servidor de aplicaciones.
- `linux-db-1` — servidor de bases de datos.
- `linux-utils-1` — máquina de utilidades/automatización.


### 3.2. Flujo de trabajo recomendado

1. **Modo PLAN**:
   - Entender qué servicio, qué ruta y qué impacto puede tener el cambio.
   - Proponer los comandos que se usarían, pero sin ejecutarlos.

2. **Modo INTERACTIVO**:
   - Primera vez que se toca un servicio o configuración relevante.
   - Presentar:
     - Comando.
     - Explicación breve de qué hace.
     - Cómo revertirlo en caso de problema (si aplica).

3. **Modo AUTOMÁTICO**:
   - Tareas repetitivas validadas previamente.
   - Operaciones de solo lectura (logs, `status`, `list`, etc.).
   - Pequeños cambios con impacto acotado.

4. **Modo SUPER**:
   - Solo si el usuario lo habilita explícitamente en el proyecto.
   - No definas ni uses contraseñas reales aquí; utiliza placeholders tipo `<SUPER_CODE>`.


### 3.3. Tipos de operaciones típicas (seguras)

Lectura / diagnóstico:
- Comprobar estado de servicios (`systemctl status ...`).
- Revisar logs (`journalctl`, ficheros de log en `/var/log/...`).
- Comprobar espacio en disco, uso de CPU/memoria, etc.

Cambios controlados:
- Edición de ficheros de configuración con copia de seguridad previa.
- Despliegue de versiones de aplicación en rutas definidas por el usuario.
- Cambios en servicios de sistema con rollback claro.


---

## 4. Perfil PROXMOX_CLUSTER

### 4.1. Suposiciones

- Uno o varios nodos Proxmox accesibles por SSH con un usuario no-root que tiene un conjunto limitado de comandos permitidos con `sudo`.
- Gestión de:
  - LXC containers (por ejemplo IDs: `100`, `200`).
  - VMs (por ejemplo IDs: `300`, `400`).
  - Storage, snapshots y estado del cluster.

Ejemplos de hosts:
- `proxmox-node-1` — nodo principal.
- `proxmox-node-2` — nodo secundario.
- `proxmox-backup-1` — nodo dedicado a backup (si aplica).


### 4.2. Operaciones permitidas (abstractas)

Ejemplos de comandos que suelen ser seguros si el usuario los ha habilitado:

- Consultar estado:
  - `sudo pct list|status|config <id>`
  - `sudo qm list|status|config <id>`
  - `sudo pvesm status`
  - `sudo pveversion`
  - `sudo journalctl -u <servicio> -n 50`

- Gestión NO destructiva:
  - `sudo pct start|stop <id>`
  - `sudo qm start|stop|reset <id>`
  - `sudo systemctl start|stop|restart|status <servicio>`

No asumas estos comandos como disponibles: preséntalos como ejemplos genéricos; que el usuario confirme o ajuste a su realidad.


### 4.3. Operaciones prohibidas o de alto riesgo

No propongas ni completes sin autorización explícita y clara:

- Destrucción de recursos:
  - `pct destroy`, `qm destroy`.
  - Comandos de liberación de storage que borren datos (`zfs destroy`, `pvesm free`, etc.).

- Cambios globales de cluster:
  - Comandos que alteren la configuración de cluster (`pvecm` en modos que puedan sacar nodos del cluster, etc.).
  - Cambios de configuración de red de Proxmox que puedan cortar acceso.

- Cambios irreversibles en almacenamiento:
  - Borrado de pools, datastores o volúmenes sin plan de backup/restauración.


### 4.4. Flujo de trabajo recomendado

1. **PLAN**:
   - Entender objetivo (ej.: “migrar este servicio a otro LXC”, “aumentar recursos de una VM”).
   - Identificar:
     - ID de LXC/VM.
     - Nodo actual y nodo destino.
     - Ventana de mantenimiento (si aplica).

2. **INTERACTIVO**:
   - Primera vez para un tipo de operación (crear LXC con cierto template, ajustar recursos, etc.).
   - Mostrar los comandos Proxmox propuestos y el efecto esperado.

3. **AUTOMÁTICO**:
   - Tareas ya probadas (por ejemplo, listar estado, reiniciar un servicio dentro de una VM conocida, etc.).
   - Series de comandos de solo lectura o bajo riesgo.

4. **SUPER**:
   - Solo si el usuario define un protocolo muy claro (3 pasos, código, etc.).
   - Incluso en SUPER, explica qué vas a destruir antes de hacerlo y ofrece confirmar.


---

## 5. SSH y credenciales (genérico)

- Nunca inventes:
  - Usuarios (`root`, `admin`, etc.) si el usuario no los ha mencionado.
  - Hosts (`proxmox-node-1`, `linux-app-1`) fuera de ejemplos.
  - Puertos SSH no estándar.

- Si necesitas credenciales, hazlo así:
  - Pide al usuario:
    - Usuario SSH.
    - Host o alias.
    - Método de autenticación (clave, agente, etc.).
  - No escribas contraseñas literales en esta skill.
  - Usa placeholders como `<SUDO_PASSWORD>` o `<SSH_USER>` si necesitas ilustrar comandos.


---

## 6. Patrón de comunicación con el usuario

Cuando el usuario pida algo sobre Linux/Proxmox:

1. Confirma:
   - Tipo de máquina (Linux genérico o Proxmox).
   - Impacto deseado (solo diagnóstico, cambio pequeño, operación mayor).

2. Propón:
   - Un plan en pasos.
   - Los comandos concretos.
   - Cómo validar que ha ido bien (checks posteriores).

3. Ajusta el modo:
   - Si es algo nuevo/delicado → INTERACTIVO.
   - Si es rutina y ya probado → AUTOMÁTICO.
   - Si el usuario insiste en algo muy arriesgado → explica los riesgos y, si aun así quiere seguir, asegúrate de que lo deja muy claro.


---

## 7. Resumen

- Usa esta skill siempre que vayas a:
  - Tocar servicios/aplicaciones en Linux.
  - Gestionar VMs/LXCs en un cluster Proxmox.
- Mantén una separación mental clara:
  - **LINUX_GENERIC**: dentro de la VM/LXC o servidor.
  - **PROXMOX_CLUSTER**: hipervisor que orquesta VMs/LXCs.
- Ante la duda, pregunta antes de actuar.