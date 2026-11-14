# TEST-PLAN-JAVA — Prueba E2E del fork sobre un proyecto real

Objetivo: generar un proyecto Java de mi elección con el template, trabajarlo
de punta a punta como lo haría un desarrollador, y usar cada hallazgo para
corregir bugs o pulir detalles del template. Los fallos que pertenezcan a
features ya planificadas (JAVA-003..013) se registran y no se reimplementan
aquí, salvo que sean bugs del template actual (JAVA-001/002).

Proyecto elegido: **procesador de pedidos** con Spring Batch (chunk-oriented):
lee `pedidos.csv` (id, cliente, importe), calcula el total con IVA en un
`ItemProcessor` y escribe el resultado con un `ItemWriter`. Con tests
`@SpringBatchTest` (end-to-end + reiniciabilidad) y cierre por el arnés
(feature → implementación → evidencia → done).

Entorno: JDK 17 local, Maven vía wrapper, Git Bash, red disponible. Postgres
no corre local: los combos con `db=postgres` se validan compilando con el
perfil de test en H2 (`application-test.yml`), no contra un Postgres real.

---

## Escenarios

### T0 — Generación y puerta (matriz de combos)

| # | Combo | Verificación |
|---|---|---|
| T0.1 | estandar + java (spring-boot-batch, h2, flyway, java 17) | `./mvnw verify` + `./init.sh` verde; README/AGENTS revisados |
| T0.2 | completo-like: web+batch, postgres, liquibase, security, observability | render OK; `./mvnw test` verde (perfil H2) |
| T0.3 | framework `spring-boot` (solo web) | directorio `batch/` ausente, pom sin spring-batch |
| T0.4 | perfil `minimo` | pom sin testcontainers/archunit; build verde |
| T0.5 | `java_version: 21` | render + `mvnw validate` (sin ejecutar: JDK local 17) |

### T1 — El arnés completo sobre el proyecto

- T1.1 `harness add` una feature Java real (PROCESA-001) con criterios
  verificables → `start` → `record` → `finish` con evidencia real.
- T1.2 `harness finish` **negativo**: con un test roto, la puerta en rojo debe
  rechazar el cierre (GATE-1).
- T1.3 `agents.evals.runner --harness --contracts` verde.
- T1.4 `make backlog`, `make agents-list`, `harness status --json`.

### T2 — Plano de control (agentes) sobre el proyecto Java

- T2.1 `agents list`, `agents doctor`, `git suggest_commit_message` (repo git
  iniciado en el proyecto).
- T2.2 `git commit_feature --dry-run` — esperado: falla porque lee
  `pyproject.toml` (Python). Hallazgo → JAVA-005, no se arregla aquí salvo que
  sea trivial.
- T2.3 `make skills`, `make prompts-sync`, `make assistants-sync` sobre el
  render (el plano de control debe poder mantener su propia documentación).

### T3 — Inspección de detalles poco pulidos (render)

Revisar el contenido del proyecto generado y registrar cada rough edge:

- `harness/featureslist.json` — seeds de DS (SCOPE/RESEARCH/EDA/DATA) en un
  proyecto Java (JAVA-003).
- `AGENTS.md` generado — conteo de agentes y referencias Python.
- `.vscode/extensions.json` — recomendaciones Python en proyecto Java.
- `.github/`, `docs/` — directorios vacíos tras el gating.
- `ayuda/README.md`, `.env.example` — ¿aplican a Java?
- `.claude/agents/` espejados, `CLAUDE.md`, `opencode.json`.
- `application-test.yml` — ¿los jobs arrancan solos en los tests? (auto-run
  de Spring Batch puede romper `contextLoads` con un job real que lee CSV).
- README generado (verificado en sesión anterior, re-confirmar).

### T4 — Proyecto de negocio (procesador de pedidos)

1. Feature `PROCESA-001` en el backlog: "Procesar pedidos.csv en chunks:
   leer, aplicar IVA, escribir resultados".
2. Implementación TDD en `src/main/java/.../batch/`:
   - `PedidoJobConfig`: `FlatFileItemReader` (CSV) → `ItemProcessor` (total
     con IVA) → `ItemWriter` (CSV de salida).
   - Muestra `pedidos.csv` en resources para la demo.
   - `PedidoJobTest` con `@SpringBatchTest`: corre end-to-end sobre la
     muestra y verifica la salida; test de re-ejecución (idempotencia
     básica con job parameters distintos).
3. Cierre por el arnés: `harness finish` con la salida real de
   `./mvnw verify`.
4. Ejecución real del artefacto: `java -jar target/*.jar` (arranque con
   timeout) y comprobación del job.

---

## Registro de hallazgos

Cada hallazgo se anota con severidad, fix propuesto y feature asociada:

