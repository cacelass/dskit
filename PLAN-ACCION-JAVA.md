# PLAN-ACCION-JAVA — Qué hacer tras el informe E2E

Basado en `TEST-PLAN-JAVA.md` (resultados Nov 2026) y `PLAN-JAVA.md` (§9).
Fecha: Nov 2026 · Estado: propuesta para ejecutar.

---

## 1. Análisis del informe

### Qué demuestra la prueba

- El **núcleo del arnés funciona en Java**: render, puerta
  (`./mvnw verify` + `contextLoads`), backlog, `finish` con GATE-1..4 y
  evals (`harness` 14/14, `contracts` PASS).
- El **template genera proyectos Spring Boot/Batch reales**: 5 combos
  (estandar, web+batch+postgres, solo web, minimo, Java 21) y un procesador
  de pedidos con chunk processing, tests end-to-end y ejecución `java -jar`.
- **La puerta muerde**: con un test roto, `harness finish` rechaza el cierre.
- **8 bugs reales corregidos** (F1, F2, F3, F4, F5, F8, F11, F14): la mayoría
  solo aparecen en Windows o con jobs reales — el CI Linux no los habría visto.

### Qué queda abierto

| Tipo | Hallazgo | Destino |
|---|---|---|
| Feature | Backlog semilla de DS en proyectos Java (F6) | JAVA-003 |
| Feature | `commit_feature` sin bump de `pom.xml` (F7) | JAVA-005 |
| Feature | `doctor`/`env` con checks Python (F9) | JAVA-005 |
| Feature | `suggest_commit_message` ignora untracked (F10) | JAVA-005 |
| Entorno | `make` no instalado en Windows (F12) | — (CI Linux) |
| Entorno | `prompts_sync` en render con `--skip-tasks` (F13) | — |

### Límites de la prueba (lo que NO cubre)

1. **Pipeline de calidad JVM**: no hay JaCoCo, Spotless, PIT, OWASP ni CRAP
   (JAVA-012). La promesa «done con evidencia» hoy solo cubre build+tests.
2. **CI del fork**: la matriz de dskit es Python-only y el fork tiene Actions
   desactivados (JAVA-013). El badge del README aún no es fiable.
3. **Agentes**: siguen siendo Python/DS (`test` ejecuta pytest, `dependency`
   consulta PyPI, `doctor` busca `pyproject.toml`).
4. **Dominios**: batch/migrations/security/api/architecture/observabilidad no
   tienen agente dueño (JAVA-006..011).
5. **Ejecución real**: Postgres solo se compiló (no se ejecutó contra un
   servidor), JDK 21 solo se renderizó, sin `copier update`, sin render
   interactivo/manual, sin Docker/Testcontainers en marcha.

**Diagnóstico:** el esqueleto y el gobierno están probados; lo que falta es la
capa que convierte el arnés en *garantía* para un equipo Java: pipeline de
calidad, agentes Java y CI. Ahí se concentra el valor.

---

## 2. Priorización

| Prioridad | Acción | Impacto | Esfuerzo | Depende de |
|---|---|---|---|---|
| **P0** | A0.1 JAVA-003 — semilla de backlog Java | Alto | S | — |
| **P0** | A0.2 JAVA-005a — fixes pequeños de agentes (commit/doctor/env) | Alto | S-M | — |
| **P1** | A1.1 JAVA-012 — pipeline de calidad JVM | Muy alto | M | P0 |
| **P1** | A1.2 JAVA-013 — CI Java + Actions del fork | Muy alto | M | A1.1 |
| **P1** | A1.3 JAVA-005b — reescritura/poda de agentes | Muy alto | L | P0 |
| **P2** | A2.1 JAVA-006 — agente `batch` | Muy alto | L | A1.3 |
| **P2** | A2.2 JAVA-007 — agente `migrations` | Alto | M | A1.3 |
| **P2** | A2.3 JAVA-008 — agente `security` | Alto | M | A1.3 |
| **P2** | A2.4 JAVA-011 — observabilidad (`ops`) | Alto | M | A1.3 |
| **P2** | A2.5 JAVA-009 — agente `api` Spring | Medio | M | A1.3 |
| **P2** | A2.6 JAVA-010 — agente `architecture` (ArchUnit) | Medio | M | A1.3 |
| **P3** | A3.1 JAVA-014 — rúbrica Java | Alto | M | A2.1–A2.4 |
| **P3** | A3.2 JAVA-004 — agentes que razonan (prompts) | Alto | S-M | A3.1 |
| **P3** | A3.3 JAVA-015 — DX (PR, IntelliJ, fricción) | Medio | M | A3.1 |
| **P4** | A4.1 — decisión: eliminar el árbol Python/DS | Estratégico | M | A1.2 |
| **P4** | A4.2 JAVA-001b — Gradle | Bajo | M | — |
| **P4** | A4.3 — segunda ronda E2E (Postgres real, JDK 21, update) | Alto | S | A1.2 |

