#include "zdis.h"
#include <stdio.h>
#include <string.h>
static unsigned char code[16];
static char text[256];
static unsigned pos;
static int rd(struct zdis_ctx*c,uint32_t a){(void)c;return a<16?code[a]:-1;}
static bool put(struct zdis_ctx*c,enum zdis_put k,int32_t v,bool il){(void)c;(void)il;if(k==ZDIS_PUT_CHAR)text[pos++]=v;else if(k==ZDIS_PUT_MNE_SEP)text[pos++]=' ';else if(k==ZDIS_PUT_ARG_SEP)text[pos++]=',';else if(k==ZDIS_PUT_OFF)pos+=snprintf(text+pos,256-pos,"%+d",v);else if(k!=ZDIS_PUT_END)pos+=snprintf(text+pos,256-pos,"$%X",v);text[pos]=0;return pos<240;}
const char* disassemble(const unsigned char*b,int adl){memcpy(code,b,16);pos=0;text[0]=0;struct zdis_ctx c={.zdis_read=rd,.zdis_put=put,.zdis_adl=adl,.zdis_implicit=true};zdis_put_inst(&c);return text;}
int instruction_size(const unsigned char*b,int adl){memcpy(code,b,16);struct zdis_ctx c={.zdis_read=rd,.zdis_put=put,.zdis_adl=adl};return zdis_inst_size(&c);}
