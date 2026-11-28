#include "cpu.h"
#include "control.h"
#include "interrupt.h"
#include "asic.h"
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
extern eZ80cpu_t cpu;
control_state_t control;
interrupt_state_t intrpt[2];
asic_state_t asic;
int test_trapped;
static unsigned keys[65536], used[65536], nused;
static unsigned char vals[65536];
typedef struct {unsigned kind,addr,value;} Event;
static Event events[16384];
static unsigned nevents,io_seed;
static bool started;
static unsigned slot(unsigned a) {unsigned k=(a*2654435761u)>>16;while(keys[k] && keys[k]!=a+1)k=(k+1)&65535;return k;}
void poke(unsigned a,unsigned v){a&=0xffffff;unsigned k=slot(a);if(!keys[k]){keys[k]=a+1;used[nused++]=k;}vals[k]=v;}
unsigned peek(unsigned a){return vals[slot(a&0xffffff)];}
static void event(unsigned k,unsigned a,unsigned v){if(nevents>=16384)abort();events[nevents++]=(Event){k,a,v};}
uint8_t mem_read_cpu(uint32_t a,bool fetch){cpu.cycles++;unsigned v=peek(a);if(!fetch)event(0,a&0xffffff,v);return v;}
void mem_write_cpu(uint32_t a,uint8_t v){cpu.cycles++;poke(a,v);event(1,a&0xffffff,v);}
uint8_t port_read_byte(uint16_t a){cpu.cycles++;unsigned v=(a^(a>>8)^io_seed)&255;event(2,a,v);return v;}
void port_write_byte(uint16_t a,uint8_t v){cpu.cycles++;event(3,a,v);}
bool unprivileged_code(void){return false;}
uint8_t bus_rand(void){return io_seed;}
uint32_t sched_event_next_cycle(void){return 1000000;}
void gui_console_printf(const char *s,...){(void)s;}
void gui_console_err_printf(const char *s,...){(void)s;}
void reset_case(unsigned seed){for(unsigned i=0;i<nused;i++){keys[used[i]]=0;vals[used[i]]=0;}nused=nevents=0;started=false;io_seed=seed;test_trapped=0;memset(&cpu,0,sizeof cpu);memset(intrpt,0,sizeof intrpt);memset(&control,0,sizeof control);asic.im2=true;cpu_clear_signals();}
void set_state(const unsigned *s){eZ80registers_t*r=&cpu.registers;r->AF=s[0];r->BC=s[1];r->DE=s[2];r->HL=s[3];r->_AF=s[4];r->_BC=s[5];r->_DE=s[6];r->_HL=s[7];r->IX=s[8];r->IY=s[9];r->SPL=s[10];r->PC=s[11];r->I=s[12];r->R=(uint8_t)((s[13]<<1)|(s[13]>>7));cpu.IEF1=s[14];cpu.IEF2=s[15];cpu.IM=s[16] ? s[16]+1 : 0;cpu.halted=s[17];cpu.ADL=s[18];r->MBASE=s[19];cpu.MADL=s[20];r->SPS=s[21];}
void get_state(unsigned *s){eZ80registers_t*r=&cpu.registers;unsigned t[]={r->AF,r->BC,r->DE,r->HL,r->_AF,r->_BC,r->_DE,r->_HL,r->IX,r->IY,r->SPL,cpu.ADL?r->PC:r->PC&65535,r->I,(uint8_t)((r->R>>1)|(r->R<<7)),cpu.IEF1,cpu.IEF2,cpu.IM ? cpu.IM-1 : 0,cpu.halted,cpu.ADL,r->MBASE,cpu.MADL,r->SPS};for(unsigned i=0;i<22;i++)s[i]=t[i]&(i==0||i==4||i==21?65535:0xffffff);}
unsigned run_step(unsigned event_kind){if(!started){cpu_flush(cpu.registers.PC,cpu.ADL);started=true;}if(event_kind==1)cpu.NMI=true;if(event_kind==2){intrpt[0].status=intrpt[0].enabled=1;}cpu_execute();return test_trapped;}
unsigned event_count(void){return nevents;}
void get_event(unsigned i,unsigned*out){out[0]=events[i].kind;out[1]=events[i].addr;out[2]=events[i].value;}
