# SPEC-JAVA — Arnés dskit para Java (Spring Boot / Spring Batch)

Estado: propuesta (v0.1) · sin implementar
Backlog: JAVA-001..JAVA-015 (ver ROADMAP.md)
Backlog y estado: ROADMAP.md

---

## 1. Objetivo

Adaptar el arnés dskit —el sistema que gobierna cómo trabajan los agentes
sobre un proyecto— para que genere y gobierne proyectos **Java con Spring Boot
y Spring Batch**, sin perder la promesa central del arnés: *ninguna feature se
marca `done` sin que la puerta pase en verde y sin evidencia real del comando
que lo demuestra*.

## 2. Decisiones previas (D)

- **D1 — Opción A: plano de control Python + template Java.** Los agentes del
  arnés son un plano de control, no el proyecto; se mantienen en Python (uv),
  igual que un proyecto Java usa Node para prettier. **No se hace port a
  JVM**: reconstruiría el foso (evals + suite de ~677 tests) desde cero.
  Confirmado por el spike de Fase 0 (ver §8): divergencia medida del núcleo de
  gobierno = **0 líneas**, `harness` eval 14/14 y `contracts` en verde sobre un
  proyecto Java.
- **D2 — El núcleo de gobierno no se toca.** `harness` (featureslist,
  claim/release, prioridad), rúbrica GATE-1..4, escalera de fricción, μ.cert y
  `contracts` como mecanismo son agnósticos de lenguaje: se heredan tal cual.
- **D3 — RAG no se toca** (restricción del usuario). Indexa `src/main/java`
  igual que indexaba código Python.
- **D4 — Dominios de primera clase.** Transacciones, semántica operativa de
  Spring Batch, migraciones, observabilidad y concurrencia se diseñan *con* el
  template (agente + contrato + rúbrica + plantillas de backlog), no después.
  Son los dominios donde un arnés que no los conoce da por bueno trabajo que
  falla en producción — y un arnés que vende garantías falsas es peor que
  ninguno.
- **D5 — Sustitución con ganancia.** PIT sustituye a `tools/mutate.py` (AST
  casero); JaCoCo a pytest-cov; Spotless/Checkstyle a ruff; Error Prone +
  NullAway a mypy; OWASP dependency-check + Trivy a bandit/pip-audit; ArchUnit
  a graphify. En cada caso la herramienta JVM es igual o más madura: la capa
  de fiabilidad mejora.
- **D6 — Makefile como fachada fina.** Un target make = un comando `./mvnw`
  (o el wrapper Gradle). Cero lógica en el Makefile: la lógica vive en los
  plugins de Maven/Gradle, que es donde un desarrollador Java espera
  encontrarla.

## 3. Alcance por capa

### 3.1 Template copier — JAVA-001

**Criterios**

- Variables nuevas en `copier.yml`: `build_tool` (maven|gradle),
  `java_version` (17|21|25), `base_package` + `groupId`/`artifactId`,
  `framework` (spring-boot-web | spring-boot-batch | spring-boot-web+batch |
  quarkus | plain), `db` (postgres|mysql|h2), `migrations`
  (flyway|liquibase|none), `use_security`, `use_testcontainers`, `use_pit`,
  `use_archunit`, `use_observability`. `use_kafka` queda en fase 2.
- Los perfiles `minimo|estandar|completo|manual` se reutilizan con defaults
  derivados; el gating por `_exclude` funciona igual que hoy.
- Estructura generada: `src/main/java/<paquete>/{controller,service,repository,domain,config,batch}`
  + `src/main/resources/` (+ `db/migration/` si migrations) + `src/test/java/`.
- `pom.xml` con spring-boot-starter-parent, spring-boot-maven-plugin,
  spring-batch, spring-data-jpa, flyway/liquibase y testcontainers según los
  flags; wrappers `mvnw`/`gradlew` incluidos.
- Un render `--defaults` (perfil estandar) termina sin preguntar y **sin
  instalar dependencias** (regla de perfiles actual: `make setup` lo hace).
- `.copier-answers.yml` captura las respuestas para `copier update`.

### 3.2 Puerta — JAVA-002

**Criterios**

- `init.sh` verifica JDK (versión >= la elegida, JAVA_HOME) y que el wrapper
  existe y es ejecutable.
