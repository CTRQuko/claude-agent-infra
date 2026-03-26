# CLAUDE.md - Playbook genérico Linux/Proxmox

## 0. Idioma

IDIOMA_ACTIVO = ES
# Valores posibles: ES (español), EN (english)

Claude:
- Si IDIOMA_ACTIVO = ES → responde en español.
- Si IDIOMA_ACTIVO = EN → responde en inglés.
- Mantén el idioma estable durante toda la sesión, salvo petición explícita del usuario.


---

## 1. Contexto general

Este proyecto puede interactuar con:
- Servidores Linux genéricos (por ejemplo: `linux-app-1`, `linux-db-1`).
- Nodos Proxmox para gestionar VMs y LXCs (por ejemplo: `proxmox-node-1`, `proxmox-node-2`).

No asumas nada sobre IPs, usuarios ni contraseñas.
Siempre pide o utiliza la información que el usuario proporcione en cada sesión.


---

## 2. Perfiles activos

PERFILES_ACTIVOS = [
  "LINUX_GENERIC",
  "PROXMOX_CLUSTER"
]

Claude:
- Interpreta que pueden existir a la vez:
  - Un conjunto de servidores Linux genéricos accesibles vía SSH.
  - Uno o varios nodos Proxmox que gestionan VMs y LXCs.
- Cuando la tarea mencione VMs, LXCs o hipervisor → aplica reglas de PROXMOX_CLUSTER.
- Cuando la tarea sea sobre aplicaciones, servicios o scripts en una máquina concreta → aplica reglas de LINUX_GENERIC.
- Si hay ambigüedad, pregunta explícitamente al usuario en qué tipo de máquina se va a actuar.


---

## 3. Sistema de modos

Modos disponibles:
- PLAN
- INTERACTIVO
- AUTOMÁTICO
- SUPER (opcional, requiere protocolo explícito)

Reglas básicas:

1. Si el usuario especifica el modo explícitamente → usa ese modo sin reclasificación.
2. El modo activo no persiste para siempre: cuando cambie mucho el contexto (tarea nueva distinta), vuelve a proponer modo.
3. Siempre anuncia el modo y (si aplica) el modelo orientativo, por ejemplo:
   - `🧠 Usando [modelo] en modo [PLAN/INTERACTIVO/AUTOMÁTICO/SUPER]`.

Criterios resumidos:

- PLAN:
  - Diseñar, analizar, proponer estrategias, arquitecturas o planes.
  - No ejecutar acciones de escritura ni comandos reales (solo propuestas).

- INTERACTIVO:
  - Primera vez tocando algo delicado.
  - Riesgo de pérdida de datos o interrupción de servicio.
  - Troubleshooting de problemas en producción.

- AUTOMÁTICO:
  - Tareas rutinarias, ya probadas, con bajo riesgo.
  - Operaciones de solo lectura o pequeños cambios controlados.
  - Scripts y comandos que el usuario ha validado antes.

- SUPER:
  - Modelo: Opus — sin override posible.
  - Acceso root total vía usuario admin — sin whitelist, sin zonas rojas, sin confirmaciones.
  - Requiere protocolo de activación de 3 pasos (ver abajo).
  - Break automático si un mismo objetivo falla 5 veces consecutivas → entra en INTERACTIVO.

### Protocolo de activación SUPER

```
PASO 1 → Usuario escribe: "modo super"
          Claude responde: solicita usuario SSH admin y ruta a clave privada

PASO 2 → Usuario proporciona: <usuario_admin> y <ruta_clave_privada>
          Claude valida conexión SSH con esas credenciales

PASO 3 → Si conexión OK → Claude muestra aviso obligatorio:
```

  [ES]
╔══════════════════════════════════════════════════════════════╗
║  💥💀☠️  PELIGRO EXTREMO — LEER ANTES DE CONTINUAR  ☠️💀💥  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   ██████  MODO SUPER ACTIVADO  ██████                        ║
║                                                              ║
║  🔴 ACCESO ROOT TOTAL SIN RESTRICCIONES 🔴                   ║
║  💣 CADA COMANDO ES POTENCIALMENTE IRREVERSIBLE 💣           ║
║  ⚡ NO HAY ZONAS ROJAS — NO HAY CONFIRMACIONES ⚡            ║
║  🔥 UN ERROR PUEDE DESTRUIR EL SISTEMA ENTERO 🔥             ║
║                                                              ║
║  ☠️  PROCEDE SOLO SI SABES LO QUE HACES  ☠️                  ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║       💀💥🚨  ¿REALMENTE QUIERES CONTINUAR?  🚨💥💀          ║
╚══════════════════════════════════════════════════════════════╝
⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️

  [EN]
╔══════════════════════════════════════════════════════════════╗
║  💥💀☠️  EXTREME DANGER — READ BEFORE CONTINUING  ☠️💀💥    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   ██████  SUPER MODE ACTIVATED  ██████                       ║
║                                                              ║
║  🔴 FULL ROOT ACCESS — ZERO RESTRICTIONS 🔴                  ║
║  💣 EVERY COMMAND IS POTENTIALLY IRREVERSIBLE 💣             ║
║  ⚡ NO RED ZONES — NO CONFIRMATIONS ⚡                        ║
║  🔥 ONE MISTAKE CAN DESTROY THE ENTIRE SYSTEM 🔥             ║
║                                                              ║
║  ☠️  PROCEED ONLY IF YOU KNOW WHAT YOU ARE DOING  ☠️         ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║       💀💥🚨  DO YOU REALLY WANT TO CONTINUE?  🚨💥💀        ║
╚══════════════════════════════════════════════════════════════╝
⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️🔴⚠️

  [SUPER + AUTO — ES]
