struct funlist {
	char name[32];
	char func[32];
} funlist_st;

struct funlist cv181x_pin_func[] = {
	// A16 - UART0_TX
	{ "A160", "UART0_TX"},
	{ "A161", "CAM_MCLK1"},
	{ "A162", "PWM_4"},
	{ "A163", "A16"},
	{ "A164", "UART1_TX"},
	{ "A165", "AUX1"},
	{ "A167", "DBG_6"},

	// A17 - UART0_RX
	{ "A170", "UART0_RX"},
	{ "A171", "CAM_MCLK0"},
	{ "A172", "PWM_5"},
	{ "A173", "A17"},
	{ "A174", "UART1_RX"},
	{ "A175", "AUX0"},
	{ "A177", "DBG_7"},

	// A19 - JTAG_CPU_TMS
	{ "A190", "CV_2WTMS_CR_4WTMS"},
	{ "A191", "CAM_MCLK0"},
	{ "A192", "PWM_7"},
	{ "A193", "A19"},
	{ "A194", "UART1_RTS"},
	{ "A195", "AUX0"},
	{ "A196", "UART1_TX"},
	{ "A197", "VO_D_28"},

	// A18 - JTAG_CPU_TCK
	{ "A180", "CV_2WTCK_CR_4WTCK"},
	{ "A181", "CAM_MCLK1"},
	{ "A182", "PWM_6"},
	{ "A183", "A18"},
	{ "A184", "UART1_CTS"},
	{ "A185", "AUX1"},
	{ "A186", "UART1_RX"},
	{ "A187", "VO_D_29"},

	// A20 - JTAG_CPU_TRST
	{ "A200", "JTAG_CPU_TRST"},
	{ "A203", "A20"},
	{ "A206", "VO_D_30"},

	// A28 - IIC0_SCL
	{ "A280", "CV_SCL0"},
	{ "A281", "UART1_TX"},
	{ "A282", "UART2_TX"},
	{ "A283", "A28"},
	{ "A285", "WG0_D0"},
	{ "A287", "DBG_10"},

	// A29 - IIC0_SDA
	{ "A290", "CV_SDA0"},
	{ "A291", "UART1_RX"},
	{ "A292", "UART2_RX"},
	{ "A293", "A29"},
	{ "A295", "WG0_D1"},
	{ "A296", "WG1_D0"},
	{ "A297", "DBG_11"},

	// E0 - PWR_GPIO0
	{ "E00", "E0"},
	{ "E01", "UART2_TX"},
	{ "E02", "PWR_UART0_RX"},
	{ "E04", "PWM_8"},

	// E1 - PWR_GPIO1
	{ "E10", "E1"},
	{ "E11", "UART2_RX"},
	{ "E13", "EPHY_LNK_LED"},
	{ "E14", "PWM_9"},
	{ "E15", "PWR_IIC_SCL"},
	{ "E16", "IIC2_SCL"},
	{ "E17", "CV_4WTMS_CR_SDA0"},

	// E2 - PWR_GPIO2
	{ "E20", "E2"},
	{ "E22", "PWR_SECTICK"},
	{ "E23", "EPHY_SPD_LED"},
	{ "E24", "PWM_10"},
	{ "E25", "PWR_IIC_SDA"},
	{ "E26", "IIC2_SDA"},
	{ "E27", "CV_4WTCK_CR_2WTCK"},

	// B1 - ADC3
	{ "B11", "CAM_MCLK0"},
	{ "B12", "IIC4_SCL"},
	{ "B13", "B1"},
	{ "B14", "PWM_12"},
	{ "B15", "EPHY_LNK_LED"},
	{ "B16", "WG2_D0"},
	{ "B17", "UART3_TX"},

	// B2 - ADC2
	{ "B21", "CAM_MCLK1"},
	{ "B22", "IIC4_SDA"},
	{ "B23", "B2"},
	{ "B24", "PWM_13"},
	{ "B25", "EPHY_SPD_LED"},
	{ "B26", "WG2_D1"},
	{ "B27", "UART3_RX"},

	// B3 - ADC1
	{ "B33", "B3"},
	{ "B34", "KEY_COL2"},

