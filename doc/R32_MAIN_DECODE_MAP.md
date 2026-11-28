# R32 主命令グループ対応

番号は保持された分類コード。命令の詳細動作は元のmcode分岐を維持する。

## Base

| 番号 | 定数 | 命令バイト（16進） | 元分岐のコメント |
|---|---|---|---|
| 0 | BG_00 | 40, 41, 42, 43, 44, 45, 47, 48, 49, 4A, 4B, 4C, 4D, 4F, 50, 51, 52, 53, 54, 55, 57, 58, 59, 5A, 5B, 5C, 5D, 5F, 60, 61, 62, 63, 64, 65, 67, 68, 69, 6A, 6B, 6C, 6D, 6F, 78, 79, 7A, 7B, 7C, 7D, 7F | LD r,r' |
| 1 | BG_01 | 06, 0E, 16, 1E, 26, 2E, 3E | LD r,n |
| 2 | BG_02 | 46, 4E, 56, 5E, 66, 6E, 7E | LD r,(HL) |
| 3 | BG_03 | 70, 71, 72, 73, 74, 75, 77 | LD (HL),r |
| 4 | BG_04 | 36 | LD (HL),n |
| 5 | BG_05 | 0A | LD A,(BC) |
| 6 | BG_06 | 1A | LD A,(DE) |
| 7 | BG_07 | 3A | LDD A,(HL); LD A,(nn) |
| 8 | BG_08 | 02 | LD (BC),A |
| 9 | BG_09 | 12 | LD (DE),A |
| 10 | BG_10 | 32 | LDD (HL),A; LD (nn),A; 16 BIT LOAD GROUP |
| 11 | BG_11 | 01, 11, 21, 31 | LD dd,nn |
| 12 | BG_12 | 2A | LDI A,(HL); LD HL,(nn); L |
| 13 | BG_13 | 22 | LDI (HL),A; LD (nn),HL; L |
| 14 | BG_14 | F9 | LD SP,HL |
| 15 | BG_15 | C5, D5, E5, F5 | PUSH qq |
| 16 | BG_16 | C1, D1, E1, F1 | POP qq; EXCHANGE, BLOCK TRANSFER AND SEARCH GROUP |
| 17 | BG_17 | EB | EX DE,HL |
| 18 | BG_18 | 08 | LD (nn),SP; EX AF,AF' |
| 19 | BG_19 | D9 | RETI; EXX |
| 20 | BG_20 | E3 | EX (SP),HL; 8 BIT ARITHMETIC AND LOGICAL GROUP |
| 21 | BG_21 | 80, 81, 82, 83, 84, 85, 87, 88, 89, 8A, 8B, 8C, 8D, 8F, 90, 91, 92, 93, 94, 95, 97, 98, 99, 9A, 9B, 9C, 9D, 9F, A0, A1, A2, A3, A4, A5, A7, A8, A9, AA, AB, AC, AD, AF, B0, B1, B2, B3, B4, B5, B7, B8, B9, BA, BB, BC, BD, BF | ADD A,r; ADC A,r; SUB A,r |
| 22 | BG_22 | 86, 8E, 96, 9E, A6, AE, B6, BE | ADD A,(HL); ADC A,(HL); SUB A,(HL) |
| 23 | BG_23 | C6, CE, D6, DE, E6, EE, F6, FE | ADD A,n; ADC A,n; SUB A,n |
| 24 | BG_24 | 04, 0C, 14, 1C, 24, 2C, 3C | INC r |
| 25 | BG_25 | 34 | INC (HL) |
| 26 | BG_26 | 05, 0D, 15, 1D, 25, 2D, 3D | DEC r |
| 27 | BG_27 | 35 | DEC (HL); GENERAL PURPOSE ARITHMETIC AND CPU CONTROL GROUPS |
| 28 | BG_28 | 27 | DAA |
| 29 | BG_29 | 2F | CPL |
| 30 | BG_30 | 3F | CCF |
| 31 | BG_31 | 37 | SCF |
| 32 | BG_32 | 00 | NMI; INT (IM 2); NOP |
| 33 | BG_33 | 76 | HALT |
| 34 | BG_34 | F3 | DI |
| 35 | BG_35 | FB | EI; 16 BIT ARITHMETIC GROUP |
| 36 | BG_36 | 09, 19, 29, 39 | ADD HL,ss |
| 37 | BG_37 | 03, 13, 23, 33 | INC ss |
| 38 | BG_38 | 0B, 1B, 2B, 3B | DEC ss; ROTATE AND SHIFT GROUP |
| 39 | BG_39 | 07, 17, 0F, 1F | RRA; JUMP GROUP |
| 40 | BG_40 | C3 | JP nn |
| 41 | BG_41 | C2, CA, D2, DA, E2, EA, F2, FA | LD ($FF00+C),A; LD (nn),A; LD A,($FF00+C) |
| 42 | BG_42 | 18 | JR e |
| 43 | BG_43 | 38 | JR C,e |
| 44 | BG_44 | 30 | JR NC,e |
| 45 | BG_45 | 28 | JR Z,e |
| 46 | BG_46 | 20 | JR NZ,e |
| 47 | BG_47 | E9 | JP (HL) |
| 48 | BG_48 | 10 | DJNZ,e; CALL AND RETURN GROUP |
| 49 | BG_49 | CD | CALL nn |
| 50 | BG_50 | C4, CC, D4, DC, E4, EC, F4, FC | CALL cc,nn |
| 51 | BG_51 | C9 | RET |
| 52 | BG_52 | C0, C8, D0, D8, E0, E8, F0, F8 | LD ($FF00+nn),A; ADD SP,n; Incorrect unsigned !!!!!!!!!!!!!!!!!!!!! |
| 53 | BG_53 | C7, CF, D7, DF, E7, EF, F7, FF | RST p; INPUT AND OUTPUT GROUP |
| 54 | BG_54 | DB | IN A,(n) |
| 55 | BG_55 | D3 | OUT (n),A; ----------------------------------------------------------------------------; ---------------------------------------------------------------------------- |
| 56 | BG_56 | CB |  |
| 57 | BG_57 | ED |  |
| 58 | BG_58 | DD, FD |  |