---

## 3. Detalle de acciones

### P0 — Cerrar lo abierto del E2E

**A0.1 — JAVA-003: semilla de backlog Java**
`harness/featureslist.json` condicional por `language`:
`SCOPE-001` (objetivo + métrica del servicio/batch), `ARCH-001` (arquitectura
y paquetes), `DB-001` (modelo + migraciones), `JOB-001` (job con
restartability, si batch), `API-001` (contrato REST, si web), `SEC-001` (si
security), `OBS-001` (si observability), `CI-001`.
**Done:** `harness next` en render Java propone la semilla Java; `init.sh`
valida el JSON en ambos idiomas; `validate_template.py` 0 bugs.
**Esfuerzo:** S · **Riesgo:** bajo (JSON condicional).

**A0.2 — JAVA-005a: fixes pequeños de agentes**
- `git commit_feature`: bump de `<version>` en `pom.xml` y del badge del
  README generado (hoy `next_version=null`).
- `git suggest_commit_message`: incluir archivos untracked
  (`git status --porcelain`).
- `doctor`/`env`: checks Java (`pom.xml`, JDK, `mvnw`, `target/`,
  `application.yml`) en vez de `pyproject.toml`/`.venv`.
**Done:** tests unitarios de cada fix + E2E sobre el render Java.
**Esfuerzo:** S-M · **Riesgo:** bajo.

### P1 — Hacer el template fiable para un equipo Java

**A1.1 — JAVA-012: pipeline de calidad JVM**
- JaCoCo con umbral (≥80% líneas, `check` en `verify`).
- Spotless (`apply`/`check`) + Checkstyle/PMD.
- Error Prone + NullAway (compilación `-Werror`).
- OWASP dependency-check + SBOM (cyclonedx) + Trivy.
- PIT (`make mutation`, `targetClasses` por módulo) y CRAP (crap4j o
  JaCoCo+PMD).
- `make check` = verify + cobertura + lint; `make security`; `make mutation`.
**Done:** targets ejecutados sobre el render; PIT mata un mutante sembrado;
`make check` en verde; documentado en README/Makefile.
**Esfuerzo:** M · **Riesgo:** PIT lento (acotar `targetClasses`), falsos
positivos de OWASP (suppressions).

**A1.2 — JAVA-013: CI Java**
- Workflow del template Java: `setup-java` (17 y 21), caché `.m2`,
  `./mvnw verify`, JaCoCo, PIT opcional, SBOM + Trivy.
- Matriz de dskit: job `smoke-java` (setup-java) o combo Java en
  `gen_smoke_matrix`; `ci-generado` con un render Java.
- Activar Actions en el fork (paso manual) y validar el badge.
**Done:** CI verde en el fork; el workflow que se entrega al usuario pasa en
un proyecto generado.
**Esfuerzo:** M · **Riesgo:** tiempo de Maven en Actions (caché), forks con
Actions desactivados.

**A1.3 — JAVA-005b: reescritura y poda de agentes**
- Reescribir: `test` (JUnit/JaCoCo), `dependency` (Maven/OWASP), `cicd`
  (workflow Java), `make` (targets Java), `doc` (Javadoc), `graph`
  (ArchUnit/JDeps), `env`, `plan`, `refactor`.
- Podar: `data`, `ml`, `mlflow`, `notebook` (+ prompts/tests; contratos
  tolerados).
- `contracts.py`: recursos Java (`pom.xml`, `application.yml`,
  `db/migration/`, configs de batch).
- Actualizar benchmarks de routing, prompts y conteo de agentes.
**Done:** `agents.evals.runner` verde en render Java; agentes podados
ausentes; `prompts-check` en CI.
**Esfuerzo:** L · **Riesgo:** regresiones (portar tests), contratos
huérfanos (ya tolerado).

### P2 — Dominios Java (en este orden)

