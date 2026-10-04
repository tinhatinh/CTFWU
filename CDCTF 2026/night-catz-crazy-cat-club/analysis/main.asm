
files/cat_club_authenticator.out:     file format elf64-x86-64


Disassembly of section .text:

0000000000403035 <main>:
  403035:	55                   	push   rbp
  403036:	48 89 e5             	mov    rbp,rsp
  403039:	53                   	push   rbx
  40303a:	48 81 ec 48 01 00 00 	sub    rsp,0x148
  403041:	64 48 8b 04 25 28 00 	mov    rax,QWORD PTR fs:0x28
  403048:	00 00 
  40304a:	48 89 45 e8          	mov    QWORD PTR [rbp-0x18],rax
  40304e:	31 c0                	xor    eax,eax
  403050:	48 8d 05 b9 cf 07 00 	lea    rax,[rip+0x7cfb9]        # 480010 <__rseq_flags+0xc>
  403057:	48 89 c7             	mov    rdi,rax
  40305a:	b8 00 00 00 00       	mov    eax,0x0
  40305f:	e8 ec 3b 00 00       	call   406c50 <_IO_printf>
  403064:	48 c7 45 80 00 00 00 	mov    QWORD PTR [rbp-0x80],0x0
  40306b:	00 
  40306c:	48 c7 45 88 00 00 00 	mov    QWORD PTR [rbp-0x78],0x0
  403073:	00 
  403074:	48 c7 45 90 00 00 00 	mov    QWORD PTR [rbp-0x70],0x0
  40307b:	00 
  40307c:	48 c7 45 98 00 00 00 	mov    QWORD PTR [rbp-0x68],0x0
  403083:	00 
  403084:	48 c7 45 a0 00 00 00 	mov    QWORD PTR [rbp-0x60],0x0
  40308b:	00 
  40308c:	48 c7 45 a8 00 00 00 	mov    QWORD PTR [rbp-0x58],0x0
  403093:	00 
  403094:	48 c7 45 b0 00 00 00 	mov    QWORD PTR [rbp-0x50],0x0
  40309b:	00 
  40309c:	48 c7 45 b8 00 00 00 	mov    QWORD PTR [rbp-0x48],0x0
  4030a3:	00 
  4030a4:	48 c7 45 c0 00 00 00 	mov    QWORD PTR [rbp-0x40],0x0
  4030ab:	00 
  4030ac:	48 c7 45 c8 00 00 00 	mov    QWORD PTR [rbp-0x38],0x0
  4030b3:	00 
  4030b4:	48 c7 45 d0 00 00 00 	mov    QWORD PTR [rbp-0x30],0x0
  4030bb:	00 
  4030bc:	48 c7 45 d8 00 00 00 	mov    QWORD PTR [rbp-0x28],0x0
  4030c3:	00 
  4030c4:	c7 45 e0 00 00 00 00 	mov    DWORD PTR [rbp-0x20],0x0
  4030cb:	48 8b 15 e6 75 0b 00 	mov    rdx,QWORD PTR [rip+0xb75e6]        # 4ba6b8 <stdin>
  4030d2:	48 8d 45 80          	lea    rax,[rbp-0x80]
  4030d6:	be 63 00 00 00       	mov    esi,0x63
  4030db:	48 89 c7             	mov    rdi,rax
  4030de:	e8 5d 9d 00 00       	call   40ce40 <_IO_fgets>
  4030e3:	48 8d 45 80          	lea    rax,[rbp-0x80]
  4030e7:	0f b6 00             	movzx  eax,BYTE PTR [rax]
  4030ea:	84 c0                	test   al,al
  4030ec:	74 2e                	je     40311c <main+0xe7>
  4030ee:	48 8d 45 80          	lea    rax,[rbp-0x80]
  4030f2:	48 89 c7             	mov    rdi,rax
  4030f5:	e8 a6 df ff ff       	call   4010a0 <_init+0xa0>
  4030fa:	48 83 e8 01          	sub    rax,0x1
  4030fe:	0f b6 44 05 80       	movzx  eax,BYTE PTR [rbp+rax*1-0x80]
  403103:	3c 0a                	cmp    al,0xa
  403105:	75 15                	jne    40311c <main+0xe7>
  403107:	48 8d 45 80          	lea    rax,[rbp-0x80]
  40310b:	48 89 c7             	mov    rdi,rax
  40310e:	e8 8d df ff ff       	call   4010a0 <_init+0xa0>
  403113:	48 83 e8 01          	sub    rax,0x1
  403117:	c6 44 05 80 00       	mov    BYTE PTR [rbp+rax*1-0x80],0x0
  40311c:	c7 85 c0 fe ff ff 10 	mov    DWORD PTR [rbp-0x140],0x10
  403123:	00 00 00 
  403126:	c7 85 c4 fe ff ff 0e 	mov    DWORD PTR [rbp-0x13c],0xe
  40312d:	00 00 00 
  403130:	c7 85 c8 fe ff ff 13 	mov    DWORD PTR [rbp-0x138],0x13
  403137:	00 00 00 
  40313a:	c7 85 cc fe ff ff 0f 	mov    DWORD PTR [rbp-0x134],0xf
  403141:	00 00 00 
  403144:	c7 85 d0 fe ff ff 47 	mov    DWORD PTR [rbp-0x130],0x47
  40314b:	00 00 00 
  40314e:	c7 85 d4 fe ff ff 06 	mov    DWORD PTR [rbp-0x12c],0x6
  403155:	00 00 00 
  403158:	c7 85 d8 fe ff ff 47 	mov    DWORD PTR [rbp-0x128],0x47
  40315f:	00 00 00 
  403162:	c7 85 dc fe ff ff 00 	mov    DWORD PTR [rbp-0x124],0x0
  403169:	00 00 00 
  40316c:	c7 85 e0 fe ff ff 0b 	mov    DWORD PTR [rbp-0x120],0xb
  403173:	00 00 00 
  403176:	c7 85 e4 fe ff ff 06 	mov    DWORD PTR [rbp-0x11c],0x6
  40317d:	00 00 00 
  403180:	c7 85 e8 fe ff ff 14 	mov    DWORD PTR [rbp-0x118],0x14
  403187:	00 00 00 
  40318a:	c7 85 ec fe ff ff 14 	mov    DWORD PTR [rbp-0x114],0x14
  403191:	00 00 00 
  403194:	c7 85 f0 fe ff ff 47 	mov    DWORD PTR [rbp-0x110],0x47
  40319b:	00 00 00 
  40319e:	c7 85 f4 fe ff ff 0e 	mov    DWORD PTR [rbp-0x10c],0xe
  4031a5:	00 00 00 
  4031a8:	c7 85 f8 fe ff ff 09 	mov    DWORD PTR [rbp-0x108],0x9
  4031af:	00 00 00 
  4031b2:	c7 85 fc fe ff ff 47 	mov    DWORD PTR [rbp-0x104],0x47
  4031b9:	00 00 00 
  4031bc:	c7 85 00 ff ff ff 0a 	mov    DWORD PTR [rbp-0x100],0xa
  4031c3:	00 00 00 
  4031c6:	c7 85 04 ff ff ff 1e 	mov    DWORD PTR [rbp-0xfc],0x1e
  4031cd:	00 00 00 
  4031d0:	c7 85 08 ff ff ff 47 	mov    DWORD PTR [rbp-0xf8],0x47
  4031d7:	00 00 00 
  4031da:	c7 85 0c ff ff ff 17 	mov    DWORD PTR [rbp-0xf4],0x17
  4031e1:	00 00 00 
  4031e4:	c7 85 10 ff ff ff 06 	mov    DWORD PTR [rbp-0xf0],0x6
  4031eb:	00 00 00 
  4031ee:	c7 85 14 ff ff ff 10 	mov    DWORD PTR [rbp-0xec],0x10
  4031f5:	00 00 00 
  4031f8:	c7 85 18 ff ff ff 47 	mov    DWORD PTR [rbp-0xe8],0x47
  4031ff:	00 00 00 
  403202:	c7 85 1c ff ff ff 06 	mov    DWORD PTR [rbp-0xe4],0x6
  403209:	00 00 00 
  40320c:	c7 85 20 ff ff ff 09 	mov    DWORD PTR [rbp-0xe0],0x9
  403213:	00 00 00 
  403216:	c7 85 24 ff ff ff 03 	mov    DWORD PTR [rbp-0xdc],0x3
  40321d:	00 00 00 
  403220:	c7 85 28 ff ff ff 47 	mov    DWORD PTR [rbp-0xd8],0x47
  403227:	00 00 00 
  40322a:	c7 85 2c ff ff ff 0a 	mov    DWORD PTR [rbp-0xd4],0xa
  403231:	00 00 00 
  403234:	c7 85 30 ff ff ff 0e 	mov    DWORD PTR [rbp-0xd0],0xe
  40323b:	00 00 00 
  40323e:	c7 85 34 ff ff ff 0b 	mov    DWORD PTR [rbp-0xcc],0xb
  403245:	00 00 00 
  403248:	c7 85 38 ff ff ff 0c 	mov    DWORD PTR [rbp-0xc8],0xc
  40324f:	00 00 00 
  403252:	c7 85 3c ff ff ff 47 	mov    DWORD PTR [rbp-0xc4],0x47
  403259:	00 00 00 
  40325c:	c7 85 40 ff ff ff 08 	mov    DWORD PTR [rbp-0xc0],0x8
  403263:	00 00 00 
  403266:	c7 85 44 ff ff ff 09 	mov    DWORD PTR [rbp-0xbc],0x9
  40326d:	00 00 00 
  403270:	c7 85 48 ff ff ff 47 	mov    DWORD PTR [rbp-0xb8],0x47
  403277:	00 00 00 
  40327a:	c7 85 4c ff ff ff 0a 	mov    DWORD PTR [rbp-0xb4],0xa
  403281:	00 00 00 
  403284:	c7 85 50 ff ff ff 1e 	mov    DWORD PTR [rbp-0xb0],0x1e
  40328b:	00 00 00 
  40328e:	c7 85 54 ff ff ff 47 	mov    DWORD PTR [rbp-0xac],0x47
  403295:	00 00 00 
  403298:	c7 85 58 ff ff ff 10 	mov    DWORD PTR [rbp-0xa8],0x10
  40329f:	00 00 00 
  4032a2:	c7 85 5c ff ff ff 0f 	mov    DWORD PTR [rbp-0xa4],0xf
  4032a9:	00 00 00 
  4032ac:	c7 85 60 ff ff ff 0e 	mov    DWORD PTR [rbp-0xa0],0xe
  4032b3:	00 00 00 
  4032b6:	c7 85 64 ff ff ff 14 	mov    DWORD PTR [rbp-0x9c],0x14
  4032bd:	00 00 00 
  4032c0:	c7 85 68 ff ff ff 0c 	mov    DWORD PTR [rbp-0x98],0xc
  4032c7:	00 00 00 
  4032ca:	c7 85 6c ff ff ff 02 	mov    DWORD PTR [rbp-0x94],0x2
  4032d1:	00 00 00 
  4032d4:	c7 85 70 ff ff ff 15 	mov    DWORD PTR [rbp-0x90],0x15
  4032db:	00 00 00 
  4032de:	c7 85 74 ff ff ff 14 	mov    DWORD PTR [rbp-0x8c],0x14
  4032e5:	00 00 00 
  4032e8:	c7 85 bc fe ff ff 67 	mov    DWORD PTR [rbp-0x144],0x67
  4032ef:	00 00 00 
  4032f2:	c7 85 b4 fe ff ff 01 	mov    DWORD PTR [rbp-0x14c],0x1
  4032f9:	00 00 00 
  4032fc:	48 8d 45 80          	lea    rax,[rbp-0x80]
  403300:	48 89 c7             	mov    rdi,rax
  403303:	e8 98 dd ff ff       	call   4010a0 <_init+0xa0>
  403308:	48 83 f8 2e          	cmp    rax,0x2e
  40330c:	74 0a                	je     403318 <main+0x2e3>
  40330e:	c7 85 b4 fe ff ff 00 	mov    DWORD PTR [rbp-0x14c],0x0
  403315:	00 00 00 
  403318:	c7 85 b8 fe ff ff 00 	mov    DWORD PTR [rbp-0x148],0x0
  40331f:	00 00 00 
  403322:	eb 3c                	jmp    403360 <main+0x32b>
  403324:	8b 85 b8 fe ff ff    	mov    eax,DWORD PTR [rbp-0x148]
  40332a:	48 98                	cdqe
  40332c:	8b 94 85 c0 fe ff ff 	mov    edx,DWORD PTR [rbp+rax*4-0x140]
  403333:	8b 85 b8 fe ff ff    	mov    eax,DWORD PTR [rbp-0x148]
  403339:	48 98                	cdqe
  40333b:	0f b6 44 05 80       	movzx  eax,BYTE PTR [rbp+rax*1-0x80]
  403340:	0f be c0             	movsx  eax,al
  403343:	33 85 bc fe ff ff    	xor    eax,DWORD PTR [rbp-0x144]
  403349:	39 c2                	cmp    edx,eax
  40334b:	74 0c                	je     403359 <main+0x324>
  40334d:	c7 85 b4 fe ff ff 00 	mov    DWORD PTR [rbp-0x14c],0x0
  403354:	00 00 00 
  403357:	eb 21                	jmp    40337a <main+0x345>
  403359:	83 85 b8 fe ff ff 01 	add    DWORD PTR [rbp-0x148],0x1
  403360:	8b 85 b8 fe ff ff    	mov    eax,DWORD PTR [rbp-0x148]
  403366:	48 63 d8             	movsxd rbx,eax
  403369:	48 8d 45 80          	lea    rax,[rbp-0x80]
  40336d:	48 89 c7             	mov    rdi,rax
  403370:	e8 2b dd ff ff       	call   4010a0 <_init+0xa0>
  403375:	48 39 c3             	cmp    rbx,rax
  403378:	72 aa                	jb     403324 <main+0x2ef>
  40337a:	83 bd b4 fe ff ff 00 	cmp    DWORD PTR [rbp-0x14c],0x0
  403381:	74 25                	je     4033a8 <main+0x373>
  403383:	48 8d 05 ae cc 07 00 	lea    rax,[rip+0x7ccae]        # 480038 <__rseq_flags+0x34>
  40338a:	48 89 c7             	mov    rdi,rax
  40338d:	b8 00 00 00 00       	mov    eax,0x0
  403392:	e8 b9 38 00 00       	call   406c50 <_IO_printf>
  403397:	48 8d 05 ea cc 07 00 	lea    rax,[rip+0x7ccea]        # 480088 <__rseq_flags+0x84>
  40339e:	48 89 c7             	mov    rdi,rax
  4033a1:	e8 2a 9e 00 00       	call   40d1d0 <_IO_puts>
  4033a6:	eb 0f                	jmp    4033b7 <main+0x382>
  4033a8:	48 8d 05 51 db 07 00 	lea    rax,[rip+0x7db51]        # 480f00 <__rseq_flags+0xefc>
  4033af:	48 89 c7             	mov    rdi,rax
  4033b2:	e8 19 9e 00 00       	call   40d1d0 <_IO_puts>
  4033b7:	b8 00 00 00 00       	mov    eax,0x0
  4033bc:	48 8b 55 e8          	mov    rdx,QWORD PTR [rbp-0x18]
  4033c0:	64 48 2b 14 25 28 00 	sub    rdx,QWORD PTR fs:0x28
  4033c7:	00 00 
  4033c9:	74 05                	je     4033d0 <main+0x39b>
  4033cb:	e8 c0 17 02 00       	call   424b90 <__stack_chk_fail>
  4033d0:	48 8b 5d f8          	mov    rbx,QWORD PTR [rbp-0x8]
  4033d4:	c9                   	leave
  4033d5:	c3                   	ret
  4033d6:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
  4033dd:	00 00 00 