## CB

| 番号 | 定数 | 命令バイト（16進） | 元分岐のコメント |
|---|---|---|---|
| 0 | CG_00 | 00, 01, 02, 03, 04, 05, 07, 10, 11, 12, 13, 14, 15, 17, 08, 09, 0A, 0B, 0C, 0D, 0F, 18, 19, 1A, 1B, 1C, 1D, 1F, 20, 21, 22, 23, 24, 25, 27, 28, 29, 2A, 2B, 2C, 2D, 2F, 30, 31, 32, 33, 34, 35, 37, 38, 39, 3A, 3B, 3C, 3D, 3F | RLC r; RL r; RRC r |
| 1 | CG_01 | 06, 16, 0E, 1E, 2E, 3E, 26, 36 | RLC (HL); RL (HL); RRC (HL) |
| 2 | CG_02 | 40, 41, 42, 43, 44, 45, 47, 48, 49, 4A, 4B, 4C, 4D, 4F, 50, 51, 52, 53, 54, 55, 57, 58, 59, 5A, 5B, 5C, 5D, 5F, 60, 61, 62, 63, 64, 65, 67, 68, 69, 6A, 6B, 6C, 6D, 6F, 70, 71, 72, 73, 74, 75, 77, 78, 79, 7A, 7B, 7C, 7D, 7F | BIT b,r; BIT b,(IX+d), undocumented |
| 3 | CG_03 | 46, 4E, 56, 5E, 66, 6E, 76, 7E | BIT b,(HL) |
| 4 | CG_04 | C0, C1, C2, C3, C4, C5, C7, C8, C9, CA, CB, CC, CD, CF, D0, D1, D2, D3, D4, D5, D7, D8, D9, DA, DB, DC, DD, DF, E0, E1, E2, E3, E4, E5, E7, E8, E9, EA, EB, EC, ED, EF, F0, F1, F2, F3, F4, F5, F7, F8, F9, FA, FB, FC, FD, FF | SET b,r; SET b,(IX+d),Reg, undocumented |
| 5 | CG_05 | C6, CE, D6, DE, E6, EE, F6, FE | SET b,(HL) |
| 6 | CG_06 | 80, 81, 82, 83, 84, 85, 87, 88, 89, 8A, 8B, 8C, 8D, 8F, 90, 91, 92, 93, 94, 95, 97, 98, 99, 9A, 9B, 9C, 9D, 9F, A0, A1, A2, A3, A4, A5, A7, A8, A9, AA, AB, AC, AD, AF, B0, B1, B2, B3, B4, B5, B7, B8, B9, BA, BB, BC, BD, BF | RES b,r; RES b,(IX+d),Reg, undocumented |
| 7 | CG_07 | 86, 8E, 96, 9E, A6, AE, B6, BE | RES b,(HL) |