- Ejecuta `./mvnw -q verify`; si falla, el agente PARA — misma filosofía que
  la puerta Python.
- Exige un test `contextLoads()` (`@SpringBootTest`) que arranque el
  ApplicationContext; contexto que no arranca = puerta roja.
- Con `migrations` activo: `flyway validate` (o liquibase) limpio sobre la BD
  de test.
- Con batch activo: esquema `BATCH_*` presente en la BD de test (o
  `JobRepository` en memoria en el perfil de test) y registro de jobs no roto.
- La evidencia que exige `harness finish` sigue siendo salida real de comando
  (regla OMP-008: se rechaza "ok"/"los tests pasan").

### 3.3 Backlog — JAVA-003

**Criterios**

- Plantillas de evidencia Java: `./mvnw test -Dtest=<Clase>`, `./mvnw -pl
  <módulo> verify`.
- Plantillas batch: *"el job corre end-to-end sobre dataset controlado"*,
  *"relanzar con los mismos job parameters no duplica"*, *"writer idempotente"*.
- Plantillas migraciones: *"migración aplicada limpiamente en base vacía y en
  base con datos"*.
- El esquema de `featureslist.json` no cambia; solo cambian los seeds y
  plantillas.

### 3.4 Agentes que razonan — JAVA-004

**Criterios**

- `lider.md`: protocolo `./mvnw`, decisión package-by-feature vs by-layer, y
  batch como dominio de primera clase (no como extra).
- `implementer.md`: DI por constructor, `@Transactional`, no cargar datasets
  completos en memoria, records/immutabilidad.
- `reviewer.md`: criterios R Java — N+1, transacciones en writers, idempotencia,
  restartability, Bean Validation, `@ControllerAdvice`.
- `explorer.md`: navegación de módulos Maven/Gradle y paquetes.

### 3.5 Núcleo ejecutor: reescritura y poda — JAVA-005

**Criterios**

- Sobreviven intactos (11): git, review, docker, integration, installer,
  supervisor, research, audit, secrets, harness, memory.
- Reescritos con equivalente JVM (10): test (JUnit5+JaCoCo), doctor (pom/JDK/m2),
  dependency (OWASP + versions-maven + convergencia/enforcer), cicd, make,
  refactor, doc/documentation (Javadoc), graph (ArchUnit/JDeps), env, plan.
- Podados (4): data, ml, mlflow, notebook — sus contratos permanecen en
  CONTRACTS sin registro (patrón ya tolerado por `validate_contracts`).
- `mutation` deja de usar el AST casero y pasa a envolver PIT (ver JAVA-012).
- Cada agente reescrito conserva la forma AgentResult/can_handle/best_action/
  Contract y su suite de tests portada.

### 3.6 Agente batch — JAVA-006 (dominio nuevo)

**Criterios**

- Nuevo agente `batch`: dueño de configuración Job/Step, chunk size, retry/skip,
  esquema `BATCH_*`, job parameters, launcher y scheduling.
- Acciones: `validate_job` (restartability + idempotencia), `run_job` (dry-run
  sobre dataset controlado), `explain_failure` (JobExecution/StepExecution),
  `checkpoint` (ExecutionContext).
- Contrato: owns `*/batch/` y sus migraciones `BATCH_*`; cannot: tocar
  entidades de dominio (son de `migrations`/implementer).
- Caso canónico con test: un writer sin transacción → `validate_job` lo rechaza
  con motivo; un job relanzado con mismos parámetros que duplica filas → rechazo.

### 3.7 Agente migrations — JAVA-007 (dominio nuevo)

**Criterios**

- Nuevo agente `migrations`: dueño de `db/migration/`.
- Acciones: `create` (V<n>__*.sql), `validate`, `status`, `undo` (solo con
  script de rollback previo).
- Rechaza: editar una migración ya aplicada (checksum cambiado),
  `out-of-order` sin bandera explícita, `down` destructivo sin revisión.
- Test: checksum cambiado → `success=false` con motivo legible.

### 3.8 Agente security — JAVA-008 (dominio nuevo)

**Criterios**

- Nuevo agente `security`: dueño de la config de Spring Security (JWT, CORS) y
  de la sección security de `application.yml`.
- Gate de exposure: en build de producción, los management endpoints no son
  accesibles públicamente (test de actuator exposure — familia real de CVEs).