| Acción | Qué añade | Caso canónico |
|---|---|---|
| A2.1 JAVA-006 `batch` | Job/Step, chunk, retry/skip, `BATCH_*`, restartability, idempotencia | writer sin transacción → rechazo; job relanzado que duplica → rechazo |
| A2.2 JAVA-007 `migrations` | Flyway/Liquibase, checksum, undo, out-of-order | editar migración aplicada → rechazo |
| A2.3 JAVA-008 `security` | Spring Security/JWT/CORS + gate de actuator expuesto | management endpoint público en prod → rechazo |
| A2.4 JAVA-011 `ops` | Actuator/Micrometer/OTel/MDC, métricas por step, logging JSON | servicio sin health real → no `done` |
| A2.5 JAVA-009 `api` | REST, DTOs + Bean Validation, OpenAPI, versionado | breaking change sin versión → rechazo |
| A2.6 JAVA-010 `architecture` | ArchUnit, límites de capas, multi-módulo | controller→repository directo → test ArchUnit falla |

Cada dominio: agente + tool + prompt + workflow skill + contrato + tests +
benchmarks de routing. **Esfuerzo:** M cada uno (batch L).

### P3 — Gobierno y adopción

- **A3.1 JAVA-014:** rúbrica Java — GATE-1 (`mvnw verify` + `contextLoads` +
  migraciones + job de prueba + actuator exposure) y R-criterios
  (transacciones, concurrencia, N+1, idempotencia, restartability, versionado
  de API, records/immutabilidad). Casos canónicos con test.
- **A3.2 JAVA-004:** `lider/explorer/implementer/reviewer.md` Java (protocolo
  `./mvnw`, idiomas Spring, patrones batch) + espejos `.claude/`.
- **A3.3 JAVA-015:** reviewer como check de PR, config IntelliJ sincronizada
  con Spotless/Checkstyle, escalera de fricción remapeada (merge por PR no es
  critical; `critical` = tag/release/publish), DevTools.

### P4 — Estratégico

**A4.1 — Decisión: eliminar el árbol Python/DS del fork**
El informe confirma que el foco es Java y que el árbol Python solo añade ruido
de mantenimiento. Opciones:
- **A (recomendada, tras A1.2):** eliminar el árbol Python (paquete, tests,
  tools, corpus ML, agentes DS), fijar `language=java` y simplificar los
  condicionales. El fork queda 100% Java.
- **B (actual):** mantenerlo como legacy excluido por `_exclude`, sin foco.
No hacerlo antes de A1.2: el CI Python actual es la red de seguridad hasta que
exista el CI Java.

**A4.2 — Gradle (JAVA-001b):** segundo build tool; no bloquea nada.
**A4.3 — Segunda ronda E2E:** Postgres real vía Testcontainers/Docker, JDK 21
ejecutado en CI, `copier update`, render interactivo y perfil `manual`.

---

## 4. Hitos

| Hito | Contenido | Criterio de salida |
|---|---|---|
| **H0** | A0.1 + A0.2 | Hallazgos F6/F7/F9/F10 cerrados; informe E2E sin abiertos |
| **H1** | A1.1 + A1.2 + A1.3 | `make check`/`mutation`/`security` funcionan; CI Java verde en el fork; agentes Java |
| **H2** | A2.1–A2.4 | batch/migrations/security/obs con agente y casos canónicos |
| **H3** | A2.5–A2.6 + A3.1–A3.3 | rúbrica Java, prompts y DX; flujo Gherkin→reviewer completo |
| **H4** | A4.1–A4.3 | repo 100% Java (si se aprueba), Gradle y segunda ronda E2E |

## 5. Riesgos del plan

- **R1 — PIT en CI:** lento. Mitigación: perfil `mutation` fuera de `verify`,
  `targetClasses` por módulo, ejecución nightly.
- **R2 — OWASP/Trivy:** falsos positivos y ruido. Mitigación: `suppressions.xml`
  versionado y revisión por PR.
- **R3 — Testcontainers:** requiere Docker en CI/local. Mitigación: perfil
  `integration` opcional; tests unitarios usan H2.
- **R4 — Reescritura de agentes:** regresiones. Mitigación: portar las suites
  existentes (663 tests de referencia) agente a agente, evals en cada paso.
- **R5 — Eliminar el árbol Python:** pierde la red de CI actual. Mitigación:
  hacerlo solo tras A1.2 y con el CI Java verde.
- **R6 — JDK 25 + Spring Boot 3.3:** compatibilidad no verificada.
  Mitigación: matriz CI 17/21; 25 solo cuando Boot lo soporte formalmente.

## 6. Próximo paso

Ejecutar **H0** en esta iteración: A0.1 (semilla de backlog Java) y A0.2
(fixes de `commit_feature`, untracked y `doctor`/`env`). Al cerrarlo, el
informe E2E queda sin hallazgos abiertos y se arranca A1.1 (pipeline de
calidad), que es lo que convierte la puerta en una garantía real para Java.
