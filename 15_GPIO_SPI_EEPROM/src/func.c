

#include "func.h"


// SysTick // 
volatile unsigned int tick10Micros = 0;
volatile unsigned int tickMillis = 0;
unsigned int TimingDelay_ms = 0;
unsigned int TimingDelay_10us = 0;



void port_init()
{
	RCC->APB2ENR |= (0x04 | 0x08);  // 0x04 -> PORTA, 0x08 -> PORTB
	
	GPIOA->CRL = 0x33333333;
	GPIOB->CRL = 0x33333333;
}


void gpioA_Port(char value)
{
	GPIOA->ODR=value;
}


void gpioB_Port(char value)
{
	GPIOB->ODR=value;
}

void gpioA_High(char pin_num)
{
	GPIOA->BSRR=0x01 << pin_num;
}

void gpioA_Low(char pin_num)
{
	GPIOA->BRR=0x01 << pin_num;
}

void gpioB_High(char pin_num)
{
	GPIOB->BSRR=0x01 << pin_num;
}

void gpioB_Low(char pin_num)
{
	GPIOB->BRR=0x01 << pin_num;
}






/// [][][][][][][][][][][][][][][][][][][][][][][][][][][]//
// Systick - millis / micros
// per 10 usec SysTick interrupt occur
void Init_SysTick()   
{ 
	// STK->LOAD : 1 / 72MHz * reloadVal = 10 usec
	// => reloadVal = 720
	(*(volatile unsigned int *)0xE000E014) = 0; 
	(*(volatile unsigned int *)0xE000E014) = 720; 
	
	// STK->CTRL : ClockSource=1(AHB), InterruptEnable, CounterEnable
	(*(volatile unsigned int *)0xE000E010) = 0; 
	(*(volatile unsigned int *)0xE000E010) = 7; 
}
//////////////////////////////////////////////////////////	 
void SysTick_Handler(void)
{
	TimingDelay_10us_Decrement();
	tick10Micros++;
	
	if((tick10Micros%100) == 0) {
		TimingDelay_ms_Decrement();
		tickMillis++;
	}
}
//////////////////////////////////////////////////////////// 
void TimingDelay_10us_Decrement()
{
	if(TimingDelay_10us != 0x00)
		TimingDelay_10us--;
} 
////////////////////////////////////////////////////////////		
void TimingDelay_ms_Decrement()
{
	if(TimingDelay_ms != 0x00)
		TimingDelay_ms--;
}
////////////////////////////////////////////////////////////		
void Delay_us(unsigned int nTime) 
{
	TimingDelay_10us = nTime / 10;
	while(TimingDelay_10us != 0) ;
}
////////////////////////////////////////////////////////////		
void Delay_ms(unsigned int nTime)
{
	TimingDelay_ms = nTime;
	while(TimingDelay_ms != 0) ;
}
////////////////////////////////////////////////////////////		
unsigned int CheckMillis()
{
	return tickMillis;
}
////////////////////////////////////////////////////////////   
unsigned int CheckMicros()
{
	return tick10Micros * 10;
}
//////////////////////////////////////////////////////////// 






// [][][][][][][][][][][][][][][][][][][][][][][][][][][]//
// UART1 - printf 
////////////////////////////////////////////////////////
void Init_UART1(void)
{
	 GPIO_InitTypeDef GPIO_InitStructure;
	 USART_InitTypeDef USART_InitStructure;

	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	 GPIO_InitStructure.GPIO_Pin = UART1_TX_PIN;
	 GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	 GPIO_Init(UART1_PORT, &GPIO_InitStructure);

	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	 GPIO_InitStructure.GPIO_Pin = UART1_RX_PIN;
	 GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	 GPIO_Init(UART1_PORT, &GPIO_InitStructure);
	 RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);

  /* Enable the USART1 Interrupt */
//	  NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
//	  NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
//	  NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
//	  NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
//	  NVIC_Init(&NVIC_InitStructure);

  /* Configure the USART1 */
	USART_InitStructure.USART_BaudRate = 115200;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;
	USART_Init(USART1, &USART_InitStructure);
	
  /* Enable the USART1 */
	USART_Cmd(USART1, ENABLE);
	
  /* Rx Not empty interrupt enable */