╔══════════════════════════════════════════════════════════════╗
║  🐒💣🚗  MODO SUPER + AUTOMÁTICO DETECTADO  🚗💣🐒          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Acabas de darle las llaves del coche a un mono borracho     ║
║  con una caja de bombas, tres ruedas pinchadas               ║
║  y el GPS configurado en DESTRUIR.                           ║
║                                                              ║
║  🔴 ROOT TOTAL + CERO CONFIRMACIONES + OPUS SIN FRENOS 🔴   ║
║                                                              ║
║  Lo que puede salir mal:                                     ║
║  💥 Todo                                                     ║
║  🔥 Absolutamente todo                                       ║
║  ☠️  En ese orden                                            ║
║                                                              ║
║  Si esto fue un error — escribe STOP ahora mismo.           ║
║  Si fue intencionado — que el señor te pille confesado.      ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  🐒💀🚨 ¿EL MONO TIENE TU PERMISO? CONFIRMA O HUYE 🚨💀🐒   ║
╚══════════════════════════════════════════════════════════════╝
🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥

  [SUPER + AUTO — EN]
╔══════════════════════════════════════════════════════════════╗
║  🐒💣🚗  SUPER + AUTO MODE DETECTED  🚗💣🐒                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  You just handed a flamethrower to a raccoon                 ║
║  in a data center.                                           ║
║  Blindfolded. On a Friday afternoon.                         ║
║                                                              ║
║  🔴 ROOT TOTAL + ZERO CONFIRMATIONS + OPUS UNLEASHED 🔴     ║
║                                                              ║
║  What could go wrong:                                        ║
║  💥 Everything                                               ║
║  🔥 Absolutely everything                                    ║
║  ☠️  In that order                                           ║
║                                                              ║
║  If this was a mistake — type STOP. Right now.              ║
║  If this was intentional — you were warned.                  ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  🐒💀🚨 CONFIRM OR RUN. YOUR CALL. 🚨💀🐒                   ║
╚══════════════════════════════════════════════════════════════╝
🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥🔴💥

Expira: log entregado + checklist de funcionamiento completado.
Credenciales: nunca en texto plano — solo ruta al fichero de clave privada.


---

## 4. Zonas rojas (genéricas)

Independientemente del entorno, NUNCA ejecutes, propongas ni completes sin confirmación explícita del usuario:

- Destrucción de sistemas:
  - `rm -rf /`, `rm -rf` en rutas críticas.
  - Comandos de destrucción de VMs/LXCs o volúmenes (por ejemplo: `destroy`, `delete`, `zfs destroy`).
- Modificación de privilegios:
  - Edición directa de `/etc/sudoers`.
  - Comandos que creen, borren o modifiquen usuarios y grupos de sistema sin revisión humana.
- Cambios globales de red o firewall:
  - Reglas que puedan cortar el acceso SSH o dejar el sistema inaccesible.
- Cambios de configuración masiva sin copia de seguridad:
  - Edición de ficheros críticos sin proponer primero un backup o un diff claro.

Si el usuario solicita alguna de estas acciones:
1. Explica claramente el riesgo.
2. Propón un plan seguro (backup, entorno de pruebas, alternativa menos destructiva).
3. Solo actúa tras confirmación explícita e inequívoca.


---

## 5. Skill externa obligatoria

Antes de ejecutar acciones en servidores Linux o nodos Proxmox:

1. Carga y lee la skill:
   - `proxmox_linux_skill.md`
2. Sigue su flujo:
   - Cómo clasificar la tarea (Linux genérico vs Proxmox).
   - Qué comandos están permitidos y cuáles requieren confirmación.
   - Cómo moverte entre modos PLAN, INTERACTIVO y AUTOMÁTICO.

Claude:
- Considera este `CLAUDE.md` como la guía general del proyecto.
- Considera `proxmox_linux_skill.md` como la referencia técnica detallada para Linux/Proxmox.
- Si hay conflicto, las instrucciones explícitas del usuario tienen prioridad, luego este `CLAUDE.md`, luego las skills.


---

## 6. Reglas de estilo y comunicación

- Mantén las respuestas ordenadas:
  - Contexto breve.
  - Plan de acción en pasos.
  - Detalle técnico (comandos, fragmentos de código).
- Cuando vayas a proponer acciones en remoto (Linux/Proxmox):
  - Indica claramente qué harías.
  - Ofrece siempre la opción de:
    - Solo mostrar comandos.
    - O ejecutar/completar (en función del modo y confirmación del usuario).
- Si hay ambigüedad en el entorno (qué nodo, qué LXC, qué servicio), pregunta antes de asumir.


---

## 7. Resumen operativo

- Idioma seleccionable con `IDIOMA_ACTIVO`.
- Perfiles simultáneos:
  - `LINUX_GENERIC`
  - `PROXMOX_CLUSTER`
- Este archivo define:
  - Idioma, modos, zonas rojas, relación con las skills.
- La skill `proxmox_linux_skill.md` define:
  - Detalles concretos para trabajar con Linux y Proxmox de forma segura.