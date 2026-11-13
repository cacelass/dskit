package {{ base_package }}.batch;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.repeat.RepeatStatus;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

/**
 * Job semilla del proyecto: demuestra el ciclo Job -> Step -> Tasklet y deja
 * el JobRepository (esquema BATCH_*) inicializado y probado por contextLoads.
 * El agente `batch` es el dueño de este directorio (ver contracts.py).
 */
@Configuration
public class DemoJobConfig {

    @Bean
    public Job demoJob(JobRepository jobRepository, Step demoStep) {
        return new JobBuilder("demoJob", jobRepository)
                .start(demoStep)
                .build();
    }

    @Bean
    public Step demoStep(JobRepository jobRepository, PlatformTransactionManager transactionManager) {
        return new StepBuilder("demoStep", jobRepository)
                .tasklet((contribution, chunkContext) -> {
                    System.out.println("demoJob: arnes listo — sustituye este tasklet por el job real");
                    return RepeatStatus.FINISHED;
                }, transactionManager)
                .build();
    }
}