//	  USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
	
}
////////////////////////////////////////////////////////
PUTCHAR_PROTOTYPE
{
  /* Place your implementation of fputc here */
  /* e.g. write a character to the USART */  
  USART_SendData(USART1, (uint8_t) ch);

  /* Loop until the end of transmission */
//	while (USART_GetFlagStatus(USART1, USART_FLAG_TC) == RESET)  {}
  
  while(USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET ) ;

  return ch;
}
////////////////////////////////////////////////////////








// [][][][][][][][][][][][][][][][][][][][][][][][][][][]//
// External Interrupt : PORTC / pin10,11,12,13,14,15
//volatile void (*intFunc[6])(void);
volatile void (*intFunc[6])(void);
////////////////////////////////////////////////////////
void attachInterrupt(uint8_t pinNo, volatile void (*userFunc)(void), EXTITrigger_TypeDef intMode)  
{
	GPIO_InitTypeDef GPIO_InitStructure;
	EXTI_InitTypeDef EXTI_InitStructure;
	NVIC_InitTypeDef NVIC_InitStructure;
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
	GPIO_InitStructure.GPIO_Pin = 0x0400 << (pinNo%10);
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	GPIO_Init(GPIOC, &GPIO_InitStructure);

	RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
	
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOC, (uint8_t)pinNo);
	EXTI_InitStructure.EXTI_Line = 0x00400 << (pinNo%10);
	EXTI_InitStructure.EXTI_Mode = EXTI_Mode_Interrupt;
	EXTI_InitStructure.EXTI_Trigger = intMode;  
	EXTI_InitStructure.EXTI_LineCmd = ENABLE;
	EXTI_Init(&EXTI_InitStructure);

	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
	NVIC_InitStructure.NVIC_IRQChannel = EXTI15_10_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 3;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	if(pinNo<10 || pinNo>15)
		intFunc[pinNo%10] = 0;
	else
		intFunc[pinNo%10] = userFunc;
}
//////////////////////////////////////////////////////////// 
void EXTI15_10_IRQHandler(void)
{
	if(EXTI_GetITStatus(EXTI_Line10) != RESET)
	{
		EXTI_ClearITPendingBit(EXTI_Line10);
		intFunc[0]();
	}
	else if(EXTI_GetITStatus(EXTI_Line11) != RESET)
	{
		EXTI_ClearITPendingBit(EXTI_Line11);
		intFunc[1]();
	}
	else if(EXTI_GetITStatus(EXTI_Line12) != RESET)
	{
		EXTI_ClearITPendingBit(EXTI_Line12);
		intFunc[2]();
	}
	else if(EXTI_GetITStatus(EXTI_Line13) != RESET)
	{
		EXTI_ClearITPendingBit(EXTI_Line13);
		intFunc[3]();
	}
	else if(EXTI_GetITStatus(EXTI_Line14) != RESET)
	{
		EXTI_ClearITPendingBit(EXTI_Line14);
		intFunc[4]();
	}
	else if(EXTI_GetITStatus(EXTI_Line15) != RESET)
	{
		EXTI_ClearITPendingBit(EXTI_Line15);
		intFunc[5]();
	}
}
//////////////////////////////////////////////////////////// 






// [][][][][][][][][][][][][][][][][][][][][][][][][][][]//
// Timer2 - update interrupt per period [us]
//////////////////////////////////////////////////////////// 
void Init_Timer2UpdateInterrupt(uint16_t period)
{
	NVIC_InitTypeDef NVIC_InitStructure;
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);
	NVIC_InitStructure.NVIC_IRQChannel = TIM2_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	TIM_TimeBaseStructure.TIM_Prescaler = 2;	// PSC + 1 = 72MHz / TIM2 clock => 24MHz
	TIM_TimeBaseStructure.TIM_Period = period*24 - 1; // ARR + 1 : 3/72MHz * X = 20us => X = 480
	TIM_TimeBaseStructure.TIM_ClockDivision = 0;
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
	TIM_TimeBaseInit(TIM2, &TIM_TimeBaseStructure);
	TIM_Cmd(TIM2, ENABLE);
	TIM_ITConfig(TIM2, TIM_IT_Update, ENABLE);
}


void TIM2_IRQHandler(void)
{
	if(TIM_GetITStatus(TIM2, TIM_IT_Update) != RESET)
	{
		TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
		userFnTim2();
	}
}
//////////////////////////////////////////////////////////// 