- Colabora con `secrets`: nunca loguea ni commitea secretos (regla existente).

### 3.9 Agente api — JAVA-009 (reescritura de dominio)

**Criterios**

- `api` reescrito: controllers, DTOs + Bean Validation, `@ControllerAdvice`,
  OpenAPI generado.
- Versionado de API (`/api/v1`) con criterio de breaking change en el reviewer.
- Smoke: contexto arranca y `/actuator/health` responde.

### 3.10 Agente architecture — JAVA-010 (dominio nuevo)

**Criterios**

- Nuevo agente `architecture`: dueño de tests ArchUnit (límites de capas,
  dependencias entre módulos, ciclos).
- Multi-módulo: propiedad por módulo en los contratos; `touched_files` acepta
  rutas por módulo.
- Test que lo demuestra: dependencia controller→repository directa viola el
  límite y el test ArchUnit del template lo detecta.

### 3.11 Observabilidad — JAVA-011 (dominio nuevo)

**Criterios**

- Nuevo agente `ops`: dueño de Actuator + Micrometer + Logback.
- Métricas por step de batch (duración, tasa de error), traceId en logs (MDC),
  endpoint Prometheus, logging estructurado JSON por defecto.
- Rúbrica: servicio sin health check real (más allá de `contextLoads`) → no
  `done`.

### 3.12 Pipeline de calidad — JAVA-012

**Criterios**

- `make test` → `./mvnw test` + JaCoCo con umbral ≥80% enforce.
- `make lint` → Spotless check + Checkstyle/PMD; `make format` → Spotless apply.
- `make typecheck` → compilación `-Werror` + Error Prone + NullAway.
- `make security` → OWASP dependency-check + Trivy + SBOM (cyclonedx).
- `make mutation` → PIT con `targetClasses` acotado por módulo.
- `make crap` → crap4j (o CRAP con JaCoCo + complejidad de PMD).
- `make audit` → PMD CPD + ArchUnit.
- Nuevos: `make migrations`, `make batch-run`, `make context-check`.
- Todos los targets son fachada sobre `./mvnw` (D6).

### 3.13 CI y release — JAVA-013

**Criterios**

- Workflow: `./mvnw verify` con caché `.m2`, matriz JDK, service containers
  (Postgres) para Testcontainers.
- Upload de JaCoCo y PIT; SBOM + Trivy en cada push.
- Release: versionado semver del artefacto + publish a GitHub Packages /
  Maven Central (historia de release nueva — el proyecto Python no publica).
- El validador de renders del template cubre el template Java.

### 3.14 Rúbrica — JAVA-014

**Criterios**

- GATE-1 Java: `./mvnw verify` verde + `contextLoads` + migraciones validadas
  + (batch) job de prueba sobre dataset controlado + check de actuator exposure.
- R-criterios nuevos: transacciones (límites, auto-invocación, aislamiento),
  concurrencia/thread-safety, N+1, idempotencia batch, restartability,
  versionado de API, records/immutabilidad.
- GATE-2..4, veredicto del reviewer y μ.cert ≥ 0.6 sin cambios.
- Casos canónicos con test: writer sin transacción y job no reiniciable →
  `harness finish` rechazado.

### 3.15 DX — JAVA-015

**Criterios**

- El reviewer se integra como check/comentarios de GitHub PR, no solo como
  puerta interna del arnés.
- Config IntelliJ: code style sincronizado con Spotless/Checkstyle y run
  configurations en el template.
- Escalera de fricción remapeada: mergear por PR no exige confirm-string;
  `critical` = tag/release/publish (lo realmente destructivo en el flujo Java).
- Hot reload (Spring DevTools) documentado en el bucle local.

---

## 4. Fuera de alcance

- Port del plano de control a JVM (D1).
- ML/DS en Java (Tribuo/DL4J): `data`/`ml` se podan, no se traducen.
- LSP/DAP nativo, GraalVM native, Kafka streaming en batch (`use_kafka`, fase 2).
- Redis/session stores y ACP.

## 5. Riesgos (R)

- **R1 — Toolchain.** El equipo Java necesita uv/Python solo para el plano de
  control. Mitigación: precedente Node/prettier en proyectos Java; el plano de
  control es empaquetable como CLI autocontenido.
- **R2 — Fricción vs flujo PR.** La escalera de fricción actual asume un agente
  operando git directo; un equipo Java mergea por PR. Mitigación: JAVA-015.
