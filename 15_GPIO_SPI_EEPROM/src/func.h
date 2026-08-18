

#include <stdio.h>
#include <stm32f10x.h>


#define PIN_NUM_0		0
#define PIN_NUM_1		1
#define PIN_NUM_2		2
#define PIN_NUM_3		3
#define PIN_NUM_4		4
#define PIN_NUM_5		5
#define PIN_NUM_6		6
#define PIN_NUM_7		7

void port_init(void);
void gpioA_Port(char value);
void gpioB_Port(char value);

void gpioA_High(char pin_num);
void gpioA_Low(char pin_num);
void gpioB_High(char pin_num);
void gpioB_Low(char pin_num);


//////////////// Time Base ////////////////////
void			Init_SysTick(void);
void			Delay_us(unsigned int nTime) ;
void			TimingDelay_ms_Decrement(void);
void			TimingDelay_10us_Decrement(void);
void			Delay_ms(unsigned int nTime);
unsigned int	CheckMillis(void);
unsigned int	CheckMicros(void);
///////////////////////////////////////////////

///////////////////////////////////////////////
 // UART1 //
#define    UART1_PORT			GPIOA
#define    UART1_TX_PIN         GPIO_Pin_9
#define    UART1_RX_PIN 		GPIO_Pin_10
#define    PUTCHAR_PROTOTYPE	int fputc(int ch, FILE *f)

void			Init_UART1(void);
///////////////////////////////////////////////



///////////////////////////////////////////////
// EXTI //
//void (*function)(void);
void attachInterrupt(uint8_t pinNo, volatile void (*userFunc)(void), EXTITrigger_TypeDef intMode);	  
///////////////////////////////////////////////



///////////////////////////////////////////////
// Timer2 update Interrupt per period us
void Init_Timer2UpdateInterrupt(uint16_t period);
volatile void userFnTim2(void);
///////////////////////////////////////////////



///////////////////////////////////////////////
// Timer3 update Interrupt per period us
void Init_Timer3UpdateInterrupt(uint16_t period);
volatile void userFnTim3(void);
///////////////////////////////////////////////



///////////////////////////////////////////////
// GPIO Read / Write
#define INPUT	0
#define OUTPUT  1
#define LOW		0
#define HIGH	1
#define GPIO_A	0x0A
#define GPIO_B	0x0B
#define GPIO_C	0x0C
#define ALL_PIN	0xFFFF

void pinMode(uint8_t portNo, uint16_t pinNo, uint8_t inOut);
void digitalWriteBit(uint8_t portNo, uint16_t pinNo, uint8_t LogicLevel);
void digitalWritePort(uint8_t portNo, uint16_t portVal);
unsigned int digitalReadBit(uint8_t portNo, uint16_t pinNo);
unsigned short digitalReadPort(uint8_t portNo);
///////////////////////////////////////////////