## ED

| 番号 | 定数 | 命令バイト（16進） | 元分岐のコメント |
|---|---|---|---|
| 0 | EG_00 | 84, 8C, A4, AC, 00, 01, 02, 03, 05, 06, 08, 09, 0A, 0B, 0D, 0E, 10, 11, 12, 13, 15, 16, 18, 19, 1A, 1B, 1D, 1E, 20, 21, 22, 23, 25, 26, 28, 29, 2A, 2B, 2D, 2E, 30, 32, 33, 35, 36, 38, 39, 3A, 3B, 3D, 80, 81, 82, 83, 85, 86, 87, 88, 89, 8A, 8B, 8D, 8E, 8F, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 9A, 9B, 9C, 9D, 9E, 9F, A5, A6, A7, AD, AE, AF, B4, B5, B6, B7, BC, BD, BE, BF, C0, C2, C4, C5, C6, C7, C8, CA, CB, CC, CD, CE, CF, D0, D2, D3, D4, D5, D6, D7, D8, DA, DB, DC, DD, DE, DF, E0, E1, E2, E3, E4, E5, E6, E7, E8, E9, EA, EB, EC, ED, EE, EF, F0, F1, F2, F4, F5, F6, F7, F8, F9, FA, FB, FC, FD, FE, FF | NOP, undocumented; R16: pair-indirect transfers share the core's EX(SP) work registers. |
| 1 | EG_01 | 07, 17, 27, 37, 31, 0F, 1F, 2F, 3F, 3E |  |
| 2 | EG_02 | 04, 0C, 14, 1C, 24, 2C, 34, 3C | R15.3: TST is an ED decode row, not a global override.; Disabled extensions retain the old undocumented NOPs. |
| 3 | EG_03 | 7E, 7F | NOP, undocumented; 8 BIT LOAD GROUP |
| 4 | EG_04 | 57 | LD A,I |
| 5 | EG_05 | 5F | LD A,R |
| 6 | EG_06 | 47 | LD I,A |
| 7 | EG_07 | 4F | LD R,A; 16 BIT LOAD GROUP |
| 8 | EG_08 | 4B, 5B, 6B, 7B | LD dd,(nn) |
| 9 | EG_09 | 43, 53, 63, 73 | LD (nn),dd |
| 10 | EG_10 | A0, A8, B0, B8 | LDI, LDD, LDIR, LDDR; BC; IX |
| 11 | EG_11 | A1, A9, B1, B9 | CPI, CPD, CPIR, CPDR; BC |
| 12 | EG_12 | 44, 4C, 54, 5C, 64, 6C, 74, 7C | ED64 is TST A,n only while extensions are active.; R25 TSTIO: M2 holds immediate in existing TmpAddr.L,; M3 reads {00,C}; existing byte AND updates flags only. |
| 13 | EG_13 | 46, 4E, 66, 6E | IM 0 |
| 14 | EG_14 | 56 | IM 1 (ED56) |
| 15 | EG_15 | 76 | R20.6: SLP unsupported, execute as NOP when unlocked.; Locked Z80 retains its original ED76 IM1 alias. |
| 16 | EG_16 | 5E, 77 | IM 2; 16 bit arithmetic |
| 17 | EG_17 | 4A, 5A, 6A, 7A | ADC HL,ss |
| 18 | EG_18 | 42, 52, 62, 72 | SBC HL,ss |
| 19 | EG_19 | 6F | RLD |
| 20 | EG_20 | 67 | RRD |
| 21 | EG_21 | 45, 4D, 55, 5D, 65, 6D, 75, 7D | RETI, RETN |
| 22 | EG_22 | 40, 48, 50, 58, 60, 68, 70, 78 | IN r,(C) |
| 23 | EG_23 | 41, 49, 51, 59, 61, 69, 71, 79 | OUT (C),r; OUT (C),0 |
| 24 | EG_24 | A2, AA, B2, BA | INI, IND, INIR, INDR. R23.2: ED84/8C are NOP above.; 0242a; 0242a |
| 25 | EG_25 | A3, AB, B3, BB | OUTI, OUTD, OTIR, OTDR. R23.2: EDA4/AC are NOP above.; 0242a; 0242a |
| 26 | EG_26 | C1, C9, D1, D9 | R800 MULUB |
| 27 | EG_27 | C3, F3 | R800 MULUW |

