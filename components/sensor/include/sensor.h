#pragma once

/* reads 4-20 mA transducer via ADC; maps 4 mA → 0 m, 20 mA → MAX_DEPTH_CM/100 m */
float sensor_read_level(void);