	// B11 - VIVO_D10
	{ "B110", "PWM_1"},
	{ "B111", "VI1_D_10"},
	{ "B112", "VO_D_23"},
	{ "B113", "B11"},
	{ "B114", "RMII0_IRQ"},
	{ "B115", "CAM_MCLK0"},
	{ "B116", "IIC1_SDA"},
	{ "B117", "UART2_TX"},

	// B12 - VIVO_D9
	{ "B120", "PWM_2"},
	{ "B121", "VI1_D_9"},
	{ "B122", "VO_D_22"},
	{ "B123", "B12"},
	{ "B125", "CAM_MCLK1"},
	{ "B126", "IIC1_SCL"},
	{ "B127", "UART2_RX"},

	// B13 - VIVO_D8
	{ "B130", "PWM_3"},
	{ "B131", "VI1_D_8"},
	{ "B132", "VO_D_21"},
	{ "B133", "B13"},
	{ "B134", "RMII0_MDIO"},
	{ "B135", "SPI3_SDO"},
	{ "B136", "IIC2_SCL"},
	{ "B137", "CAM_VS0"},

	// B14 - VIVO_D7
	{ "B140", "VI2_D_7"},
	{ "B141", "VI1_D_7"},
	{ "B142", "VO_D_20"},
	{ "B143", "B14"},
	{ "B144", "RMII0_RXD1"},
	{ "B145", "SPI3_SDI"},
	{ "B146", "IIC2_SDA"},
	{ "B147", "CAM_HS0"},

	// B15 - VIVO_D6
	{ "B150", "VI2_D_6"},
	{ "B151", "VI1_D_6"},
	{ "B152", "VO_D_19"},
	{ "B153", "B15"},
	{ "B154", "RMII0_REFCLKI"},
	{ "B155", "SPI3_SCK"},
	{ "B156", "UART2_TX"},
	{ "B157", "CAM_VS0"},

	// B16 - VIVO_D5
	{ "B160", "VI2_D_5"},
	{ "B161", "VI1_D_5"},
	{ "B162", "VO_D_18"},
	{ "B163", "B16"},
	{ "B164", "RMII0_RXD0"},
	{ "B165", "SPI3_CS_X"},
	{ "B166", "UART2_RX"},
	{ "B167", "CAM_HS0"},

	// B17 - VIVO_D4
	{ "B170", "VI2_D_4"},
	{ "B171", "VI1_D_4"},
	{ "B172", "VO_D_17"},
	{ "B173", "B17"},
	{ "B174", "RMII0_MDC"},
	{ "B175", "IIC1_SDA"},
	{ "B176", "UART2_CTS"},
	{ "B177", "CAM_VS0"},

	// B18 - VIVO_D3
	{ "B180", "VI2_D_3"},
	{ "B181", "VI1_D_3"},
	{ "B182", "VO_D_16"},
	{ "B183", "B18"},
	{ "B184", "RMII0_TXD0"},
	{ "B185", "IIC1_SCL"},
	{ "B186", "UART2_RTS"},
	{ "B187", "CAM_HS0"},

	// B19 - VIVO_D2
	{ "B190", "VI2_D_2"},
	{ "B191", "VI1_D_2"},
	{ "B192", "VO_D_15"},
	{ "B193", "B19"},
	{ "B194", "RMII0_TXD1"},
	{ "B195", "CAM_MCLK1"},
	{ "B196", "PWM_2"},
	{ "B197", "UART2_TX"},

	// B20 - VIVO_D1
	{ "B200", "VI2_D_1"},
	{ "B201", "VI1_D_1"},
	{ "B202", "VO_D_14"},
	{ "B203", "B20"},
	{ "B204", "RMII0_RXDV"},
	{ "B205", "IIC3_SDA"},
	{ "B206", "PWM_3"},
	{ "B207", "IIC4_SCL"},

	// B21 - VIVO_D0
	{ "B210", "VI2_D_0"},
	{ "B211", "VI1_D_0"},
	{ "B212", "VO_D_13"},
	{ "B213", "B21"},
	{ "B214", "RMII0_TXCLK"},
	{ "B215", "IIC3_SCL"},
	{ "B216", "WG1_D0"},
	{ "B217", "IIC4_SDA"},