- **R3 — Copier mirror cacheado.** Los renders de prueba usan lo pusheado, no
  el árbol local. Mitigación: copiar template+copier.yml a tmp sin `.git`
  (práctica ya anotada en memory.md).
- **R4 — Suite sobre template sin renderizar.** Jinja2 rompe el parser; se
  mantiene el flujo copiar-a-tmp + quitar `{% raw %}` con sed, ahora sobre el
  template Java.
- **R5 — PIT es lento en proyectos grandes.** Mitigación: `targetClasses`
  acotado por módulo y PIT fuera del `verify` por defecto.
- **R6 — Contratos huérfanos de agentes podados.** Ya tolerado por
  `validate_contracts` (patrón de los perfiles minimo/estandar).

## 6. Plan de fases

- **Fase 0 — Esqueleto:** JAVA-001 + JAVA-002. Un render estandar Java que
  pasa la puerta (`mvnw verify` + `contextLoads`).
- **Fase 1 — Núcleo:** JAVA-005 + JAVA-012 + JAVA-003. Agentes reescritos,
  pipeline de calidad JVM, plantillas de backlog.
- **Fase 2 — Dominios:** JAVA-006..JAVA-011. batch, migrations, security, api,
  architecture, observabilidad — cada uno con agente + contrato + tests.
- **Fase 3 — Gobierno y adopción:** JAVA-013 + JAVA-014 + JAVA-004 + JAVA-015.
  CI/release, rúbrica Java, agentes que razonan, DX.

Cada feature sigue el flujo SDD del arnés: backlog → `write_feature` (Gherkin)
→ `approve` (puerta humana) → TDD + evidencia → `finish` con rúbrica.

## 7. Métrica de éxito

- Un render `estandar` Java: `./init.sh` verde, `./mvnw verify` verde, JaCoCo ≥80%.
- `uv run python -m agents.evals.runner` verde sobre el template Java.
- Los 21 agentes del núcleo con contrato; los 6 dominios nuevos con agente +
  contrato + tests + workflow skill.
- El reviewer rechaza (con test que lo demuestra) un writer sin transacción y
  un job no reiniciable — los dos casos canónicos que hoy aprobaría.

## 8. Arquitectura física (resuelta en Fase 0)

**Decisión: A1 — un solo árbol `template/` con variable `language`
(python|java).** El contenido Java se añade al mismo template y se activa con
`_exclude`; los ficheros compartidos (init.sh, Makefile, AGENTS.md, prompts)
llevan condicionales `{% if language == ... %}` solo donde es imprescindible.
El núcleo de gobierno queda en una única fuente de verdad.

Evidencia del spike (Fase 0, `/tmp/dskit-spike-java`):

| Comprobación | Resultado |
|---|---|
| `./init.sh` sobre proyecto Java (JDK 17 + `./mvnw verify` + `contextLoads`) | **verde** |
| `agents/`, `harness/`, `.opencode/`, `AGENTS.md` vs render Python | **diff = 0 líneas** |
| `agents.evals.runner --harness` | **14/14 passed** |
| `agents.evals.runner --contracts` | **PASS** |
| `agents.evals.runner --smoke` | 9/21 vs 11/21 del render Python: las 2 diferencias son `dependency` y `env` (buscan `pyproject.toml`) + `doctor` 3/8 — los tres ya están en la lista de reescritura de JAVA-005 |
| `_subdirectory` con Jinja | **soportado** (renderiza `{{ language }}`), pero descartado: obligaría a duplicar el núcleo en dos árboles |

Consecuencias:

- `language` es una variable nueva de `copier.yml` (default `python`, para no
  romper el uso actual) y añade una dimensión a la matriz de CI (un combo Java
  mínimo; JAVA-013 amplía).
- Los ficheros Python-only se excluyen con `_exclude` cuando `language == 'java'`
  y viceversa; no se mueve ningún fichero existente de sitio.
- Las variables de DS (`ml_type`, `nn_model`, ...) llevan
  `when: "{{ language == 'python' }}"`; las nuevas de Java llevan
  `when: "{{ language == 'java' }}"`.
- `build_tool` arranca con `maven` como única opción implementada; `gradle`
  queda para una feature posterior (JAVA-001b) hasta tener su árbol verificado.