// [][][][][][][][][][][][][][][][][][][][][][][][][][][]//
// Timer3 - update interrupt per period [us]
////////////////////////////////////////////////////////// 
void Init_Timer3UpdateInterrupt(uint16_t period)
{
	NVIC_InitTypeDef NVIC_InitStructure;
	TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;

	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);

	NVIC_InitStructure.NVIC_IRQChannel = TIM3_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
	NVIC_Init(&NVIC_InitStructure);

	TIM_TimeBaseStructure.TIM_Prescaler = 2;	// PSC + 1 = 72MHz / TIM2 clock => 24MHz
	TIM_TimeBaseStructure.TIM_Period = period*24 - 1; // ARR : 50us period => 50us interrupt
	TIM_TimeBaseStructure.TIM_ClockDivision = 0;
	TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
	TIM_TimeBaseInit(TIM3, &TIM_TimeBaseStructure);
	TIM_Cmd(TIM3, ENABLE);
	TIM_ITConfig(TIM3, TIM_IT_Update, ENABLE);
}



void TIM3_IRQHandler(void)
{
	if(TIM_GetITStatus(TIM3, TIM_IT_Update) != RESET)
	{
		TIM_ClearITPendingBit(TIM3, TIM_IT_Update);
		userFnTim3();
	}
}
//////////////////////////////////////////////////////// 





// [][][][][][][][][][][][][][][][][][][][][][][][][][][]//
// GPIO Read / Write
////////////////////////////////////////////////////////// 
void pinMode(uint8_t portNo, uint16_t pinNo, uint8_t inOut)
{
	GPIO_InitTypeDef GPIO_InitStructure;
	if(portNo == GPIO_A) 
		RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	else if(portNo == GPIO_B) 
		RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	else if(portNo == GPIO_C) 
		RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);

	if(pinNo == ALL_PIN)
		GPIO_InitStructure.GPIO_Pin = ALL_PIN;
	else
		GPIO_InitStructure.GPIO_Pin = 0x0001 << pinNo;
	
	if(inOut == OUTPUT) {
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
		GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	}
	else if(inOut == INPUT) {
		GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IN_FLOATING;
	}

	if(portNo == GPIO_A)
		GPIO_Init(GPIOA, &GPIO_InitStructure);
	else if(portNo == GPIO_B)
		GPIO_Init(GPIOB, &GPIO_InitStructure);
	else if(portNo == GPIO_C)
		GPIO_Init(GPIOC, &GPIO_InitStructure);
}


void digitalWriteBit(uint8_t portNo, uint16_t pinNo, uint8_t LogicLevel)
{
	if(portNo == GPIO_A)
		GPIO_WriteBit(GPIOA, 0x0001<<pinNo, (BitAction)LogicLevel);
	else if(portNo == GPIO_B)
		GPIO_WriteBit(GPIOB, 0x0001<<pinNo, (BitAction)LogicLevel);
	else if(portNo == GPIO_C)
		GPIO_WriteBit(GPIOC, 0x0001<<pinNo, (BitAction)LogicLevel);
}

void digitalWritePort(uint8_t portNo, uint16_t portVal)
{
	if(portNo == GPIO_A)
		GPIOA->ODR = portVal;
	else if(portNo == GPIO_B)
		GPIOB->ODR = portVal;
	else if(portNo == GPIO_C)
		GPIOC->ODR = portVal;
}

unsigned int digitalReadBit(uint8_t portNo, uint16_t pinNo)
{
	if(portNo == GPIO_A) 
		return (GPIOA->IDR & (0x0001<<pinNo));
	else if(portNo == GPIO_B) 
		return (GPIOB->IDR & (0x0001<<pinNo));
	else if(portNo == GPIO_C) 
		return (GPIOC->IDR & (0x0001<<pinNo));
	else
		return 0;
	
}

unsigned short digitalReadPort(uint8_t portNo)
{
	if(portNo == GPIO_A) 
		return ((uint16_t)GPIOA->IDR);
	else if(portNo == GPIO_B) 
		return ((uint16_t)GPIOB->IDR);
	else if(portNo == GPIO_C) 
		return ((uint16_t)GPIOC->IDR);
	return 0;

}
//////////////////////////////////////////////////////// 























