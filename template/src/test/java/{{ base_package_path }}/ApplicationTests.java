package {{ base_package }};

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * La prueba de humo de la puerta: si el ApplicationContext no arranca, el
 * proyecto no está en condiciones de trabajar y ./init.sh se pone en rojo.
 */
@SpringBootTest
@ActiveProfiles("test")
class ApplicationTests {

    @Test
    void contextLoads() {}
}