| ID | Dónde | Severidad | Fix | Feature | Estado |
|---|---|---|---|---|---|
| F1 | `pom.xml` + `application-test.yml`: con `db != h2`, los tests usan H2 pero falta el driver | Alta | H2 en scope `test` cuando la BD no es H2 | JAVA-001 | Corregido |
| F2 | `application-test.yml`: los jobs se auto-ejecutan al cargar el contexto | Alta | `spring.batch.job.enabled: false` en tests | JAVA-002 | Corregido |
| F3 | `harness gate` en Windows: `bash` resuelve al stub de WSL | Alta | `_bash_command` prioriza Git Bash | JAVA-002 | Corregido |
| F4 | Render Java con `.env.example`/`.vscode` Python, `ayuda/` y `.github/` vacío | Media | Condicionales por lenguaje + `_exclude` | JAVA-001 | Corregido |
| F5 | `agents doctor`/GStack en Windows: `import fcntl` (solo Unix) | Alta | Fail-open sin lock cuando no hay `fcntl` | JAVA-002 | Corregido |
| F6 | Backlog semilla de DS (RESEARCH/EDA/DATA) en un proyecto Java | Media | Semilla Java propia | JAVA-003 | Registrado |
| F7 | `git commit_feature` en Java: `next_version=null` (lee `pyproject.toml`) | Media | Bump de `<version>` en `pom.xml` | JAVA-005 | Registrado |
| F8 | Multi-job: `java -jar` falla ("Job name must be specified") | Alta | `spring.batch.job.name: ${JOB_NAME:demoJob}` | JAVA-001/002 | Corregido |
| F9 | `agents doctor`/`env` con checks Python (`pyproject.toml`) en Java | Media | Reescritura de `doctor`/`env` | JAVA-005 | Registrado |
| F10 | `git suggest_commit_message` ignora archivos untracked | Baja | Incluir `git status --porcelain` | JAVA-005 | Registrado |
| F11 | `init.sh --json` en Windows: `UnicodeEncodeError` (cp1252) | Alta | `export PYTHONUTF8=1` en la puerta | JAVA-002 | Corregido |
| F12 | `make` no instalado en Windows local: targets no ejecutables | Baja (entorno) | — (CI Linux los cubre) | — | Nota |
| F13 | `prompts_sync` modifica prompts en render con `--skip-tasks` | Baja (entorno) | Esperado: la tarea de copier los sincroniza | — | Nota |
| F14 | `template/.vscode/extensions.json` no estaba versionado en el fork (lo ignoraba el `.gitignore` raíz) | Media | `git add -f` (queda versionado) | — | Corregido |
| F15 | El template no incluía la plantilla de `.copier-answers.yml`: copier no lo generaba → `copier update` roto y agentes sin `language`/`project_slug` | **Crítica** | `template/.copier-answers.yml` con `_copier_answers \| to_nice_yaml` | JAVA-001/002 | Corregido |

Reglas:

- **Bug del template (JAVA-001/002)** → se corrige en esta iteración, con
  test/verificación y commit.
- **Rough edge pequeño y barato** (docs, gating, contenido estático) → se
  corrige si no contradice el plan; si toca dominio (agentes, backlog), se
  registra para su feature.
- **Pertenece a JAVA-003..013** → se registra en SPEC/PLAN con el detalle
  encontrado, no se reimplementa.

## Criterios de salida

- T0.1, T0.2, T0.3, T0.4 en verde; T0.5 renderizado y validado.
- T1 completo: feature cerrada con evidencia real y rechazo del finish con
  puerta roja verificado.
- T4: procesador de pedidos funcionando end-to-end y cerrado por el arnés.
- Todos los hallazgos registrados con fix aplicado (si procede) y commiteado.
- `validate_template.py` (212 combos) y render `estandar` Java en verde al
  final de cada cambio.

## Orden de ejecución

T0 → T3 (inspección inicial, antes de ensuciar el render) → T1 (arnés) →
T2 (agentes) → T4 (proyecto) → fixes iterativos → informe final con
resumen de hallazgos y commits.

---

## Resultados de la ejecución (Nov 2026)

| Escenario | Resultado |
|---|---|
| T0.1 estandar + batch + H2 + Flyway | `./init.sh` verde, 0 avisos; build + contextLoads OK |
| T0.2 web+batch + postgres + liquibase + security + observability | `./mvnw test` verde tras F1 (H2 en scope test) |
| T0.3 solo web | sin `batch/` ni dependencia batch; verify verde |
| T0.4 perfil minimo | sin testcontainers/archunit; verify verde |
| T0.5 Java 21 | render + `mvnw validate` exit 0 (sin ejecutar tests: JDK local 17) |
| T1.1 feature PROCESA-001 | `add` → `start` → `finish` OK, GATE-1..4 |
| T1.2 finish con test roto | **rechazado** (`success=false`, GATE-1) |
| T1.3 evals | `harness` 14/14, `contracts` PASS |
| T1.4 estado | `harness next` OK; `make backlog` no ejecutable (F12) |
| T2.1 git/doctor | `doctor` ejecuta tras F5; checks Python fallan (F9) |
| T2.2 `commit_feature` | no falla, pero `next_version=null` (F7) |
| T2.3 mantenimiento | `prompts_sync --write` actualiza 4 prompts (F13) |
| T4 procesador de pedidos | job chunk COMPLETED; CSV `1,Ana,100.00,121.00`; `java -jar` OK tras F8 |

Proyecto de prueba: procesador de pedidos (CSV → IVA 21% → CSV) con lectura
`FlatFileItemReader`, procesador, writer, tests end-to-end y de re-ejecución.

Cambios aplicados al template durante la prueba: F1, F2, F3, F4, F5, F8,
F11, F14 y F15. Registrados para sus features: F6 (JAVA-003) y F7/F9/F10
(JAVA-005).