	// B22 - VIVO_CLK
	{ "B220", "VI2_CLK"},
	{ "B221", "VI1_CLK"},
	{ "B222", "VO_CLK1"},
	{ "B223", "B22"},
	{ "B224", "RMII0_TXEN"},
	{ "B225", "CAM_MCLK0"},
	{ "B226", "WG1_D1"},
	{ "B227", "UART2_RX"},

	// C18 - PAD_MIPI_TXM4
	{ "C180", "VI0_D_15"},
	{ "C181", "SD1_CLK"},
	{ "C182", "VO_D_24"},
	{ "C183", "C18"},
	{ "C184", "CAM_MCLK1"},
	{ "C185", "PWM_12"},
	{ "C186", "IIC1_SDA"},
	{ "C187", "DBG_18"},

	// C19 - PAD_MIPI_TXP4
	{ "C190", "VI0_D_16"},
	{ "C191", "SD1_CMD"},
	{ "C192", "VO_D_25"},
	{ "C193", "C19"},
	{ "C194", "CAM_MCLK0"},
	{ "C195", "PWM_13"},
	{ "C196", "IIC1_SCL"},
	{ "C197", "DBG_19"},

	// C20 - PAD_MIPI_TXM3
	{ "C200", "VI0_D_17"},
	{ "C201", "SD1_D0"},
	{ "C202", "VO_D_26"},
	{ "C203", "C20"},
	{ "C204", "IIC2_SDA"},
	{ "C205", "PWM_14"},
	{ "C206", "IIC1_SDA"},
	{ "C207", "CAM_VS0"},

	// C21 - PAD_MIPI_TXP3
	{ "C210", "VI0_D_18"},
	{ "C211", "SD1_D1"},
	{ "C212", "VO_D_27"},
	{ "C213", "C21"},
	{ "C214", "IIC2_SCL"},
	{ "C215", "PWM_15"},
	{ "C216", "IIC1_SCL"},
	{ "C217", "CAM_HS0"},

	// C16 - PAD_MIPI_TXM2
	{ "C160", "CV_4WTMS_CR_SDA0"},
	{ "C161", "VI0_D_13"},
	{ "C162", "VO_D_0"},
	{ "C163", "C16"},
	{ "C164", "IIC1_SDA"},
	{ "C165", "PWM_8"},
	{ "C166", "SPI0_SCK"},
	{ "C167", "SD1_D2"},

	// C17 - PAD_MIPI_TXP2
	{ "C170", "CV_4WTDI_CR_SCL0"},
	{ "C171", "VI0_D_14"},
	{ "C172", "VO_CLK0"},
	{ "C173", "C17"},
	{ "C174", "IIC1_SCL"},
	{ "C175", "PWM_9"},
	{ "C176", "SPI0_CS_X"},
	{ "C177", "SD1_D3"},

	// C14 - PAD_MIPI_TXM1
	{ "C140", "CV_4WTDO_CR_2WTMS"},
	{ "C141", "VI0_D_11"},
	{ "C142", "VO_D_2"},
	{ "C143", "C14"},
	{ "C144", "IIC2_SDA"},
	{ "C145", "PWM_10"},
	{ "C146", "SPI0_SDO"},
	{ "C147", "DBG_14"},

	// C15 - PAD_MIPI_TXP1
	{ "C150", "CV_4WTCK_CR_2WTCK"},
	{ "C151", "VI0_D_12"},
	{ "C152", "VO_D_1"},
	{ "C153", "C15"},
	{ "C154", "IIC2_SCL"},
	{ "C155", "PWM_11"},
	{ "C156", "SPI0_SDI"},
	{ "C157", "DBG_15"},

	// C12 - PAD_MIPI_TXM0
	{ "C121", "VI0_D_9"},
	{ "C122", "VO_D_4"},
	{ "C123", "C12"},
	{ "C124", "CAM_MCLK1"},
	{ "C125", "PWM_14"},
	{ "C126", "CAM_VS0"},
	{ "C127", "DBG_12"},

	// C13 - PAD_MIPI_TXP0
	{ "C131", "VI0_D_10"},
	{ "C132", "VO_D_3"},
	{ "C133", "C13"},
	{ "C134", "CAM_MCLK0"},
	{ "C135", "PWM_15"},
	{ "C136", "CAM_HS0"},
	{ "C137", "DBG_13"},
};
