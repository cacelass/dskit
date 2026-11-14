package {{ base_package }};

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * Test semilla del job de demostracion. Existe para que el proyecto recien
 * generado cumpla el umbral de cobertura de JaCoCo sin editar nada: ejecuta
 * el ciclo Job -> Step y verifica que termina en COMPLETED.
 */
@SpringBootTest
@ActiveProfiles("test")
class DemoJobTest {

    @Autowired
    private JobLauncher jobLauncher;

    @Autowired
    @Qualifier("demoJob")
    private Job demoJob;

    @Test
    void demoJobTerminaEnCompletado() throws Exception {
        JobExecution execution = jobLauncher.run(
                demoJob,
                new JobParametersBuilder().addLong("run.id", System.nanoTime()).toJobParameters());

        assertThat(execution.getExitStatus().getExitCode()).isEqualTo("COMPLETED");
    }
}
