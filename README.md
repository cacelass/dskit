# DSKIT-JAVA

**Template copier para proyectos Java (Spring Boot / Spring Batch) con arnés de IA.**

Fork de [dskit](https://github.com/cacelass/dskit) centrado en desarrollo Java.
El arnés —la capa que gobierna cómo trabajan los agentes sobre el proyecto— se
mantiene intacto: puerta de entrada, backlog verificable y una definición de
«hecho» que se aplica en código, no pidiéndosela al modelo.

![CI](https://github.com/Pedro0020/dskit-JAVA/actions/workflows/ci.yml/badge.svg)
[![based on dskit](https://img.shields.io/badge/based_on-dskit_by_cacelass-blueviolet)](https://github.com/cacelass/dskit)
![license](https://img.shields.io/badge/license-Apache--2.0-green)

> **Fork de [dskit](https://github.com/cacelass/dskit)** — repo original:
> `https://github.com/cacelass/dskit` — creado por
> [cacelass](https://github.com/cacelass) y publicado bajo Apache-2.0.
> Ver [CREDITS.md](CREDITS.md) y [Créditos y origen](#créditos-y-origen).

---

## Índice

- [Requisitos](#requisitos)
- [Inicio rápido](#inicio-rápido)
- [Variables](#variables)
- [Estructura generada](#estructura-generada)
- [El arnés](#el-arnés)
- [Make targets](#make-targets)
- [Estado de la adaptación](#estado-de-la-adaptación)
- [Créditos y origen](#créditos-y-origen)
- [License](#license)

## Requisitos

- **JDK 17+** (la plantilla admite 17, 21 y 25; elige `java_version`).
- **copier** para generar el proyecto: `pip install copier`.
- **uv** y **Python 3.10+** para el plano de control del arnés (los agentes
  son herramientas de desarrollo, no forman parte del artefacto Java).
- **Bash** (Git Bash o WSL en Windows) para ejecutar `./init.sh`.
- **Docker** opcional, solo si activas `use_testcontainers`.

## Inicio rápido

```bash
# Interactivo: responde language=java y las preguntas Java
copier copy --trust gh:Pedro0020/dskit-JAVA mi_proyecto

# No interactivo (perfil estandar: Spring Batch + H2 + Flyway)
copier copy --trust --defaults --data language=java gh:Pedro0020/dskit-JAVA mi_proyecto
cd mi_proyecto
./mvnw verify        # build + tests
./init.sh            # la puerta del arnés
```

Desde una copia local del repo:

```bash
copier copy --trust ./dskit-JAVA mi_proyecto
```

## Variables

| Variable | Valores | Descripción |
|---|---|---|
| `language` | `python` · `java` | `java` genera el árbol Spring Boot / Spring Batch |
| `project_name` | texto | Nombre del proyecto |
| `project_slug` | `[a-z0-9_]` | Nombre del artefacto / paquete |
| `base_package` | `com.empresa.proyecto` | Paquete base Java |
| `java_version` | `17` · `21` · `25` | Versión de Java (LTS) |
| `build_tool` | `maven` | Maven con wrapper (Gradle pendiente) |
| `framework` | `spring-boot` · `spring-boot-batch` · `spring-boot-web+batch` | Stack Spring |
| `db` | `h2` · `postgres` · `mysql` · `none` | Base de datos |
| `migrations` | `flyway` · `liquibase` · `none` | Migraciones de esquema |
| `use_security` | bool | Spring Security |
| `use_testcontainers` | bool | Tests de integración con contenedores |
| `use_pit` | bool | Mutation testing con PIT (pipeline en JAVA-012) |
| `use_archunit` | bool | Tests de arquitectura (JAVA-010) |
| `use_observability` | bool | Actuator + Micrometer + Prometheus |
| `proyecto_perfil` | `minimo` · `estandar` · `completo` · `manual` | Fija los defaults |

El perfil `estandar` activa `spring-boot-batch`, H2, Flyway, Testcontainers,
PIT y ArchUnit. En `minimo`/`estandar` no se instalan dependencias al generar
el proyecto: el primer paso es `./mvnw verify`.

## Estructura generada

```
mi_proyecto/
├── pom.xml
├── mvnw · mvnw.cmd · .mvn/
├── src/main/java/<paquete>/
│   ├── Application.java
│   └── batch/DemoJobConfig.java      (si el framework incluye batch)
├── src/main/resources/
│   ├── application.yml
│   └── db/migration/ | db/changelog/ (si hay migraciones)
├── src/test/java/<paquete>/ApplicationTests.java
├── src/test/resources/application-test.yml
├── harness/                          backlog + progreso del arnés
├── agents/                           plano de control (Python)
├── .opencode/agents/                 lider · explorer · implementer · reviewer
├── init.sh                           la puerta
└── Makefile                          fachada sobre ./mvnw
```

## El arnés

La regla que no se salta: **ninguna feature se marca `done` sin que
`./init.sh` pase en verde y sin evidencia real del comando que lo demuestra**.
No es una instrucción en un prompt: la aplica `harness finish` en Python.

```
./init.sh → harness/progress/ → harness/featureslist.json → implementar → revisar → done
```

- **`init.sh`** — JDK, wrapper de Maven, `./mvnw verify` y el test
  `contextLoads()` (el ApplicationContext tiene que arrancar).
- **`harness/featureslist.json`** — backlog con criterios verificables.
- **`.opencode/agents/`** — los cuatro agentes que razonan (markdown).
- **`agents/`** — los agentes que ejecutan (Python, plano de control).

```bash
make init            # ./init.sh
make backlog         # estado del backlog
make agents-list     # agentes disponibles
make agents-eval     # harness + contracts
```

## Make targets

| Target | Qué hace |
|---|---|
| `make setup` | resuelve dependencias (`dependency:go-offline`) |
| `make init` | ejecuta la puerta `./init.sh` |
| `make test` | `./mvnw test` |
| `make verify` | `./mvnw verify` |
| `make check` | `verify` + puerta |
| `make compile` | `./mvnw -q compile` |
| `make backlog` | estado de `harness/featureslist.json` |
| `make agents-list` | lista los agentes del plano de control |
| `make agents-doctor` | diagnóstico del arnés |
| `make agents-eval` | harness + contracts |
| `make prompts-sync` | regenera prompts desde el código y los contratos |
| `make prompts-check` | falla si un prompt se desincronizó |
| `make skills` | instala los prompts como skills en `.opencode/skills/` |
| `make assistants-sync` | espeja los subagentes a `.claude/agents/` |
| `make clean` | `./mvnw clean` |

## Estado de la adaptación

| Feature | Estado |
|---|---|
| JAVA-001 — template Java (Maven, Spring Boot/Batch, H2, Flyway, wrapper) | Hecha |
| JAVA-002 — puerta `./mvnw verify` + `contextLoads` | Hecha |
| JAVA-003 — plantillas de backlog Java | Pendiente |
| JAVA-005..011 — agentes Java: batch, migrations, security, api, architecture, observabilidad | Pendiente |
| JAVA-012 — pipeline de calidad (JaCoCo, Spotless, PIT, OWASP) | Pendiente |
| JAVA-013 — CI del template Java | Pendiente |

Alcance completo y criterios: [SPEC-JAVA.md](SPEC-JAVA.md) ·
[PLAN-JAVA.md](PLAN-JAVA.md).

El árbol Python original de la plantilla sigue disponible con
`language: python`, pero este fork no lo mantiene como foco.

**Verificado:** render `estandar` Java → `./init.sh` verde, `./mvnw verify`
verde, `harness` eval 14/14 y `contracts` PASS.

## Créditos y origen

Este proyecto es una **obra derivada** de [dskit](https://github.com/cacelass/dskit)
—`https://github.com/cacelass/dskit`—, creado por
[cacelass](https://github.com/cacelass) y publicado bajo Apache-2.0. Se
conservan la licencia y el aviso de copyright de la obra original.

Este fork se publica en
**[https://github.com/Pedro0020/dskit-JAVA](https://github.com/Pedro0020/dskit-JAVA)**
y está mantenido por **poganmart** desde 2026. Los cambios respecto al
original se detallan en [NOTICE](NOTICE), [CREDITS.md](CREDITS.md),
[SPEC-JAVA.md](SPEC-JAVA.md) y [PLAN-JAVA.md](PLAN-JAVA.md).

Si reutilizas este trabajo, mantén también la atribución a la obra original.

---

## License

Apache-2.0
