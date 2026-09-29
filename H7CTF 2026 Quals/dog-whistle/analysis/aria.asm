
unpacked/aria:     file format elf64-x86-64


Disassembly of section .text:

0000000000001180 <.text>:
    1180:	55                   	push   rbp
    1181:	ba 02 00 00 00       	mov    edx,0x2
    1186:	31 f6                	xor    esi,esi
    1188:	48 89 e5             	mov    rbp,rsp
    118b:	41 54                	push   r12
    118d:	53                   	push   rbx
    118e:	bb 0c 00 00 00       	mov    ebx,0xc
    1193:	48 83 ec 20          	sub    rsp,0x20
    1197:	48 8b 3d 82 3e 00 00 	mov    rdi,QWORD PTR [rip+0x3e82]        # 5020 <stdout@GLIBC_2.2.5>
    119e:	64 48 8b 0c 25 28 00 	mov    rcx,QWORD PTR fs:0x28
    11a5:	00 00 
    11a7:	48 89 4d e8          	mov    QWORD PTR [rbp-0x18],rcx
    11ab:	31 c9                	xor    ecx,ecx
    11ad:	e8 7e ff ff ff       	call   1130 <setvbuf@plt>
    11b2:	e8 49 15 00 00       	call   2700 <fopen@plt+0x15c0>
    11b7:	48 8d 3d f2 1e 00 00 	lea    rdi,[rip+0x1ef2]        # 30b0 <fopen@plt+0x1f70>
    11be:	e8 ad fe ff ff       	call   1070 <puts@plt>
    11c3:	48 8d 3d 0e 1f 00 00 	lea    rdi,[rip+0x1f0e]        # 30d8 <fopen@plt+0x1f98>
    11ca:	e8 a1 fe ff ff       	call   1070 <puts@plt>
    11cf:	ba 02 00 00 00       	mov    edx,0x2
    11d4:	be 00 77 01 00       	mov    esi,0x17700
    11d9:	31 c0                	xor    eax,eax
    11db:	48 8d 3d 1e 1f 00 00 	lea    rdi,[rip+0x1f1e]        # 3100 <fopen@plt+0x1fc0>
    11e2:	e8 c9 fe ff ff       	call   10b0 <printf@plt>
    11e7:	be 0c 00 00 00       	mov    esi,0xc
    11ec:	48 8d 3d a5 1f 00 00 	lea    rdi,[rip+0x1fa5]        # 3198 <fopen@plt+0x2058>
    11f3:	31 c0                	xor    eax,eax
    11f5:	e8 b6 fe ff ff       	call   10b0 <printf@plt>
    11fa:	48 8d 3d ab 1f 00 00 	lea    rdi,[rip+0x1fab]        # 31ac <fopen@plt+0x206c>
    1201:	e8 6a fe ff ff       	call   1070 <puts@plt>
    1206:	48 8b 3d 13 3e 00 00 	mov    rdi,QWORD PTR [rip+0x3e13]        # 5020 <stdout@GLIBC_2.2.5>
    120d:	e8 0e ff ff ff       	call   1120 <fflush@plt>
    1212:	48 c7 45 d8 00 00 00 	mov    QWORD PTR [rbp-0x28],0x0
    1219:	00 
    121a:	48 c7 45 e0 00 00 00 	mov    QWORD PTR [rbp-0x20],0x0
    1221:	00 
    1222:	0f 1f 00             	nop    DWORD PTR [rax]
    1225:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    122c:	00 00 00 00 
    1230:	48 8b 0d f9 3d 00 00 	mov    rcx,QWORD PTR [rip+0x3df9]        # 5030 <stdin@GLIBC_2.2.5>
    1237:	48 8d 75 e0          	lea    rsi,[rbp-0x20]
    123b:	ba 0a 00 00 00       	mov    edx,0xa
    1240:	48 8d 7d d8          	lea    rdi,[rbp-0x28]
    1244:	e8 a7 fe ff ff       	call   10f0 <__getdelim@plt>
    1249:	48 89 c6             	mov    rsi,rax
    124c:	48 85 c0             	test   rax,rax
    124f:	78 58                	js     12a9 <fopen@plt+0x169>
    1251:	75 18                	jne    126b <fopen@plt+0x12b>
    1253:	eb db                	jmp    1230 <fopen@plt+0xf0>
    1255:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    125c:	00 00 00 00 
    1260:	c6 00 00             	mov    BYTE PTR [rax],0x0
    1263:	48 89 d6             	mov    rsi,rdx
    1266:	48 85 d2             	test   rdx,rdx
    1269:	74 c5                	je     1230 <fopen@plt+0xf0>
    126b:	48 8b 7d d8          	mov    rdi,QWORD PTR [rbp-0x28]
    126f:	48 8d 56 ff          	lea    rdx,[rsi-0x1]
    1273:	48 8d 04 17          	lea    rax,[rdi+rdx*1]
    1277:	0f b6 08             	movzx  ecx,BYTE PTR [rax]
    127a:	80 f9 0a             	cmp    cl,0xa
    127d:	74 e1                	je     1260 <fopen@plt+0x120>
    127f:	80 f9 0d             	cmp    cl,0xd
    1282:	74 dc                	je     1260 <fopen@plt+0x120>
    1284:	e8 57 01 00 00       	call   13e0 <fopen@plt+0x2a0>
    1289:	48 8d 3d 1c 1f 00 00 	lea    rdi,[rip+0x1f1c]        # 31ac <fopen@plt+0x206c>
    1290:	41 89 c4             	mov    r12d,eax
    1293:	e8 d8 fd ff ff       	call   1070 <puts@plt>
    1298:	48 8b 3d 81 3d 00 00 	mov    rdi,QWORD PTR [rip+0x3d81]        # 5020 <stdout@GLIBC_2.2.5>
    129f:	e8 7c fe ff ff       	call   1120 <fflush@plt>
    12a4:	44 29 e3             	sub    ebx,r12d
    12a7:	75 87                	jne    1230 <fopen@plt+0xf0>
    12a9:	48 8d 3d 01 1f 00 00 	lea    rdi,[rip+0x1f01]        # 31b1 <fopen@plt+0x2071>
    12b0:	e8 bb fd ff ff       	call   1070 <puts@plt>
    12b5:	48 8b 7d d8          	mov    rdi,QWORD PTR [rbp-0x28]
    12b9:	e8 82 fd ff ff       	call   1040 <free@plt>
    12be:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    12c2:	64 48 2b 04 25 28 00 	sub    rax,QWORD PTR fs:0x28
    12c9:	00 00 
    12cb:	75 0b                	jne    12d8 <fopen@plt+0x198>
    12cd:	48 83 c4 20          	add    rsp,0x20
    12d1:	31 c0                	xor    eax,eax
    12d3:	5b                   	pop    rbx
    12d4:	41 5c                	pop    r12
    12d6:	5d                   	pop    rbp
    12d7:	c3                   	ret
    12d8:	e8 c3 fd ff ff       	call   10a0 <__stack_chk_fail@plt>
    12dd:	0f 1f 00             	nop    DWORD PTR [rax]
    12e0:	f3 0f 1e fa          	endbr64
    12e4:	31 ed                	xor    ebp,ebp
    12e6:	49 89 d1             	mov    r9,rdx
    12e9:	5e                   	pop    rsi
    12ea:	48 89 e2             	mov    rdx,rsp
    12ed:	48 83 e4 f0          	and    rsp,0xfffffffffffffff0
    12f1:	50                   	push   rax
    12f2:	54                   	push   rsp
    12f3:	45 31 c0             	xor    r8d,r8d
    12f6:	31 c9                	xor    ecx,ecx
    12f8:	48 8d 3d 81 fe ff ff 	lea    rdi,[rip+0xfffffffffffffe81]        # 1180 <fopen@plt+0x40>
    12ff:	ff 15 d3 3c 00 00    	call   QWORD PTR [rip+0x3cd3]        # 4fd8 <fopen@plt+0x3e98>
    1305:	f4                   	hlt
    1306:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    130d:	00 00 00 
    1310:	48 8d 3d 01 3d 00 00 	lea    rdi,[rip+0x3d01]        # 5018 <fopen@plt+0x3ed8>
    1317:	48 8d 05 fa 3c 00 00 	lea    rax,[rip+0x3cfa]        # 5018 <fopen@plt+0x3ed8>
    131e:	48 39 f8             	cmp    rax,rdi
    1321:	74 15                	je     1338 <fopen@plt+0x1f8>
    1323:	48 8b 05 b6 3c 00 00 	mov    rax,QWORD PTR [rip+0x3cb6]        # 4fe0 <fopen@plt+0x3ea0>
    132a:	48 85 c0             	test   rax,rax
    132d:	74 09                	je     1338 <fopen@plt+0x1f8>
    132f:	ff e0                	jmp    rax
    1331:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    1338:	c3                   	ret
    1339:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    1340:	48 8d 3d d1 3c 00 00 	lea    rdi,[rip+0x3cd1]        # 5018 <fopen@plt+0x3ed8>
    1347:	48 8d 35 ca 3c 00 00 	lea    rsi,[rip+0x3cca]        # 5018 <fopen@plt+0x3ed8>
    134e:	48 29 fe             	sub    rsi,rdi
    1351:	48 89 f0             	mov    rax,rsi
    1354:	48 c1 ee 3f          	shr    rsi,0x3f
    1358:	48 c1 f8 03          	sar    rax,0x3
    135c:	48 01 c6             	add    rsi,rax
    135f:	48 d1 fe             	sar    rsi,1
    1362:	74 14                	je     1378 <fopen@plt+0x238>
    1364:	48 8b 05 85 3c 00 00 	mov    rax,QWORD PTR [rip+0x3c85]        # 4ff0 <fopen@plt+0x3eb0>
    136b:	48 85 c0             	test   rax,rax
    136e:	74 08                	je     1378 <fopen@plt+0x238>
    1370:	ff e0                	jmp    rax
    1372:	66 0f 1f 44 00 00    	nop    WORD PTR [rax+rax*1+0x0]
    1378:	c3                   	ret
    1379:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    1380:	f3 0f 1e fa          	endbr64
    1384:	80 3d ad 3c 00 00 00 	cmp    BYTE PTR [rip+0x3cad],0x0        # 5038 <stdin@GLIBC_2.2.5+0x8>
    138b:	75 33                	jne    13c0 <fopen@plt+0x280>
    138d:	55                   	push   rbp
    138e:	48 83 3d 62 3c 00 00 	cmp    QWORD PTR [rip+0x3c62],0x0        # 4ff8 <fopen@plt+0x3eb8>
    1395:	00 
    1396:	48 89 e5             	mov    rbp,rsp
    1399:	74 0d                	je     13a8 <fopen@plt+0x268>
    139b:	48 8b 3d 66 3c 00 00 	mov    rdi,QWORD PTR [rip+0x3c66]        # 5008 <fopen@plt+0x3ec8>
    13a2:	ff 15 50 3c 00 00    	call   QWORD PTR [rip+0x3c50]        # 4ff8 <fopen@plt+0x3eb8>
    13a8:	e8 63 ff ff ff       	call   1310 <fopen@plt+0x1d0>
    13ad:	c6 05 84 3c 00 00 01 	mov    BYTE PTR [rip+0x3c84],0x1        # 5038 <stdin@GLIBC_2.2.5+0x8>
    13b4:	5d                   	pop    rbp
    13b5:	c3                   	ret
    13b6:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    13bd:	00 00 00 
    13c0:	c3                   	ret
    13c1:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    13c5:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    13cc:	00 00 00 00 
    13d0:	f3 0f 1e fa          	endbr64
    13d4:	e9 67 ff ff ff       	jmp    1340 <fopen@plt+0x200>
    13d9:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    13e0:	55                   	push   rbp
    13e1:	48 89 e5             	mov    rbp,rsp
    13e4:	48 81 ec 90 01 00 00 	sub    rsp,0x190
    13eb:	48 89 5d f0          	mov    QWORD PTR [rbp-0x10],rbx
    13ef:	48 8d 8d 98 fe ff ff 	lea    rcx,[rbp-0x168]
    13f6:	48 8d 95 90 fe ff ff 	lea    rdx,[rbp-0x170]
    13fd:	64 48 8b 04 25 28 00 	mov    rax,QWORD PTR fs:0x28
    1404:	00 00 
    1406:	48 89 45 e8          	mov    QWORD PTR [rbp-0x18],rax
    140a:	31 c0                	xor    eax,eax
    140c:	48 c7 85 90 fe ff ff 	mov    QWORD PTR [rbp-0x170],0x0
    1413:	00 00 00 00 
    1417:	48 c7 85 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],0x0
    141e:	00 00 00 00 
    1422:	e8 d9 01 00 00       	call   1600 <fopen@plt+0x4c0>
    1427:	85 c0                	test   eax,eax
    1429:	0f 85 71 01 00 00    	jne    15a0 <fopen@plt+0x460>
    142f:	48 8b b5 98 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x168]
    1436:	48 8b bd 90 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x170]
    143d:	48 8d 8d a8 fe ff ff 	lea    rcx,[rbp-0x158]
    1444:	89 c3                	mov    ebx,eax
    1446:	48 8d 95 a0 fe ff ff 	lea    rdx,[rbp-0x160]
    144d:	48 c7 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],0x0
    1454:	00 00 00 00 
    1458:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    145f:	00 00 00 00 
    1463:	e8 a8 02 00 00       	call   1710 <fopen@plt+0x5d0>
    1468:	85 c0                	test   eax,eax
    146a:	0f 85 f8 00 00 00    	jne    1568 <fopen@plt+0x428>
    1470:	48 8b bd 90 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x170]
    1477:	e8 c4 fb ff ff       	call   1040 <free@plt>
    147c:	48 8b b5 a8 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x158]
    1483:	48 8b bd a0 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x160]
    148a:	e8 b1 04 00 00       	call   1940 <fopen@plt+0x800>
    148f:	48 8b b5 a8 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x158]
    1496:	48 8b bd a0 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x160]
    149d:	e8 ae 10 00 00       	call   2550 <fopen@plt+0x1410>
    14a2:	85 c0                	test   eax,eax
    14a4:	0f 85 1e 01 00 00    	jne    15c8 <fopen@plt+0x488>
    14aa:	48 8b b5 a8 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x158]
    14b1:	48 8b bd a0 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x160]
    14b8:	4c 89 75 f8          	mov    QWORD PTR [rbp-0x8],r14
    14bc:	e8 af 0a 00 00       	call   1f70 <fopen@plt+0xe30>
    14c1:	48 8b b5 a8 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x158]
    14c8:	48 ba ab aa aa aa aa 	movabs rdx,0xaaaaaaaaaaaaaaab
    14cf:	aa aa aa 
    14d2:	48 89 f0             	mov    rax,rsi
    14d5:	48 89 b5 78 fe ff ff 	mov    QWORD PTR [rbp-0x188],rsi
    14dc:	48 f7 e2             	mul    rdx
    14df:	48 c1 ea 02          	shr    rdx,0x2
    14e3:	48 8d 3c d5 20 00 00 	lea    rdi,[rdx*8+0x20]
    14ea:	00 
    14eb:	e8 20 fc ff ff       	call   1110 <malloc@plt>
    14f0:	48 8b b5 78 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x188]
    14f7:	48 8b bd a0 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x160]
    14fe:	48 89 c2             	mov    rdx,rax
    1501:	48 89 c3             	mov    rbx,rax
    1504:	e8 27 09 00 00       	call   1e30 <fopen@plt+0xcf0>
    1509:	48 8b bd a0 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x160]
    1510:	49 89 c6             	mov    r14,rax
    1513:	e8 28 fb ff ff       	call   1040 <free@plt>
    1518:	48 8d 8d 8c fe ff ff 	lea    rcx,[rbp-0x174]
    151f:	4c 89 f6             	mov    rsi,r14
    1522:	48 89 df             	mov    rdi,rbx
    1525:	48 8d 95 b0 fe ff ff 	lea    rdx,[rbp-0x150]
    152c:	c7 85 8c fe ff ff 00 	mov    DWORD PTR [rbp-0x174],0x0
    1533:	00 00 00 
    1536:	e8 35 0b 00 00       	call   2070 <fopen@plt+0xf30>
    153b:	85 c0                	test   eax,eax
    153d:	74 71                	je     15b0 <fopen@plt+0x470>
    153f:	48 8d 3d 37 1c 00 00 	lea    rdi,[rip+0x1c37]        # 317d <fopen@plt+0x203d>
    1546:	e8 25 fb ff ff       	call   1070 <puts@plt>
    154b:	48 89 df             	mov    rdi,rbx
    154e:	bb 01 00 00 00       	mov    ebx,0x1
    1553:	e8 e8 fa ff ff       	call   1040 <free@plt>
    1558:	e8 13 14 00 00       	call   2970 <fopen@plt+0x1830>
    155d:	4c 8b 75 f8          	mov    r14,QWORD PTR [rbp-0x8]
    1561:	eb 24                	jmp    1587 <fopen@plt+0x447>
    1563:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    1568:	48 8d 3d c1 1a 00 00 	lea    rdi,[rip+0x1ac1]        # 3030 <fopen@plt+0x1ef0>
    156f:	be 00 77 01 00       	mov    esi,0x17700
    1574:	31 c0                	xor    eax,eax
    1576:	e8 35 fb ff ff       	call   10b0 <printf@plt>
    157b:	48 8b bd 90 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x170]
    1582:	e8 b9 fa ff ff       	call   1040 <free@plt>
    1587:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    158b:	64 48 2b 04 25 28 00 	sub    rax,QWORD PTR fs:0x28
    1592:	00 00 
    1594:	75 5d                	jne    15f3 <fopen@plt+0x4b3>
    1596:	89 d8                	mov    eax,ebx
    1598:	48 8b 5d f0          	mov    rbx,QWORD PTR [rbp-0x10]
    159c:	c9                   	leave
    159d:	c3                   	ret
    159e:	66 90                	xchg   ax,ax
    15a0:	48 8d 3d 61 1a 00 00 	lea    rdi,[rip+0x1a61]        # 3008 <fopen@plt+0x1ec8>
    15a7:	31 db                	xor    ebx,ebx
    15a9:	e8 c2 fa ff ff       	call   1070 <puts@plt>
    15ae:	eb d7                	jmp    1587 <fopen@plt+0x447>
    15b0:	8b b5 8c fe ff ff    	mov    esi,DWORD PTR [rbp-0x174]
    15b6:	48 8d bd b0 fe ff ff 	lea    rdi,[rbp-0x150]
    15bd:	e8 ce 11 00 00       	call   2790 <fopen@plt+0x1650>
    15c2:	eb 87                	jmp    154b <fopen@plt+0x40b>
    15c4:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    15c8:	48 8d 3d 99 1a 00 00 	lea    rdi,[rip+0x1a99]        # 3068 <fopen@plt+0x1f28>
    15cf:	bb 01 00 00 00       	mov    ebx,0x1
    15d4:	e8 97 fa ff ff       	call   1070 <puts@plt>
    15d9:	48 8d 3d 89 1b 00 00 	lea    rdi,[rip+0x1b89]        # 3169 <fopen@plt+0x2029>
    15e0:	e8 8b fa ff ff       	call   1070 <puts@plt>
    15e5:	48 8b bd a0 fe ff ff 	mov    rdi,QWORD PTR [rbp-0x160]
    15ec:	e8 4f fa ff ff       	call   1040 <free@plt>
    15f1:	eb 94                	jmp    1587 <fopen@plt+0x447>
    15f3:	4c 89 75 f8          	mov    QWORD PTR [rbp-0x8],r14
    15f7:	e8 a4 fa ff ff       	call   10a0 <__stack_chk_fail@plt>
    15fc:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    1600:	55                   	push   rbp
    1601:	48 89 f0             	mov    rax,rsi
    1604:	48 c1 e8 02          	shr    rax,0x2
    1608:	48 89 e5             	mov    rbp,rsp
    160b:	41 56                	push   r14
    160d:	49 89 f6             	mov    r14,rsi
    1610:	41 55                	push   r13
    1612:	49 89 d5             	mov    r13,rdx
    1615:	41 54                	push   r12
    1617:	49 89 cc             	mov    r12,rcx
    161a:	53                   	push   rbx
    161b:	48 89 fb             	mov    rbx,rdi
    161e:	48 8d 7c 40 04       	lea    rdi,[rax+rax*2+0x4]
    1623:	e8 e8 fa ff ff       	call   1110 <malloc@plt>
    1628:	48 85 c0             	test   rax,rax
    162b:	0f 84 d5 00 00 00    	je     1706 <fopen@plt+0x5c6>
    1631:	48 89 c7             	mov    rdi,rax
    1634:	4d 85 f6             	test   r14,r14
    1637:	74 37                	je     1670 <fopen@plt+0x530>
    1639:	4e 8d 04 33          	lea    r8,[rbx+r14*1]
    163d:	48 89 da             	mov    rdx,rbx
    1640:	31 c9                	xor    ecx,ecx
    1642:	31 f6                	xor    esi,esi
    1644:	45 31 f6             	xor    r14d,r14d
    1647:	41 ba 13 00 80 00    	mov    r10d,0x800013
    164d:	0f b6 02             	movzx  eax,BYTE PTR [rdx]
    1650:	3c 20                	cmp    al,0x20
    1652:	7f 34                	jg     1688 <fopen@plt+0x548>
    1654:	3c 08                	cmp    al,0x8
    1656:	7e 0a                	jle    1662 <fopen@plt+0x522>
    1658:	44 8d 48 f7          	lea    r9d,[rax-0x9]
    165c:	4d 0f a3 ca          	bt     r10,r9
    1660:	73 64                	jae    16c6 <fopen@plt+0x586>
    1662:	48 83 c2 01          	add    rdx,0x1
    1666:	4c 39 c2             	cmp    rdx,r8
    1669:	75 e2                	jne    164d <fopen@plt+0x50d>
    166b:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    1670:	49 89 7d 00          	mov    QWORD PTR [r13+0x0],rdi
    1674:	31 c0                	xor    eax,eax
    1676:	4d 89 34 24          	mov    QWORD PTR [r12],r14
    167a:	5b                   	pop    rbx
    167b:	41 5c                	pop    r12
    167d:	41 5d                	pop    r13
    167f:	41 5e                	pop    r14
    1681:	5d                   	pop    rbp
    1682:	c3                   	ret
    1683:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    1688:	3c 3d                	cmp    al,0x3d
    168a:	74 e4                	je     1670 <fopen@plt+0x530>
    168c:	44 0f be c8          	movsx  r9d,al
    1690:	3c 39                	cmp    al,0x39
    1692:	7e 2e                	jle    16c2 <fopen@plt+0x582>
    1694:	3c 5a                	cmp    al,0x5a
    1696:	7e 58                	jle    16f0 <fopen@plt+0x5b0>
    1698:	83 e8 61             	sub    eax,0x61
    169b:	3c 19                	cmp    al,0x19
    169d:	77 c3                	ja     1662 <fopen@plt+0x522>
    169f:	41 83 e9 47          	sub    r9d,0x47
    16a3:	c1 e6 06             	shl    esi,0x6
    16a6:	8d 41 06             	lea    eax,[rcx+0x6]
    16a9:	44 09 ce             	or     esi,r9d
    16ac:	83 f8 07             	cmp    eax,0x7
    16af:	7e 37                	jle    16e8 <fopen@plt+0x5a8>
    16b1:	83 e9 02             	sub    ecx,0x2
    16b4:	89 f0                	mov    eax,esi
    16b6:	d3 f8                	sar    eax,cl
    16b8:	42 88 04 37          	mov    BYTE PTR [rdi+r14*1],al
    16bc:	49 83 c6 01          	add    r14,0x1
    16c0:	eb a0                	jmp    1662 <fopen@plt+0x522>
    16c2:	3c 2f                	cmp    al,0x2f
    16c4:	7f 3a                	jg     1700 <fopen@plt+0x5c0>
    16c6:	41 b9 3e 00 00 00    	mov    r9d,0x3e
    16cc:	3c 2b                	cmp    al,0x2b
    16ce:	74 d3                	je     16a3 <fopen@plt+0x563>
    16d0:	3c 2f                	cmp    al,0x2f
    16d2:	75 8e                	jne    1662 <fopen@plt+0x522>
    16d4:	41 b9 3f 00 00 00    	mov    r9d,0x3f
    16da:	c1 e6 06             	shl    esi,0x6
    16dd:	8d 41 06             	lea    eax,[rcx+0x6]
    16e0:	44 09 ce             	or     esi,r9d
    16e3:	83 f8 07             	cmp    eax,0x7
    16e6:	7f c9                	jg     16b1 <fopen@plt+0x571>
    16e8:	89 c1                	mov    ecx,eax
    16ea:	e9 73 ff ff ff       	jmp    1662 <fopen@plt+0x522>
    16ef:	90                   	nop
    16f0:	41 83 e9 41          	sub    r9d,0x41
    16f4:	3c 40                	cmp    al,0x40
    16f6:	7f ab                	jg     16a3 <fopen@plt+0x563>
    16f8:	e9 65 ff ff ff       	jmp    1662 <fopen@plt+0x522>
    16fd:	0f 1f 00             	nop    DWORD PTR [rax]
    1700:	41 83 c1 04          	add    r9d,0x4
    1704:	eb 9d                	jmp    16a3 <fopen@plt+0x563>
    1706:	b8 ff ff ff ff       	mov    eax,0xffffffff
    170b:	e9 6a ff ff ff       	jmp    167a <fopen@plt+0x53a>
    1710:	48 83 fe 0b          	cmp    rsi,0xb
    1714:	0f 86 fe 01 00 00    	jbe    1918 <fopen@plt+0x7d8>
    171a:	49 89 f8             	mov    r8,rdi
    171d:	81 3f 52 49 46 46    	cmp    DWORD PTR [rdi],0x46464952
    1723:	0f 85 ef 01 00 00    	jne    1918 <fopen@plt+0x7d8>
    1729:	81 7f 08 57 41 56 45 	cmp    DWORD PTR [rdi+0x8],0x45564157
    1730:	0f 85 e2 01 00 00    	jne    1918 <fopen@plt+0x7d8>
    1736:	48 89 f7             	mov    rdi,rsi
    1739:	48 83 fe 13          	cmp    rsi,0x13
    173d:	0f 86 d5 01 00 00    	jbe    1918 <fopen@plt+0x7d8>
    1743:	55                   	push   rbp
    1744:	49 89 ca             	mov    r10,rcx
    1747:	49 89 d3             	mov    r11,rdx
    174a:	45 31 c9             	xor    r9d,r9d
    174d:	be 0c 00 00 00       	mov    esi,0xc
    1752:	b9 14 00 00 00       	mov    ecx,0x14
    1757:	48 89 e5             	mov    rbp,rsp
    175a:	41 57                	push   r15
    175c:	41 56                	push   r14
    175e:	45 31 f6             	xor    r14d,r14d
    1761:	41 55                	push   r13
    1763:	45 31 ed             	xor    r13d,r13d
    1766:	41 54                	push   r12
    1768:	45 31 e4             	xor    r12d,r12d
    176b:	53                   	push   rbx
    176c:	31 db                	xor    ebx,ebx
    176e:	48 83 ec 08          	sub    rsp,0x8
    1772:	eb 26                	jmp    179a <fopen@plt+0x65a>
    1774:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    1778:	4c 01 c1             	add    rcx,r8
    177b:	41 81 ff 64 61 74 61 	cmp    r15d,0x61746164
    1782:	48 0f 44 d9          	cmove  rbx,rcx
    1786:	44 0f 44 c8          	cmove  r9d,eax
    178a:	83 e0 01             	and    eax,0x1
    178d:	48 8d 34 10          	lea    rsi,[rax+rdx*1]
    1791:	48 8d 4e 08          	lea    rcx,[rsi+0x8]
    1795:	48 39 cf             	cmp    rdi,rcx
    1798:	72 66                	jb     1800 <fopen@plt+0x6c0>
    179a:	41 8b 54 30 04       	mov    edx,DWORD PTR [r8+rsi*1+0x4]
    179f:	41 89 ff             	mov    r15d,edi
    17a2:	41 29 cf             	sub    r15d,ecx
    17a5:	48 89 d0             	mov    rax,rdx
    17a8:	48 01 ca             	add    rdx,rcx
    17ab:	48 39 d7             	cmp    rdi,rdx
    17ae:	41 0f 42 c7          	cmovb  eax,r15d
    17b2:	41 89 c7             	mov    r15d,eax
    17b5:	49 01 cf             	add    r15,rcx
    17b8:	48 39 d7             	cmp    rdi,rdx
    17bb:	49 0f 42 d7          	cmovb  rdx,r15
    17bf:	45 8b 3c 30          	mov    r15d,DWORD PTR [r8+rsi*1]
    17c3:	41 81 ff 66 6d 74 20 	cmp    r15d,0x20746d66
    17ca:	75 ac                	jne    1778 <fopen@plt+0x638>
    17cc:	83 f8 0f             	cmp    eax,0xf
    17cf:	76 b9                	jbe    178a <fopen@plt+0x64a>
    17d1:	83 e0 01             	and    eax,0x1
    17d4:	45 0f b7 74 30 0a    	movzx  r14d,WORD PTR [r8+rsi*1+0xa]
    17da:	45 8b 64 30 0c       	mov    r12d,DWORD PTR [r8+rsi*1+0xc]
    17df:	45 0f b7 6c 30 16    	movzx  r13d,WORD PTR [r8+rsi*1+0x16]
    17e5:	48 8d 34 10          	lea    rsi,[rax+rdx*1]
    17e9:	48 8d 4e 08          	lea    rcx,[rsi+0x8]
    17ed:	48 39 cf             	cmp    rdi,rcx
    17f0:	73 a8                	jae    179a <fopen@plt+0x65a>
    17f2:	0f 1f 00             	nop    DWORD PTR [rax]
    17f5:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    17fc:	00 00 00 00 
    1800:	48 85 db             	test   rbx,rbx
    1803:	0f 84 f7 00 00 00    	je     1900 <fopen@plt+0x7c0>
    1809:	66 41 83 fe 01       	cmp    r14w,0x1
    180e:	0f 85 ec 00 00 00    	jne    1900 <fopen@plt+0x7c0>
    1814:	66 41 83 fd 18       	cmp    r13w,0x18
    1819:	0f 85 e1 00 00 00    	jne    1900 <fopen@plt+0x7c0>
    181f:	41 81 fc 00 77 01 00 	cmp    r12d,0x17700
    1826:	0f 85 d4 00 00 00    	jne    1900 <fopen@plt+0x7c0>
    182c:	41 83 f9 02          	cmp    r9d,0x2
    1830:	0f 86 ca 00 00 00    	jbe    1900 <fopen@plt+0x7c0>
    1836:	41 81 f9 02 ca 08 00 	cmp    r9d,0x8ca02
    183d:	0f 87 ad 00 00 00    	ja     18f0 <fopen@plt+0x7b0>
    1843:	45 89 cc             	mov    r12d,r9d
    1846:	b8 ab aa aa aa       	mov    eax,0xaaaaaaab
    184b:	4c 0f af e0          	imul   r12,rax
    184f:	49 c1 ec 21          	shr    r12,0x21
    1853:	4a 8d 3c e5 00 00 00 	lea    rdi,[r12*8+0x0]
    185a:	00 
    185b:	4d 89 d5             	mov    r13,r10
    185e:	4d 89 de             	mov    r14,r11
    1861:	e8 aa f8 ff ff       	call   1110 <malloc@plt>
    1866:	48 89 c7             	mov    rdi,rax
    1869:	48 85 c0             	test   rax,rax
    186c:	0f 84 8e 00 00 00    	je     1900 <fopen@plt+0x7c0>
    1872:	4f 8d 04 64          	lea    r8,[r12+r12*2]
    1876:	f2 0f 10 0d 3a 1a 00 	movsd  xmm1,QWORD PTR [rip+0x1a3a]        # 32b8 <fopen@plt+0x2178>
    187d:	00 
    187e:	48 89 d9             	mov    rcx,rbx
    1881:	48 89 c6             	mov    rsi,rax
    1884:	49 01 d8             	add    r8,rbx
    1887:	66 0f 1f 84 00 00 00 	nop    WORD PTR [rax+rax*1+0x0]
    188e:	00 00 
    1890:	0f b6 51 02          	movzx  edx,BYTE PTR [rcx+0x2]
    1894:	0f b6 41 01          	movzx  eax,BYTE PTR [rcx+0x1]
    1898:	66 0f ef c0          	pxor   xmm0,xmm0
    189c:	c1 e0 08             	shl    eax,0x8
    189f:	c1 e2 10             	shl    edx,0x10
    18a2:	09 c2                	or     edx,eax
    18a4:	0f b6 01             	movzx  eax,BYTE PTR [rcx]
    18a7:	09 d0                	or     eax,edx
    18a9:	41 89 c1             	mov    r9d,eax
    18ac:	41 81 c9 00 00 00 ff 	or     r9d,0xff000000
    18b3:	81 e2 00 00 80 00    	and    edx,0x800000
    18b9:	41 0f 45 c1          	cmovne eax,r9d
    18bd:	48 83 c1 03          	add    rcx,0x3
    18c1:	48 83 c6 08          	add    rsi,0x8
    18c5:	f2 0f 2a c0          	cvtsi2sd xmm0,eax
    18c9:	f2 0f 59 c1          	mulsd  xmm0,xmm1
    18cd:	f2 0f 11 46 f8       	movsd  QWORD PTR [rsi-0x8],xmm0
    18d2:	49 39 c8             	cmp    r8,rcx
    18d5:	75 b9                	jne    1890 <fopen@plt+0x750>
    18d7:	49 89 3e             	mov    QWORD PTR [r14],rdi
    18da:	31 c0                	xor    eax,eax
    18dc:	4d 89 65 00          	mov    QWORD PTR [r13+0x0],r12
    18e0:	48 83 c4 08          	add    rsp,0x8
    18e4:	5b                   	pop    rbx
    18e5:	41 5c                	pop    r12
    18e7:	41 5d                	pop    r13
    18e9:	41 5e                	pop    r14
    18eb:	41 5f                	pop    r15
    18ed:	5d                   	pop    rbp
    18ee:	c3                   	ret
    18ef:	90                   	nop
    18f0:	bf 00 70 17 00       	mov    edi,0x177000
    18f5:	41 bc 00 ee 02 00    	mov    r12d,0x2ee00
    18fb:	e9 5b ff ff ff       	jmp    185b <fopen@plt+0x71b>
    1900:	48 83 c4 08          	add    rsp,0x8
    1904:	b8 ff ff ff ff       	mov    eax,0xffffffff
    1909:	5b                   	pop    rbx
    190a:	41 5c                	pop    r12
    190c:	41 5d                	pop    r13
    190e:	41 5e                	pop    r14
    1910:	41 5f                	pop    r15
    1912:	5d                   	pop    rbp
    1913:	c3                   	ret
    1914:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    1918:	b8 ff ff ff ff       	mov    eax,0xffffffff
    191d:	c3                   	ret
    191e:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    1925:	00 00 00 
    1928:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    192f:	00 00 00 
    1932:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    1939:	00 00 00 
    193c:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    1940:	55                   	push   rbp
    1941:	48 89 e5             	mov    rbp,rsp
    1944:	41 57                	push   r15
    1946:	41 56                	push   r14
    1948:	41 55                	push   r13
    194a:	49 89 fd             	mov    r13,rdi
    194d:	41 54                	push   r12
    194f:	53                   	push   rbx
    1950:	48 81 ec 78 01 00 00 	sub    rsp,0x178
    1957:	8b 15 b3 36 00 00    	mov    edx,DWORD PTR [rip+0x36b3]        # 5010 <fopen@plt+0x3ed0>
    195d:	64 4c 8b 24 25 28 00 	mov    r12,QWORD PTR fs:0x28
    1964:	00 00 
    1966:	4c 89 65 c8          	mov    QWORD PTR [rbp-0x38],r12
    196a:	49 89 f4             	mov    r12,rsi
    196d:	85 d2                	test   edx,edx
    196f:	0f 88 1a 03 00 00    	js     1c8f <fopen@plt+0xb4f>
    1975:	8b 05 c5 36 00 00    	mov    eax,DWORD PTR [rip+0x36c5]        # 5040 <stdin@GLIBC_2.2.5+0x10>
    197b:	85 c0                	test   eax,eax
    197d:	0f 8e 86 01 00 00    	jle    1b09 <fopen@plt+0x9c9>
    1983:	4c 8d 35 d6 36 00 00 	lea    r14,[rip+0x36d6]        # 5060 <stdin@GLIBC_2.2.5+0x30>
    198a:	48 c1 e0 05          	shl    rax,0x5
    198e:	4f 8d 7c e5 00       	lea    r15,[r13+r12*8+0x0]
    1993:	4a 8d 1c 30          	lea    rbx,[rax+r14*1]
    1997:	66 0f 1f 84 00 00 00 	nop    WORD PTR [rax+rax*1+0x0]
    199e:	00 00 
    19a0:	f2 41 0f 10 4e 18    	movsd  xmm1,QWORD PTR [r14+0x18]
    19a6:	66 0f ef c0          	pxor   xmm0,xmm0
    19aa:	66 0f 2e c8          	ucomisd xmm1,xmm0
    19ae:	7a 0d                	jp     19bd <fopen@plt+0x87d>
    19b0:	75 0b                	jne    19bd <fopen@plt+0x87d>
    19b2:	41 8b 06             	mov    eax,DWORD PTR [r14]
    19b5:	85 c0                	test   eax,eax
    19b7:	0f 84 3f 01 00 00    	je     1afc <fopen@plt+0x9bc>
    19bd:	f2 0f 10 05 0b 19 00 	movsd  xmm0,QWORD PTR [rip+0x190b]        # 32d0 <fopen@plt+0x2190>
    19c4:	00 
    19c5:	f2 0f 5e 0d fb 18 00 	divsd  xmm1,QWORD PTR [rip+0x18fb]        # 32c8 <fopen@plt+0x2188>
    19cc:	00 
    19cd:	e8 ae f6 ff ff       	call   1080 <pow@plt>
    19d2:	48 8d bd 78 fe ff ff 	lea    rdi,[rbp-0x188]
    19d9:	48 8d b5 70 fe ff ff 	lea    rsi,[rbp-0x190]
    19e0:	f2 0f 11 85 68 fe ff 	movsd  QWORD PTR [rbp-0x198],xmm0
    19e7:	ff 
    19e8:	f2 0f 10 05 e8 18 00 	movsd  xmm0,QWORD PTR [rip+0x18e8]        # 32d8 <fopen@plt+0x2198>
    19ef:	00 
    19f0:	f2 41 0f 59 46 08    	mulsd  xmm0,QWORD PTR [r14+0x8]
    19f6:	f2 0f 5e 05 e2 18 00 	divsd  xmm0,QWORD PTR [rip+0x18e2]        # 32e0 <fopen@plt+0x21a0>
    19fd:	00 
    19fe:	e8 bd f6 ff ff       	call   10c0 <sincos@plt>
    1a03:	41 8b 06             	mov    eax,DWORD PTR [r14]
    1a06:	f2 41 0f 10 46 10    	movsd  xmm0,QWORD PTR [r14+0x10]
    1a0c:	f2 0f 10 b5 70 fe ff 	movsd  xmm6,QWORD PTR [rbp-0x190]
    1a13:	ff 
    1a14:	f2 0f 10 8d 68 fe ff 	movsd  xmm1,QWORD PTR [rbp-0x198]
    1a1b:	ff 
    1a1c:	66 0f 28 d0          	movapd xmm2,xmm0
    1a20:	83 f8 01             	cmp    eax,0x1
    1a23:	f2 0f 58 d0          	addsd  xmm2,xmm0
    1a27:	f2 0f 10 85 78 fe ff 	movsd  xmm0,QWORD PTR [rbp-0x188]
    1a2e:	ff 
    1a2f:	f2 0f 5e c2          	divsd  xmm0,xmm2
    1a33:	0f 84 f7 00 00 00    	je     1b30 <fopen@plt+0x9f0>
    1a39:	66 0f 28 d1          	movapd xmm2,xmm1
    1a3d:	83 f8 02             	cmp    eax,0x2
    1a40:	0f 84 2a 01 00 00    	je     1b70 <fopen@plt+0xa30>
    1a46:	83 f8 03             	cmp    eax,0x3
    1a49:	0f 84 b1 01 00 00    	je     1c00 <fopen@plt+0xac0>
    1a4f:	f2 0f 59 d0          	mulsd  xmm2,xmm0
    1a53:	f2 0f 10 2d 65 18 00 	movsd  xmm5,QWORD PTR [rip+0x1865]        # 32c0 <fopen@plt+0x2180>
    1a5a:	00 
    1a5b:	f2 0f 59 35 85 18 00 	mulsd  xmm6,QWORD PTR [rip+0x1885]        # 32e8 <fopen@plt+0x21a8>
    1a62:	00 
    1a63:	66 0f 28 fd          	movapd xmm7,xmm5
    1a67:	66 44 0f 28 ca       	movapd xmm9,xmm2
    1a6c:	f2 0f 5c fa          	subsd  xmm7,xmm2
    1a70:	f2 44 0f 58 cd       	addsd  xmm9,xmm5
    1a75:	66 44 0f 28 c6       	movapd xmm8,xmm6
    1a7a:	f2 0f 5e c1          	divsd  xmm0,xmm1
    1a7e:	66 0f 28 c8          	movapd xmm1,xmm0
    1a82:	f2 0f 58 cd          	addsd  xmm1,xmm5
    1a86:	f2 0f 5c e8          	subsd  xmm5,xmm0
    1a8a:	4d 85 e4             	test   r12,r12
    1a8d:	74 6d                	je     1afc <fopen@plt+0x9bc>
    1a8f:	f2 44 0f 5e c9       	divsd  xmm9,xmm1
    1a94:	66 0f ef db          	pxor   xmm3,xmm3
    1a98:	4c 89 e8             	mov    rax,r13
    1a9b:	66 0f 28 c3          	movapd xmm0,xmm3
    1a9f:	f2 44 0f 5e c1       	divsd  xmm8,xmm1
    1aa4:	f2 0f 5e f9          	divsd  xmm7,xmm1
    1aa8:	f2 0f 5e f1          	divsd  xmm6,xmm1
    1aac:	f2 0f 5e e9          	divsd  xmm5,xmm1
    1ab0:	f2 0f 10 10          	movsd  xmm2,QWORD PTR [rax]
    1ab4:	48 83 c0 08          	add    rax,0x8
    1ab8:	66 0f 28 ca          	movapd xmm1,xmm2
    1abc:	f2 41 0f 59 c9       	mulsd  xmm1,xmm9
    1ac1:	f2 0f 58 c8          	addsd  xmm1,xmm0
    1ac5:	66 0f 28 c2          	movapd xmm0,xmm2
    1ac9:	f2 41 0f 59 c0       	mulsd  xmm0,xmm8
    1ace:	f2 0f 59 d7          	mulsd  xmm2,xmm7
    1ad2:	66 0f 28 e1          	movapd xmm4,xmm1
    1ad6:	f2 0f 11 48 f8       	movsd  QWORD PTR [rax-0x8],xmm1
    1adb:	f2 0f 59 e6          	mulsd  xmm4,xmm6
    1adf:	f2 0f 5c c4          	subsd  xmm0,xmm4
    1ae3:	66 0f 28 e1          	movapd xmm4,xmm1
    1ae7:	f2 0f 59 e5          	mulsd  xmm4,xmm5
    1aeb:	f2 0f 58 c3          	addsd  xmm0,xmm3
    1aef:	66 0f 28 da          	movapd xmm3,xmm2
    1af3:	f2 0f 5c dc          	subsd  xmm3,xmm4
    1af7:	4c 39 f8             	cmp    rax,r15
    1afa:	75 b4                	jne    1ab0 <fopen@plt+0x970>
    1afc:	49 83 c6 20          	add    r14,0x20
    1b00:	4c 39 f3             	cmp    rbx,r14
    1b03:	0f 85 97 fe ff ff    	jne    19a0 <fopen@plt+0x860>
    1b09:	48 8b 45 c8          	mov    rax,QWORD PTR [rbp-0x38]
    1b0d:	64 48 2b 04 25 28 00 	sub    rax,QWORD PTR fs:0x28
    1b14:	00 00 
    1b16:	0f 85 09 03 00 00    	jne    1e25 <fopen@plt+0xce5>
    1b1c:	48 81 c4 78 01 00 00 	add    rsp,0x178
    1b23:	5b                   	pop    rbx
    1b24:	41 5c                	pop    r12
    1b26:	41 5d                	pop    r13
    1b28:	41 5e                	pop    r14
    1b2a:	41 5f                	pop    r15
    1b2c:	5d                   	pop    rbp
    1b2d:	c3                   	ret
    1b2e:	66 90                	xchg   ax,ax
    1b30:	f2 0f 59 35 b0 17 00 	mulsd  xmm6,QWORD PTR [rip+0x17b0]        # 32e8 <fopen@plt+0x21a8>
    1b37:	00 
    1b38:	f2 0f 10 0d 80 17 00 	movsd  xmm1,QWORD PTR [rip+0x1780]        # 32c0 <fopen@plt+0x2180>
    1b3f:	00 
    1b40:	f2 0f 10 2d 78 17 00 	movsd  xmm5,QWORD PTR [rip+0x1778]        # 32c0 <fopen@plt+0x2180>
    1b47:	00 
    1b48:	f2 0f 10 3d 70 17 00 	movsd  xmm7,QWORD PTR [rip+0x1770]        # 32c0 <fopen@plt+0x2180>
    1b4f:	00 
    1b50:	f2 0f 58 c8          	addsd  xmm1,xmm0
    1b54:	f2 0f 5c e8          	subsd  xmm5,xmm0
    1b58:	66 44 0f 28 cf       	movapd xmm9,xmm7
    1b5d:	66 44 0f 28 c6       	movapd xmm8,xmm6
    1b62:	e9 23 ff ff ff       	jmp    1a8a <fopen@plt+0x94a>
    1b67:	66 0f 1f 84 00 00 00 	nop    WORD PTR [rax+rax*1+0x0]
    1b6e:	00 00 
    1b70:	f2 0f 51 d2          	sqrtsd xmm2,xmm2
    1b74:	66 0f 28 e9          	movapd xmm5,xmm1
    1b78:	66 44 0f 28 c1       	movapd xmm8,xmm1
    1b7d:	f2 0f 10 1d 3b 17 00 	movsd  xmm3,QWORD PTR [rip+0x173b]        # 32c0 <fopen@plt+0x2180>
    1b84:	00 
    1b85:	f2 44 0f 58 c1       	addsd  xmm8,xmm1
    1b8a:	f2 0f 58 eb          	addsd  xmm5,xmm3
    1b8e:	f2 0f 58 d2          	addsd  xmm2,xmm2
    1b92:	66 0f 28 fd          	movapd xmm7,xmm5
    1b96:	f2 0f 59 c2          	mulsd  xmm0,xmm2
    1b9a:	66 0f 28 d1          	movapd xmm2,xmm1
    1b9e:	f2 0f 5c d3          	subsd  xmm2,xmm3
    1ba2:	66 0f 28 de          	movapd xmm3,xmm6
    1ba6:	f2 0f 59 f5          	mulsd  xmm6,xmm5
    1baa:	f2 0f 59 da          	mulsd  xmm3,xmm2
    1bae:	66 0f 28 e2          	movapd xmm4,xmm2
    1bb2:	66 44 0f 28 c8       	movapd xmm9,xmm0
    1bb7:	f2 0f 5c e6          	subsd  xmm4,xmm6
    1bbb:	f2 0f 58 f2          	addsd  xmm6,xmm2
    1bbf:	f2 0f 59 35 21 17 00 	mulsd  xmm6,QWORD PTR [rip+0x1721]        # 32e8 <fopen@plt+0x21a8>
    1bc6:	00 
    1bc7:	f2 0f 5c fb          	subsd  xmm7,xmm3
    1bcb:	f2 0f 58 eb          	addsd  xmm5,xmm3
    1bcf:	f2 44 0f 59 c4       	mulsd  xmm8,xmm4
    1bd4:	f2 44 0f 58 cf       	addsd  xmm9,xmm7
    1bd9:	f2 0f 5c f8          	subsd  xmm7,xmm0
    1bdd:	f2 44 0f 59 c9       	mulsd  xmm9,xmm1
    1be2:	f2 0f 59 f9          	mulsd  xmm7,xmm1
    1be6:	66 0f 28 c8          	movapd xmm1,xmm0
    1bea:	f2 0f 58 cd          	addsd  xmm1,xmm5
    1bee:	f2 0f 5c e8          	subsd  xmm5,xmm0
    1bf2:	e9 93 fe ff ff       	jmp    1a8a <fopen@plt+0x94a>
    1bf7:	66 0f 1f 84 00 00 00 	nop    WORD PTR [rax+rax*1+0x0]
    1bfe:	00 00 
    1c00:	f2 0f 51 d2          	sqrtsd xmm2,xmm2
    1c04:	f2 0f 10 1d b4 16 00 	movsd  xmm3,QWORD PTR [rip+0x16b4]        # 32c0 <fopen@plt+0x2180>
    1c0b:	00 
    1c0c:	66 0f 28 e9          	movapd xmm5,xmm1
    1c10:	66 0f 28 e6          	movapd xmm4,xmm6
    1c14:	f2 44 0f 10 05 cb 16 	movsd  xmm8,QWORD PTR [rip+0x16cb]        # 32e8 <fopen@plt+0x21a8>
    1c1b:	00 00 
    1c1d:	f2 0f 58 eb          	addsd  xmm5,xmm3
    1c21:	f2 0f 58 d2          	addsd  xmm2,xmm2
    1c25:	f2 44 0f 59 c1       	mulsd  xmm8,xmm1
    1c2a:	f2 0f 59 f5          	mulsd  xmm6,xmm5
    1c2e:	66 0f 28 fd          	movapd xmm7,xmm5
    1c32:	f2 0f 59 c2          	mulsd  xmm0,xmm2
    1c36:	66 0f 28 d1          	movapd xmm2,xmm1
    1c3a:	f2 0f 5c d3          	subsd  xmm2,xmm3
    1c3e:	f2 0f 59 e2          	mulsd  xmm4,xmm2
    1c42:	66 0f 28 de          	movapd xmm3,xmm6
    1c46:	66 0f 28 f2          	movapd xmm6,xmm2
    1c4a:	f2 0f 58 f3          	addsd  xmm6,xmm3
    1c4e:	66 44 0f 28 c8       	movapd xmm9,xmm0
    1c53:	f2 44 0f 59 c6       	mulsd  xmm8,xmm6
    1c58:	66 0f 28 f2          	movapd xmm6,xmm2
    1c5c:	f2 0f 58 fc          	addsd  xmm7,xmm4
    1c60:	f2 0f 5c ec          	subsd  xmm5,xmm4
    1c64:	f2 0f 5c f3          	subsd  xmm6,xmm3
    1c68:	f2 44 0f 58 cf       	addsd  xmm9,xmm7
    1c6d:	f2 0f 5c f8          	subsd  xmm7,xmm0
    1c71:	f2 0f 58 f6          	addsd  xmm6,xmm6
    1c75:	f2 44 0f 59 c9       	mulsd  xmm9,xmm1
    1c7a:	f2 0f 59 f9          	mulsd  xmm7,xmm1
    1c7e:	66 0f 28 c8          	movapd xmm1,xmm0
    1c82:	f2 0f 58 cd          	addsd  xmm1,xmm5
    1c86:	f2 0f 5c e8          	subsd  xmm5,xmm0
    1c8a:	e9 fb fd ff ff       	jmp    1a8a <fopen@plt+0x94a>
    1c8f:	48 8d 3d 31 15 00 00 	lea    rdi,[rip+0x1531]        # 31c7 <fopen@plt+0x2087>
    1c96:	c7 05 70 33 00 00 01 	mov    DWORD PTR [rip+0x3370],0x1        # 5010 <fopen@plt+0x3ed0>
    1c9d:	00 00 00 
    1ca0:	c7 05 96 33 00 00 00 	mov    DWORD PTR [rip+0x3396],0x0        # 5040 <stdin@GLIBC_2.2.5+0x10>
    1ca7:	00 00 00 
    1caa:	e8 81 f3 ff ff       	call   1030 <getenv@plt>
    1caf:	48 8d 15 0a 15 00 00 	lea    rdx,[rip+0x150a]        # 31c0 <fopen@plt+0x2080>
    1cb6:	48 8d 35 11 15 00 00 	lea    rsi,[rip+0x1511]        # 31ce <fopen@plt+0x208e>
    1cbd:	48 85 c0             	test   rax,rax
    1cc0:	48 0f 45 d0          	cmovne rdx,rax
    1cc4:	48 89 d7             	mov    rdi,rdx
    1cc7:	e8 74 f4 ff ff       	call   1140 <fopen@plt>
    1ccc:	49 89 c6             	mov    r14,rax
    1ccf:	48 85 c0             	test   rax,rax
    1cd2:	0f 84 9d fc ff ff    	je     1975 <fopen@plt+0x835>
    1cd8:	4c 8d 3d 81 33 00 00 	lea    r15,[rip+0x3381]        # 5060 <stdin@GLIBC_2.2.5+0x30>
    1cdf:	90                   	nop
    1ce0:	4c 89 f2             	mov    rdx,r14
    1ce3:	be 00 01 00 00       	mov    esi,0x100
    1ce8:	48 8d bd c0 fe ff ff 	lea    rdi,[rbp-0x140]
    1cef:	e8 ec f3 ff ff       	call   10e0 <fgets@plt>
    1cf4:	48 85 c0             	test   rax,rax
    1cf7:	0f 84 d3 00 00 00    	je     1dd0 <fopen@plt+0xc90>
    1cfd:	8b 1d 3d 33 00 00    	mov    ebx,DWORD PTR [rip+0x333d]        # 5040 <stdin@GLIBC_2.2.5+0x10>
    1d03:	83 fb 07             	cmp    ebx,0x7
    1d06:	0f 8f c4 00 00 00    	jg     1dd0 <fopen@plt+0xc90>
    1d0c:	0f b6 85 c0 fe ff ff 	movzx  eax,BYTE PTR [rbp-0x140]
    1d13:	3c 23                	cmp    al,0x23
    1d15:	74 c9                	je     1ce0 <fopen@plt+0xba0>
    1d17:	3c 0a                	cmp    al,0xa
    1d19:	74 c5                	je     1ce0 <fopen@plt+0xba0>
    1d1b:	31 c0                	xor    eax,eax
    1d1d:	48 8d 8d 88 fe ff ff 	lea    rcx,[rbp-0x178]
    1d24:	48 8d 95 a0 fe ff ff 	lea    rdx,[rbp-0x160]
    1d2b:	4c 8d 8d 98 fe ff ff 	lea    r9,[rbp-0x168]
    1d32:	4c 8d 85 90 fe ff ff 	lea    r8,[rbp-0x170]
    1d39:	48 8d 35 90 14 00 00 	lea    rsi,[rip+0x1490]        # 31d0 <fopen@plt+0x2090>
    1d40:	48 8d bd c0 fe ff ff 	lea    rdi,[rbp-0x140]
    1d47:	e8 14 f3 ff ff       	call   1060 <__isoc23_sscanf@plt>
    1d4c:	83 f8 04             	cmp    eax,0x4
    1d4f:	75 8f                	jne    1ce0 <fopen@plt+0xba0>
    1d51:	81 bd a0 fe ff ff 70 	cmp    DWORD PTR [rbp-0x160],0x6b616570
    1d58:	65 61 6b 
    1d5b:	0f 84 9d 00 00 00    	je     1dfe <fopen@plt+0xcbe>
    1d61:	81 bd a0 fe ff ff 6e 	cmp    DWORD PTR [rbp-0x160],0x63746f6e
    1d68:	6f 74 63 
    1d6b:	74 70                	je     1ddd <fopen@plt+0xc9d>
    1d6d:	48 b8 6c 6f 77 73 68 	movabs rax,0x666c656873776f6c
    1d74:	65 6c 66 
    1d77:	48 39 85 a0 fe ff ff 	cmp    QWORD PTR [rbp-0x160],rax
    1d7e:	74 6e                	je     1dee <fopen@plt+0xcae>
    1d80:	48 b8 68 69 67 68 73 	movabs rax,0x6c65687368676968
    1d87:	68 65 6c 
    1d8a:	48 39 85 a0 fe ff ff 	cmp    QWORD PTR [rbp-0x160],rax
    1d91:	74 7a                	je     1e0d <fopen@plt+0xccd>
    1d93:	31 c9                	xor    ecx,ecx
    1d95:	48 63 c3             	movsxd rax,ebx
    1d98:	66 0f 10 85 88 fe ff 	movupd xmm0,XMMWORD PTR [rbp-0x178]
    1d9f:	ff 
    1da0:	83 c3 01             	add    ebx,0x1
    1da3:	48 c1 e0 05          	shl    rax,0x5
    1da7:	89 1d 93 32 00 00    	mov    DWORD PTR [rip+0x3293],ebx        # 5040 <stdin@GLIBC_2.2.5+0x10>
    1dad:	41 89 0c 07          	mov    DWORD PTR [r15+rax*1],ecx
    1db1:	48 8d 0d b0 32 00 00 	lea    rcx,[rip+0x32b0]        # 5068 <stdin@GLIBC_2.2.5+0x38>
    1db8:	0f 11 04 01          	movups XMMWORD PTR [rcx+rax*1],xmm0
    1dbc:	f2 0f 10 85 98 fe ff 	movsd  xmm0,QWORD PTR [rbp-0x168]
    1dc3:	ff 
    1dc4:	f2 41 0f 11 44 07 18 	movsd  QWORD PTR [r15+rax*1+0x18],xmm0
    1dcb:	e9 10 ff ff ff       	jmp    1ce0 <fopen@plt+0xba0>
    1dd0:	4c 89 f7             	mov    rdi,r14
    1dd3:	e8 b8 f2 ff ff       	call   1090 <fclose@plt>
    1dd8:	e9 98 fb ff ff       	jmp    1975 <fopen@plt+0x835>
    1ddd:	b9 01 00 00 00       	mov    ecx,0x1
    1de2:	66 83 bd a4 fe ff ff 	cmp    WORD PTR [rbp-0x15c],0x68
    1de9:	68 
    1dea:	75 81                	jne    1d6d <fopen@plt+0xc2d>
    1dec:	eb a7                	jmp    1d95 <fopen@plt+0xc55>
    1dee:	b9 02 00 00 00       	mov    ecx,0x2
    1df3:	80 bd a8 fe ff ff 00 	cmp    BYTE PTR [rbp-0x158],0x0
    1dfa:	74 99                	je     1d95 <fopen@plt+0xc55>
    1dfc:	eb 82                	jmp    1d80 <fopen@plt+0xc40>
    1dfe:	80 bd a4 fe ff ff 00 	cmp    BYTE PTR [rbp-0x15c],0x0
    1e05:	0f 85 56 ff ff ff    	jne    1d61 <fopen@plt+0xc21>
    1e0b:	eb 86                	jmp    1d93 <fopen@plt+0xc53>
    1e0d:	b9 03 00 00 00       	mov    ecx,0x3
    1e12:	66 83 bd a8 fe ff ff 	cmp    WORD PTR [rbp-0x158],0x66
    1e19:	66 
    1e1a:	0f 85 73 ff ff ff    	jne    1d93 <fopen@plt+0xc53>
    1e20:	e9 70 ff ff ff       	jmp    1d95 <fopen@plt+0xc55>
    1e25:	e8 76 f2 ff ff       	call   10a0 <__stack_chk_fail@plt>
    1e2a:	66 0f 1f 44 00 00    	nop    WORD PTR [rax+rax*1+0x0]
    1e30:	55                   	push   rbp
    1e31:	48 89 e5             	mov    rbp,rsp
    1e34:	41 56                	push   r14
    1e36:	49 89 fe             	mov    r14,rdi
    1e39:	41 55                	push   r13
    1e3b:	49 89 d5             	mov    r13,rdx
    1e3e:	41 54                	push   r12
    1e40:	49 89 f4             	mov    r12,rsi
    1e43:	53                   	push   rbx
    1e44:	48 8d 1c f5 00 00 00 	lea    rbx,[rsi*8+0x0]
    1e4b:	00 
    1e4c:	48 89 df             	mov    rdi,rbx
    1e4f:	e8 bc f2 ff ff       	call   1110 <malloc@plt>
    1e54:	48 85 c0             	test   rax,rax
    1e57:	0f 84 00 01 00 00    	je     1f5d <fopen@plt+0xe1d>
    1e5d:	48 89 c7             	mov    rdi,rax
    1e60:	48 89 da             	mov    rdx,rbx
    1e63:	4c 89 f6             	mov    rsi,r14
    1e66:	e8 95 f2 ff ff       	call   1100 <memcpy@plt>
    1e6b:	48 8d 0d ce 14 00 00 	lea    rcx,[rip+0x14ce]        # 3340 <fopen@plt+0x2200>
    1e72:	48 89 c7             	mov    rdi,rax
    1e75:	48 8d 71 78          	lea    rsi,[rcx+0x78]
    1e79:	48 8d 14 18          	lea    rdx,[rax+rbx*1]
    1e7d:	4d 85 e4             	test   r12,r12
    1e80:	0f 84 ca 00 00 00    	je     1f50 <fopen@plt+0xe10>
    1e86:	66 0f ef db          	pxor   xmm3,xmm3
    1e8a:	f2 44 0f 10 09       	movsd  xmm9,QWORD PTR [rcx]
    1e8f:	f2 44 0f 10 41 08    	movsd  xmm8,QWORD PTR [rcx+0x8]
    1e95:	48 89 f8             	mov    rax,rdi
    1e98:	f2 0f 10 79 18       	movsd  xmm7,QWORD PTR [rcx+0x18]
    1e9d:	f2 0f 10 71 10       	movsd  xmm6,QWORD PTR [rcx+0x10]
    1ea2:	66 0f 28 c3          	movapd xmm0,xmm3
    1ea6:	f2 0f 10 69 20       	movsd  xmm5,QWORD PTR [rcx+0x20]
    1eab:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    1eb0:	f2 0f 10 10          	movsd  xmm2,QWORD PTR [rax]
    1eb4:	48 83 c0 08          	add    rax,0x8
    1eb8:	66 0f 28 ca          	movapd xmm1,xmm2
    1ebc:	f2 41 0f 59 c9       	mulsd  xmm1,xmm9
    1ec1:	f2 0f 58 c8          	addsd  xmm1,xmm0
    1ec5:	66 0f 28 c2          	movapd xmm0,xmm2
    1ec9:	f2 41 0f 59 c0       	mulsd  xmm0,xmm8
    1ece:	f2 0f 59 d6          	mulsd  xmm2,xmm6
    1ed2:	66 0f 28 e1          	movapd xmm4,xmm1
    1ed6:	f2 0f 11 48 f8       	movsd  QWORD PTR [rax-0x8],xmm1
    1edb:	f2 0f 59 e7          	mulsd  xmm4,xmm7
    1edf:	f2 0f 5c c4          	subsd  xmm0,xmm4
    1ee3:	66 0f 28 e1          	movapd xmm4,xmm1
    1ee7:	f2 0f 59 e5          	mulsd  xmm4,xmm5
    1eeb:	f2 0f 58 c3          	addsd  xmm0,xmm3
    1eef:	66 0f 28 da          	movapd xmm3,xmm2
    1ef3:	f2 0f 5c dc          	subsd  xmm3,xmm4
    1ef7:	48 39 c2             	cmp    rdx,rax
    1efa:	75 b4                	jne    1eb0 <fopen@plt+0xd70>
    1efc:	48 83 c1 28          	add    rcx,0x28
    1f00:	48 39 ce             	cmp    rsi,rcx
    1f03:	0f 85 7d ff ff ff    	jne    1e86 <fopen@plt+0xd46>
    1f09:	4d 85 e4             	test   r12,r12
    1f0c:	74 4b                	je     1f59 <fopen@plt+0xe19>
    1f0e:	31 c0                	xor    eax,eax
    1f10:	31 db                	xor    ebx,ebx
    1f12:	0f 1f 00             	nop    DWORD PTR [rax]
    1f15:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1f1c:	00 00 00 00 
    1f20:	f2 0f 10 04 c7       	movsd  xmm0,QWORD PTR [rdi+rax*8]
    1f25:	48 83 c3 01          	add    rbx,0x1
    1f29:	48 83 c0 06          	add    rax,0x6
    1f2d:	f2 41 0f 11 44 dd f8 	movsd  QWORD PTR [r13+rbx*8-0x8],xmm0
    1f34:	4c 39 e0             	cmp    rax,r12
    1f37:	72 e7                	jb     1f20 <fopen@plt+0xde0>
    1f39:	e8 02 f1 ff ff       	call   1040 <free@plt>
    1f3e:	48 89 d8             	mov    rax,rbx
    1f41:	5b                   	pop    rbx
    1f42:	41 5c                	pop    r12
    1f44:	41 5d                	pop    r13
    1f46:	41 5e                	pop    r14
    1f48:	5d                   	pop    rbp
    1f49:	c3                   	ret
    1f4a:	66 0f 1f 44 00 00    	nop    WORD PTR [rax+rax*1+0x0]
    1f50:	48 83 c1 28          	add    rcx,0x28
    1f54:	48 39 ce             	cmp    rsi,rcx
    1f57:	75 f7                	jne    1f50 <fopen@plt+0xe10>
    1f59:	31 db                	xor    ebx,ebx
    1f5b:	eb dc                	jmp    1f39 <fopen@plt+0xdf9>
    1f5d:	31 db                	xor    ebx,ebx
    1f5f:	eb dd                	jmp    1f3e <fopen@plt+0xdfe>
    1f61:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    1f65:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1f6c:	00 00 00 00 
    1f70:	48 85 f6             	test   rsi,rsi
    1f73:	0f 84 ea 00 00 00    	je     2063 <fopen@plt+0xf23>
    1f79:	48 83 fe 01          	cmp    rsi,0x1
    1f7d:	0f 84 e6 00 00 00    	je     2069 <fopen@plt+0xf29>
    1f83:	48 89 f1             	mov    rcx,rsi
    1f86:	f2 0f 10 35 62 13 00 	movsd  xmm6,QWORD PTR [rip+0x1362]        # 32f0 <fopen@plt+0x21b0>
    1f8d:	00 
    1f8e:	f2 0f 10 2d 62 13 00 	movsd  xmm5,QWORD PTR [rip+0x1362]        # 32f8 <fopen@plt+0x21b8>
    1f95:	00 
    1f96:	48 89 f8             	mov    rax,rdi
    1f99:	48 d1 e9             	shr    rcx,1
    1f9c:	f2 0f 10 25 5c 13 00 	movsd  xmm4,QWORD PTR [rip+0x135c]        # 3300 <fopen@plt+0x21c0>
    1fa3:	00 
    1fa4:	f2 0f 10 1d 5c 13 00 	movsd  xmm3,QWORD PTR [rip+0x135c]        # 3308 <fopen@plt+0x21c8>
    1fab:	00 
    1fac:	48 89 ca             	mov    rdx,rcx
    1faf:	66 0f 14 f6          	unpcklpd xmm6,xmm6
    1fb3:	66 0f 14 ed          	unpcklpd xmm5,xmm5
    1fb7:	48 c1 e2 04          	shl    rdx,0x4
    1fbb:	66 0f 14 e4          	unpcklpd xmm4,xmm4
    1fbf:	66 0f 14 db          	unpcklpd xmm3,xmm3
    1fc3:	48 01 fa             	add    rdx,rdi
    1fc6:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    1fcd:	00 00 00 
    1fd0:	66 0f 10 00          	movupd xmm0,XMMWORD PTR [rax]
    1fd4:	48 83 c0 10          	add    rax,0x10
    1fd8:	66 0f 59 c6          	mulpd  xmm0,xmm6
    1fdc:	66 0f 28 c8          	movapd xmm1,xmm0
    1fe0:	66 0f 28 d0          	movapd xmm2,xmm0
    1fe4:	66 0f 59 cd          	mulpd  xmm1,xmm5
    1fe8:	66 0f 59 d4          	mulpd  xmm2,xmm4
    1fec:	66 0f 59 c8          	mulpd  xmm1,xmm0
    1ff0:	66 0f 58 ca          	addpd  xmm1,xmm2
    1ff4:	66 0f 28 d0          	movapd xmm2,xmm0
    1ff8:	66 0f 59 d3          	mulpd  xmm2,xmm3
    1ffc:	66 0f 59 d0          	mulpd  xmm2,xmm0
    2000:	66 0f 59 c2          	mulpd  xmm0,xmm2
    2004:	66 0f 58 c1          	addpd  xmm0,xmm1
    2008:	0f 11 40 f0          	movups XMMWORD PTR [rax-0x10],xmm0
    200c:	48 39 d0             	cmp    rax,rdx
    200f:	75 bf                	jne    1fd0 <fopen@plt+0xe90>
    2011:	48 01 c9             	add    rcx,rcx
    2014:	48 39 ce             	cmp    rsi,rcx
    2017:	74 4f                	je     2068 <fopen@plt+0xf28>
    2019:	f2 0f 10 05 cf 12 00 	movsd  xmm0,QWORD PTR [rip+0x12cf]        # 32f0 <fopen@plt+0x21b0>
    2020:	00 
    2021:	f2 0f 59 04 cf       	mulsd  xmm0,QWORD PTR [rdi+rcx*8]
    2026:	f2 0f 10 0d ca 12 00 	movsd  xmm1,QWORD PTR [rip+0x12ca]        # 32f8 <fopen@plt+0x21b8>
    202d:	00 
    202e:	f2 0f 10 15 ca 12 00 	movsd  xmm2,QWORD PTR [rip+0x12ca]        # 3300 <fopen@plt+0x21c0>
    2035:	00 
    2036:	f2 0f 59 c8          	mulsd  xmm1,xmm0
    203a:	f2 0f 59 d0          	mulsd  xmm2,xmm0
    203e:	f2 0f 59 c8          	mulsd  xmm1,xmm0
    2042:	f2 0f 58 ca          	addsd  xmm1,xmm2
    2046:	f2 0f 10 15 ba 12 00 	movsd  xmm2,QWORD PTR [rip+0x12ba]        # 3308 <fopen@plt+0x21c8>
    204d:	00 
    204e:	f2 0f 59 d0          	mulsd  xmm2,xmm0
    2052:	f2 0f 59 d0          	mulsd  xmm2,xmm0
    2056:	f2 0f 59 c2          	mulsd  xmm0,xmm2
    205a:	f2 0f 58 c8          	addsd  xmm1,xmm0
    205e:	f2 0f 11 0c cf       	movsd  QWORD PTR [rdi+rcx*8],xmm1
    2063:	c3                   	ret
    2064:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    2068:	c3                   	ret
    2069:	31 c9                	xor    ecx,ecx
    206b:	eb ac                	jmp    2019 <fopen@plt+0xed9>
    206d:	0f 1f 00             	nop    DWORD PTR [rax]
    2070:	55                   	push   rbp
    2071:	48 89 e5             	mov    rbp,rsp
    2074:	41 57                	push   r15
    2076:	41 56                	push   r14
    2078:	41 55                	push   r13
    207a:	41 54                	push   r12
    207c:	45 31 e4             	xor    r12d,r12d
    207f:	53                   	push   rbx
    2080:	48 81 ec d8 0a 00 00 	sub    rsp,0xad8
    2087:	48 89 b5 10 f5 ff ff 	mov    QWORD PTR [rbp-0xaf0],rsi
    208e:	48 89 95 18 f5 ff ff 	mov    QWORD PTR [rbp-0xae8],rdx
    2095:	48 89 8d 08 f5 ff ff 	mov    QWORD PTR [rbp-0xaf8],rcx
    209c:	64 4c 8b 3c 25 28 00 	mov    r15,QWORD PTR fs:0x28
    20a3:	00 00 
    20a5:	4c 89 7d c8          	mov    QWORD PTR [rbp-0x38],r15
    20a9:	4c 8d bf 40 08 00 00 	lea    r15,[rdi+0x840]
    20b0:	48 c7 85 20 f5 ff ff 	mov    QWORD PTR [rbp-0xae0],0x108
    20b7:	08 01 00 00 
    20bb:	48 8b bd 20 f5 ff ff 	mov    rdi,QWORD PTR [rbp-0xae0]
    20c2:	48 39 bd 10 f5 ff ff 	cmp    QWORD PTR [rbp-0xaf0],rdi
    20c9:	0f 82 48 01 00 00    	jb     2217 <fopen@plt+0x10d7>
    20cf:	41 be ff ff ff ff    	mov    r14d,0xffffffff
    20d5:	f2 0f 10 05 33 12 00 	movsd  xmm0,QWORD PTR [rip+0x1233]        # 3310 <fopen@plt+0x21d0>
    20dc:	00 
    20dd:	45 31 ed             	xor    r13d,r13d
    20e0:	f2 0f 10 25 30 12 00 	movsd  xmm4,QWORD PTR [rip+0x1230]        # 3318 <fopen@plt+0x21d8>
    20e7:	00 
    20e8:	49 8d 9f c0 f9 ff ff 	lea    rbx,[r15-0x640]
    20ef:	90                   	nop
    20f0:	66 0f ef db          	pxor   xmm3,xmm3
    20f4:	f2 0f 58 c0          	addsd  xmm0,xmm0
    20f8:	48 89 d8             	mov    rax,rbx
    20fb:	66 0f 28 d3          	movapd xmm2,xmm3
    20ff:	eb 43                	jmp    2144 <fopen@plt+0x1004>
    2101:	0f 1f 84 00 00 00 00 	nop    DWORD PTR [rax+rax*1+0x0]
    2108:	00 
    2109:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2110:	00 00 00 00 
    2114:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    211b:	00 00 00 00 
    211f:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2126:	00 00 00 00 
    212a:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2131:	00 00 00 00 
    2135:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    213c:	00 00 00 00 
    2140:	66 0f 28 d1          	movapd xmm2,xmm1
    2144:	66 0f 28 c8          	movapd xmm1,xmm0
    2148:	48 83 c0 08          	add    rax,0x8
    214c:	f2 0f 59 ca          	mulsd  xmm1,xmm2
    2150:	f2 0f 58 48 f8       	addsd  xmm1,QWORD PTR [rax-0x8]
    2155:	f2 0f 5c cb          	subsd  xmm1,xmm3
    2159:	66 0f 28 da          	movapd xmm3,xmm2
    215d:	4c 39 f8             	cmp    rax,r15
    2160:	75 de                	jne    2140 <fopen@plt+0x1000>
    2162:	f2 0f 59 c1          	mulsd  xmm0,xmm1
    2166:	66 0f 28 d9          	movapd xmm3,xmm1
    216a:	66 0f 28 ea          	movapd xmm5,xmm2
    216e:	f2 0f 59 d9          	mulsd  xmm3,xmm1
    2172:	f2 0f 59 ea          	mulsd  xmm5,xmm2
    2176:	f2 0f 59 c2          	mulsd  xmm0,xmm2
    217a:	f2 0f 58 dd          	addsd  xmm3,xmm5
    217e:	f2 0f 5c d8          	subsd  xmm3,xmm0
    2182:	66 0f 2f dc          	comisd xmm3,xmm4
    2186:	f2 0f 5f dc          	maxsd  xmm3,xmm4
    218a:	45 0f 47 f5          	cmova  r14d,r13d
    218e:	41 83 c5 01          	add    r13d,0x1
    2192:	41 83 fd 10          	cmp    r13d,0x10
    2196:	74 43                	je     21db <fopen@plt+0x109b>
    2198:	66 0f ef c0          	pxor   xmm0,xmm0
    219c:	f2 0f 11 9d 28 f5 ff 	movsd  QWORD PTR [rbp-0xad8],xmm3
    21a3:	ff 
    21a4:	f2 41 0f 2a c5       	cvtsi2sd xmm0,r13d
    21a9:	f2 0f 59 05 6f 11 00 	mulsd  xmm0,QWORD PTR [rip+0x116f]        # 3320 <fopen@plt+0x21e0>
    21b0:	00 
    21b1:	f2 0f 58 05 6f 11 00 	addsd  xmm0,QWORD PTR [rip+0x116f]        # 3328 <fopen@plt+0x21e8>
    21b8:	00 
    21b9:	f2 0f 59 05 17 11 00 	mulsd  xmm0,QWORD PTR [rip+0x1117]        # 32d8 <fopen@plt+0x2198>
    21c0:	00 
    21c1:	f2 0f 5e 05 67 11 00 	divsd  xmm0,QWORD PTR [rip+0x1167]        # 3330 <fopen@plt+0x21f0>
    21c8:	00 
    21c9:	e8 02 ef ff ff       	call   10d0 <cos@plt>
    21ce:	f2 0f 10 a5 28 f5 ff 	movsd  xmm4,QWORD PTR [rbp-0xad8]
    21d5:	ff 
    21d6:	e9 15 ff ff ff       	jmp    20f0 <fopen@plt+0xfb0>
    21db:	41 83 fe ff          	cmp    r14d,0xffffffff
    21df:	74 36                	je     2217 <fopen@plt+0x10d7>
    21e1:	48 8d 8d 30 f5 ff ff 	lea    rcx,[rbp-0xad0]
    21e8:	4c 8d b8 40 06 00 00 	lea    r15,[rax+0x640]
    21ef:	48 81 85 20 f5 ff ff 	add    QWORD PTR [rbp-0xae0],0xc8
    21f6:	c8 00 00 00 
    21fa:	46 89 34 a1          	mov    DWORD PTR [rcx+r12*4],r14d
    21fe:	49 83 c4 01          	add    r12,0x1
    2202:	49 81 fc 58 02 00 00 	cmp    r12,0x258
    2209:	0f 85 ac fe ff ff    	jne    20bb <fopen@plt+0xf7b>
    220f:	41 bc 2c 01 00 00    	mov    r12d,0x12c
    2215:	eb 14                	jmp    222b <fopen@plt+0x10eb>
    2217:	41 83 fc 07          	cmp    r12d,0x7
    221b:	0f 8e 63 02 00 00    	jle    2484 <fopen@plt+0x1344>
    2221:	41 d1 fc             	sar    r12d,1
    2224:	48 8d 8d 30 f5 ff ff 	lea    rcx,[rbp-0xad0]
    222b:	48 8d bd 90 fe ff ff 	lea    rdi,[rbp-0x170]
    2232:	31 d2                	xor    edx,edx
    2234:	48 89 fe             	mov    rsi,rdi
    2237:	0f b6 01             	movzx  eax,BYTE PTR [rcx]
    223a:	83 c2 01             	add    edx,0x1
    223d:	48 83 c1 08          	add    rcx,0x8
    2241:	48 83 c6 01          	add    rsi,0x1
    2245:	c1 e0 04             	shl    eax,0x4
    2248:	0a 41 fc             	or     al,BYTE PTR [rcx-0x4]
    224b:	88 46 ff             	mov    BYTE PTR [rsi-0x1],al
    224e:	44 39 e2             	cmp    edx,r12d
    2251:	7d 08                	jge    225b <fopen@plt+0x111b>
    2253:	81 fa 2c 01 00 00    	cmp    edx,0x12c
    2259:	75 dc                	jne    2237 <fopen@plt+0x10f7>
    225b:	80 bd 90 fe ff ff a5 	cmp    BYTE PTR [rbp-0x170],0xa5
    2262:	0f 85 1c 02 00 00    	jne    2484 <fopen@plt+0x1344>
    2268:	80 bd 91 fe ff ff 5a 	cmp    BYTE PTR [rbp-0x16f],0x5a
    226f:	0f 85 0f 02 00 00    	jne    2484 <fopen@plt+0x1344>
    2275:	0f b6 8d 92 fe ff ff 	movzx  ecx,BYTE PTR [rbp-0x16e]
    227c:	44 8d 41 03          	lea    r8d,[rcx+0x3]
    2280:	89 ca                	mov    edx,ecx
    2282:	45 39 e0             	cmp    r8d,r12d
    2285:	0f 8d f9 01 00 00    	jge    2484 <fopen@plt+0x1344>
    228b:	85 c9                	test   ecx,ecx
    228d:	0f 84 fb 01 00 00    	je     248e <fopen@plt+0x134e>
    2293:	8d 41 ff             	lea    eax,[rcx-0x1]
    2296:	83 f8 0e             	cmp    eax,0xe
    2299:	0f 86 dc 01 00 00    	jbe    247b <fopen@plt+0x133b>
    229f:	89 ce                	mov    esi,ecx
    22a1:	48 89 f8             	mov    rax,rdi
    22a4:	66 0f ef c0          	pxor   xmm0,xmm0
    22a8:	c1 ee 04             	shr    esi,0x4
    22ab:	41 89 f1             	mov    r9d,esi
    22ae:	49 c1 e1 04          	shl    r9,0x4
    22b2:	49 01 f9             	add    r9,rdi
    22b5:	f3 0f 6f 70 03       	movdqu xmm6,XMMWORD PTR [rax+0x3]
    22ba:	48 83 c0 10          	add    rax,0x10
    22be:	66 0f ef c6          	pxor   xmm0,xmm6
    22c2:	4c 39 c8             	cmp    rax,r9
    22c5:	75 ee                	jne    22b5 <fopen@plt+0x1175>
    22c7:	66 0f 6f c8          	movdqa xmm1,xmm0
    22cb:	c1 e6 04             	shl    esi,0x4
    22ce:	66 0f 73 d9 08       	psrldq xmm1,0x8
    22d3:	66 0f ef c1          	pxor   xmm0,xmm1
    22d7:	66 0f 6f c8          	movdqa xmm1,xmm0
    22db:	66 0f 73 d9 04       	psrldq xmm1,0x4
    22e0:	66 0f ef c1          	pxor   xmm0,xmm1
    22e4:	66 0f 6f c8          	movdqa xmm1,xmm0
    22e8:	66 0f 73 d9 02       	psrldq xmm1,0x2
    22ed:	66 0f ef c1          	pxor   xmm0,xmm1
    22f1:	66 0f 6f c8          	movdqa xmm1,xmm0
    22f5:	66 0f 73 d9 01       	psrldq xmm1,0x1
    22fa:	66 0f ef c1          	pxor   xmm0,xmm1
    22fe:	66 0f 7e c0          	movd   eax,xmm0
    2302:	31 d0                	xor    eax,edx
    2304:	39 ce                	cmp    esi,ecx
    2306:	74 41                	je     2349 <fopen@plt+0x1209>
    2308:	41 89 f1             	mov    r9d,esi
    230b:	83 c6 03             	add    esi,0x3
    230e:	4c 29 cf             	sub    rdi,r9
    2311:	4d 89 ca             	mov    r10,r9
    2314:	48 01 f7             	add    rdi,rsi
    2317:	49 f7 d2             	not    r10
    231a:	49 8d 71 01          	lea    rsi,[r9+0x1]
    231e:	41 01 ca             	add    r10d,ecx
    2321:	42 32 04 0f          	xor    al,BYTE PTR [rdi+r9*1]
    2325:	39 f1                	cmp    ecx,esi
    2327:	7e 20                	jle    2349 <fopen@plt+0x1209>
    2329:	41 83 e2 01          	and    r10d,0x1
    232d:	74 0b                	je     233a <fopen@plt+0x11fa>
    232f:	32 04 37             	xor    al,BYTE PTR [rdi+rsi*1]
    2332:	49 8d 71 02          	lea    rsi,[r9+0x2]
    2336:	39 f1                	cmp    ecx,esi
    2338:	7e 0f                	jle    2349 <fopen@plt+0x1209>
    233a:	32 04 37             	xor    al,BYTE PTR [rdi+rsi*1]
    233d:	48 83 c6 02          	add    rsi,0x2
    2341:	32 44 3e ff          	xor    al,BYTE PTR [rsi+rdi*1-0x1]
    2345:	39 f1                	cmp    ecx,esi
    2347:	7f f1                	jg     233a <fopen@plt+0x11fa>
    2349:	45 89 c0             	mov    r8d,r8d
    234c:	42 38 84 05 90 fe ff 	cmp    BYTE PTR [rbp+r8*1-0x170],al
    2353:	ff 
    2354:	0f 85 2a 01 00 00    	jne    2484 <fopen@plt+0x1344>
    235a:	0f b6 c2             	movzx  eax,dl
    235d:	83 f8 40             	cmp    eax,0x40
    2360:	73 58                	jae    23ba <fopen@plt+0x127a>
    2362:	a8 20                	test   al,0x20
    2364:	0f 85 2b 01 00 00    	jne    2495 <fopen@plt+0x1355>
    236a:	a8 10                	test   al,0x10
    236c:	0f 85 65 01 00 00    	jne    24d7 <fopen@plt+0x1397>
    2372:	a8 08                	test   al,0x8
    2374:	0f 85 82 01 00 00    	jne    24fc <fopen@plt+0x13bc>
    237a:	a8 04                	test   al,0x4
    237c:	0f 85 a6 01 00 00    	jne    2528 <fopen@plt+0x13e8>
    2382:	85 c0                	test   eax,eax
    2384:	0f 85 c0 00 00 00    	jne    244a <fopen@plt+0x130a>
    238a:	48 8b 85 08 f5 ff ff 	mov    rax,QWORD PTR [rbp-0xaf8]
    2391:	89 08                	mov    DWORD PTR [rax],ecx
    2393:	31 c0                	xor    eax,eax
    2395:	48 8b 55 c8          	mov    rdx,QWORD PTR [rbp-0x38]
    2399:	64 48 2b 14 25 28 00 	sub    rdx,QWORD PTR fs:0x28
    23a0:	00 00 
    23a2:	0f 85 77 01 00 00    	jne    251f <fopen@plt+0x13df>
    23a8:	48 81 c4 d8 0a 00 00 	add    rsp,0xad8
    23af:	5b                   	pop    rbx
    23b0:	41 5c                	pop    r12
    23b2:	41 5d                	pop    r13
    23b4:	41 5e                	pop    r14
    23b6:	41 5f                	pop    r15
    23b8:	5d                   	pop    rbp
    23b9:	c3                   	ret
    23ba:	48 8d b4 05 93 fe ff 	lea    rsi,[rbp+rax*1-0x16d]
    23c1:	ff 
    23c2:	48 8b 95 18 f5 ff ff 	mov    rdx,QWORD PTR [rbp-0xae8]
    23c9:	f3 0f 6f 46 c0       	movdqu xmm0,XMMWORD PTR [rsi-0x40]
    23ce:	0f 11 44 02 c0       	movups XMMWORD PTR [rdx+rax*1-0x40],xmm0
    23d3:	f3 0f 6f 46 d0       	movdqu xmm0,XMMWORD PTR [rsi-0x30]
    23d8:	0f 11 44 02 d0       	movups XMMWORD PTR [rdx+rax*1-0x30],xmm0
    23dd:	f3 0f 6f 46 e0       	movdqu xmm0,XMMWORD PTR [rsi-0x20]
    23e2:	0f 11 44 02 e0       	movups XMMWORD PTR [rdx+rax*1-0x20],xmm0
    23e7:	f3 0f 6f 46 f0       	movdqu xmm0,XMMWORD PTR [rsi-0x10]
    23ec:	0f 11 44 02 f0       	movups XMMWORD PTR [rdx+rax*1-0x10],xmm0
    23f1:	83 e8 01             	sub    eax,0x1
    23f4:	83 f8 40             	cmp    eax,0x40
    23f7:	72 91                	jb     238a <fopen@plt+0x124a>
    23f9:	83 e0 c0             	and    eax,0xffffffc0
    23fc:	31 f6                	xor    esi,esi
    23fe:	89 f2                	mov    edx,esi
    2400:	48 8b bd 18 f5 ff ff 	mov    rdi,QWORD PTR [rbp-0xae8]
    2407:	83 c6 40             	add    esi,0x40
    240a:	f3 0f 6f 9c 15 93 fe 	movdqu xmm3,XMMWORD PTR [rbp+rdx*1-0x16d]
    2411:	ff ff 
    2413:	f3 0f 6f 94 15 a3 fe 	movdqu xmm2,XMMWORD PTR [rbp+rdx*1-0x15d]
    241a:	ff ff 
    241c:	f3 0f 6f 8c 15 b3 fe 	movdqu xmm1,XMMWORD PTR [rbp+rdx*1-0x14d]
    2423:	ff ff 
    2425:	f3 0f 6f 84 15 c3 fe 	movdqu xmm0,XMMWORD PTR [rbp+rdx*1-0x13d]
    242c:	ff ff 
    242e:	0f 11 1c 17          	movups XMMWORD PTR [rdi+rdx*1],xmm3
    2432:	0f 11 54 17 10       	movups XMMWORD PTR [rdi+rdx*1+0x10],xmm2
    2437:	0f 11 4c 17 20       	movups XMMWORD PTR [rdi+rdx*1+0x20],xmm1
    243c:	0f 11 44 17 30       	movups XMMWORD PTR [rdi+rdx*1+0x30],xmm0
    2441:	39 c6                	cmp    esi,eax
    2443:	72 b9                	jb     23fe <fopen@plt+0x12be>
    2445:	e9 40 ff ff ff       	jmp    238a <fopen@plt+0x124a>
    244a:	0f b6 95 93 fe ff ff 	movzx  edx,BYTE PTR [rbp-0x16d]
    2451:	48 8b bd 18 f5 ff ff 	mov    rdi,QWORD PTR [rbp-0xae8]
    2458:	88 17                	mov    BYTE PTR [rdi],dl
    245a:	a8 02                	test   al,0x2
    245c:	0f 84 28 ff ff ff    	je     238a <fopen@plt+0x124a>
    2462:	0f b7 94 05 91 fe ff 	movzx  edx,WORD PTR [rbp+rax*1-0x16f]
    2469:	ff 
    246a:	48 8b bd 18 f5 ff ff 	mov    rdi,QWORD PTR [rbp-0xae8]
    2471:	66 89 54 07 fe       	mov    WORD PTR [rdi+rax*1-0x2],dx
    2476:	e9 0f ff ff ff       	jmp    238a <fopen@plt+0x124a>
    247b:	89 c8                	mov    eax,ecx
    247d:	31 f6                	xor    esi,esi
    247f:	e9 84 fe ff ff       	jmp    2308 <fopen@plt+0x11c8>
    2484:	b8 ff ff ff ff       	mov    eax,0xffffffff
    2489:	e9 07 ff ff ff       	jmp    2395 <fopen@plt+0x1255>
    248e:	31 c0                	xor    eax,eax
    2490:	e9 b4 fe ff ff       	jmp    2349 <fopen@plt+0x1209>
    2495:	f3 0f 6f 85 93 fe ff 	movdqu xmm0,XMMWORD PTR [rbp-0x16d]
    249c:	ff 
    249d:	48 8b b5 18 f5 ff ff 	mov    rsi,QWORD PTR [rbp-0xae8]
    24a4:	0f 11 06             	movups XMMWORD PTR [rsi],xmm0
    24a7:	f3 0f 6f 85 a3 fe ff 	movdqu xmm0,XMMWORD PTR [rbp-0x15d]
    24ae:	ff 
    24af:	48 8d 54 06 20       	lea    rdx,[rsi+rax*1+0x20]
    24b4:	48 8d 84 05 b3 fe ff 	lea    rax,[rbp+rax*1-0x14d]
    24bb:	ff 
    24bc:	0f 11 46 10          	movups XMMWORD PTR [rsi+0x10],xmm0
    24c0:	f3 0f 6f 40 c0       	movdqu xmm0,XMMWORD PTR [rax-0x40]
    24c5:	0f 11 42 c0          	movups XMMWORD PTR [rdx-0x40],xmm0
    24c9:	f3 0f 6f 40 d0       	movdqu xmm0,XMMWORD PTR [rax-0x30]
    24ce:	0f 11 42 d0          	movups XMMWORD PTR [rdx-0x30],xmm0
    24d2:	e9 b3 fe ff ff       	jmp    238a <fopen@plt+0x124a>
    24d7:	f3 0f 6f 85 93 fe ff 	movdqu xmm0,XMMWORD PTR [rbp-0x16d]
    24de:	ff 
    24df:	48 8b 95 18 f5 ff ff 	mov    rdx,QWORD PTR [rbp-0xae8]
    24e6:	0f 11 02             	movups XMMWORD PTR [rdx],xmm0
    24e9:	f3 0f 6f 84 05 83 fe 	movdqu xmm0,XMMWORD PTR [rbp+rax*1-0x17d]
    24f0:	ff ff 
    24f2:	0f 11 44 02 f0       	movups XMMWORD PTR [rdx+rax*1-0x10],xmm0
    24f7:	e9 8e fe ff ff       	jmp    238a <fopen@plt+0x124a>
    24fc:	48 8b 95 93 fe ff ff 	mov    rdx,QWORD PTR [rbp-0x16d]
    2503:	48 8b b5 18 f5 ff ff 	mov    rsi,QWORD PTR [rbp-0xae8]
    250a:	48 89 16             	mov    QWORD PTR [rsi],rdx
    250d:	48 8b 94 05 8b fe ff 	mov    rdx,QWORD PTR [rbp+rax*1-0x175]
    2514:	ff 
    2515:	48 89 54 06 f8       	mov    QWORD PTR [rsi+rax*1-0x8],rdx
    251a:	e9 6b fe ff ff       	jmp    238a <fopen@plt+0x124a>
    251f:	e8 7c eb ff ff       	call   10a0 <__stack_chk_fail@plt>
    2524:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    2528:	8b 95 93 fe ff ff    	mov    edx,DWORD PTR [rbp-0x16d]
    252e:	48 8b b5 18 f5 ff ff 	mov    rsi,QWORD PTR [rbp-0xae8]
    2535:	89 16                	mov    DWORD PTR [rsi],edx
    2537:	8b 94 05 8f fe ff ff 	mov    edx,DWORD PTR [rbp+rax*1-0x171]
    253e:	89 54 06 fc          	mov    DWORD PTR [rsi+rax*1-0x4],edx
    2542:	e9 43 fe ff ff       	jmp    238a <fopen@plt+0x124a>
    2547:	66 0f 1f 84 00 00 00 	nop    WORD PTR [rax+rax*1+0x0]
    254e:	00 00 
    2550:	48 ba ab aa aa aa aa 	movabs rdx,0xaaaaaaaaaaaaaaab
    2557:	aa aa aa 
    255a:	55                   	push   rbp
    255b:	48 89 f0             	mov    rax,rsi
    255e:	48 f7 e2             	mul    rdx
    2561:	48 89 e5             	mov    rbp,rsp
    2564:	41 54                	push   r12
    2566:	53                   	push   rbx
    2567:	48 c1 ea 02          	shr    rdx,0x2
    256b:	48 81 ec 60 01 00 00 	sub    rsp,0x160
    2572:	64 4c 8b 24 25 28 00 	mov    r12,QWORD PTR fs:0x28
    2579:	00 00 
    257b:	4c 89 65 e8          	mov    QWORD PTR [rbp-0x18],r12
    257f:	49 89 fc             	mov    r12,rdi
    2582:	48 8d 3c d5 20 00 00 	lea    rdi,[rdx*8+0x20]
    2589:	00 
    258a:	48 89 b5 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],rsi
    2591:	e8 7a eb ff ff       	call   1110 <malloc@plt>
    2596:	48 85 c0             	test   rax,rax
    2599:	0f 84 da 00 00 00    	je     2679 <fopen@plt+0x1539>
    259f:	48 8b b5 98 fe ff ff 	mov    rsi,QWORD PTR [rbp-0x168]
    25a6:	4c 89 e7             	mov    rdi,r12
    25a9:	48 89 c2             	mov    rdx,rax
    25ac:	48 89 c3             	mov    rbx,rax
    25af:	e8 7c f8 ff ff       	call   1e30 <fopen@plt+0xcf0>
    25b4:	48 8d 8d ac fe ff ff 	lea    rcx,[rbp-0x154]
    25bb:	48 8d 95 b0 fe ff ff 	lea    rdx,[rbp-0x150]
    25c2:	48 89 df             	mov    rdi,rbx
    25c5:	c7 85 ac fe ff ff 00 	mov    DWORD PTR [rbp-0x154],0x0
    25cc:	00 00 00 
    25cf:	48 89 c6             	mov    rsi,rax
    25d2:	e8 99 fa ff ff       	call   2070 <fopen@plt+0xf30>
    25d7:	41 89 c4             	mov    r12d,eax
    25da:	85 c0                	test   eax,eax
    25dc:	74 32                	je     2610 <fopen@plt+0x14d0>
    25de:	45 31 e4             	xor    r12d,r12d
    25e1:	48 89 df             	mov    rdi,rbx
    25e4:	e8 57 ea ff ff       	call   1040 <free@plt>
    25e9:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    25ed:	64 48 2b 04 25 28 00 	sub    rax,QWORD PTR fs:0x28
    25f4:	00 00 
    25f6:	75 7c                	jne    2674 <fopen@plt+0x1534>
    25f8:	48 81 c4 60 01 00 00 	add    rsp,0x160
    25ff:	44 89 e0             	mov    eax,r12d
    2602:	5b                   	pop    rbx
    2603:	41 5c                	pop    r12
    2605:	5d                   	pop    rbp
    2606:	c3                   	ret
    2607:	66 0f 1f 84 00 00 00 	nop    WORD PTR [rax+rax*1+0x0]
    260e:	00 00 
    2610:	8b 85 ac fe ff ff    	mov    eax,DWORD PTR [rbp-0x154]
    2616:	31 f6                	xor    esi,esi
    2618:	ba 01 00 00 00       	mov    edx,0x1
    261d:	83 f8 01             	cmp    eax,0x1
    2620:	7f 34                	jg     2656 <fopen@plt+0x1516>
    2622:	eb bd                	jmp    25e1 <fopen@plt+0x14a1>
    2624:	66 0f 1f 44 00 00    	nop    WORD PTR [rax+rax*1+0x0]
    262a:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2631:	00 00 00 00 
    2635:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    263c:	00 00 00 00 
    2640:	48 63 d2             	movsxd rdx,edx
    2643:	0f b6 94 15 b0 fe ff 	movzx  edx,BYTE PTR [rbp+rdx*1-0x150]
    264a:	ff 
    264b:	8d 74 16 02          	lea    esi,[rsi+rdx*1+0x2]
    264f:	8d 56 01             	lea    edx,[rsi+0x1]
    2652:	39 c2                	cmp    edx,eax
    2654:	7d 8b                	jge    25e1 <fopen@plt+0x14a1>
    2656:	48 63 ce             	movsxd rcx,esi
    2659:	0f b6 8c 0d b0 fe ff 	movzx  ecx,BYTE PTR [rbp+rcx*1-0x150]
    2660:	ff 
    2661:	83 e9 01             	sub    ecx,0x1
    2664:	83 f9 01             	cmp    ecx,0x1
    2667:	77 d7                	ja     2640 <fopen@plt+0x1500>
    2669:	41 bc 01 00 00 00    	mov    r12d,0x1
    266f:	e9 6d ff ff ff       	jmp    25e1 <fopen@plt+0x14a1>
    2674:	e8 27 ea ff ff       	call   10a0 <__stack_chk_fail@plt>
    2679:	45 31 e4             	xor    r12d,r12d
    267c:	e9 68 ff ff ff       	jmp    25e9 <fopen@plt+0x14a9>
    2681:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    2688:	00 00 00 
    268b:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    2690:	83 07 01             	add    DWORD PTR [rdi],0x1
    2693:	c3                   	ret
    2694:	90                   	nop
    2695:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    269c:	00 00 00 00 
    26a0:	55                   	push   rbp
    26a1:	48 8d 3d 57 0b 00 00 	lea    rdi,[rip+0xb57]        # 31ff <fopen@plt+0x20bf>
    26a8:	48 89 e5             	mov    rbp,rsp
    26ab:	53                   	push   rbx
    26ac:	48 83 ec 08          	sub    rsp,0x8
    26b0:	e8 7b e9 ff ff       	call   1030 <getenv@plt>
    26b5:	48 8d 3d 48 0b 00 00 	lea    rdi,[rip+0xb48]        # 3204 <fopen@plt+0x20c4>
    26bc:	48 89 c3             	mov    rbx,rax
    26bf:	e8 ac e9 ff ff       	call   1070 <puts@plt>
    26c4:	48 85 db             	test   rbx,rbx
    26c7:	74 27                	je     26f0 <fopen@plt+0x15b0>
    26c9:	48 89 de             	mov    rsi,rbx
    26cc:	48 8d 3d 47 0b 00 00 	lea    rdi,[rip+0xb47]        # 321a <fopen@plt+0x20da>
    26d3:	31 c0                	xor    eax,eax
    26d5:	e8 d6 e9 ff ff       	call   10b0 <printf@plt>
    26da:	48 8b 3d 3f 29 00 00 	mov    rdi,QWORD PTR [rip+0x293f]        # 5020 <stdout@GLIBC_2.2.5>
    26e1:	48 8b 5d f8          	mov    rbx,QWORD PTR [rbp-0x8]
    26e5:	c9                   	leave
    26e6:	e9 35 ea ff ff       	jmp    1120 <fflush@plt>
    26eb:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    26f0:	48 8d 3d 2d 0b 00 00 	lea    rdi,[rip+0xb2d]        # 3224 <fopen@plt+0x20e4>
    26f7:	e8 74 e9 ff ff       	call   1070 <puts@plt>
    26fc:	eb dc                	jmp    26da <fopen@plt+0x159a>
    26fe:	66 90                	xchg   ax,ax
    2700:	55                   	push   rbp
    2701:	bf 20 00 00 00       	mov    edi,0x20
    2706:	48 89 e5             	mov    rbp,rsp
    2709:	53                   	push   rbx
    270a:	48 83 ec 08          	sub    rsp,0x8
    270e:	e8 fd e9 ff ff       	call   1110 <malloc@plt>
    2713:	bf 30 00 00 00       	mov    edi,0x30
    2718:	48 89 c3             	mov    rbx,rax
    271b:	48 89 05 4e 2a 00 00 	mov    QWORD PTR [rip+0x2a4e],rax        # 5170 <stdin@GLIBC_2.2.5+0x140>
    2722:	e8 e9 e9 ff ff       	call   1110 <malloc@plt>
    2727:	f3 0f 7e 05 91 0c 00 	movq   xmm0,QWORD PTR [rip+0xc91]        # 33c0 <fopen@plt+0x2280>
    272e:	00 
    272f:	48 8d 15 5a ff ff ff 	lea    rdx,[rip+0xffffffffffffff5a]        # 2690 <fopen@plt+0x1550>
    2736:	48 8d 0d 63 ff ff ff 	lea    rcx,[rip+0xffffffffffffff63]        # 26a0 <fopen@plt+0x1560>
    273d:	0f 11 40 08          	movups XMMWORD PTR [rax+0x8],xmm0
    2741:	66 0f ef c0          	pxor   xmm0,xmm0
    2745:	0f 11 40 20          	movups XMMWORD PTR [rax+0x20],xmm0
    2749:	48 89 10             	mov    QWORD PTR [rax],rdx
    274c:	48 c7 40 18 04 00 00 	mov    QWORD PTR [rax+0x18],0x4
    2753:	00 
    2754:	48 89 05 1d 2a 00 00 	mov    QWORD PTR [rip+0x2a1d],rax        # 5178 <stdin@GLIBC_2.2.5+0x148>
    275b:	48 89 43 08          	mov    QWORD PTR [rbx+0x8],rax
    275f:	b8 2e 2e 2e 2e       	mov    eax,0x2e2e2e2e
    2764:	66 0f 6e c0          	movd   xmm0,eax
    2768:	48 89 0b             	mov    QWORD PTR [rbx],rcx
    276b:	c7 05 f3 29 00 00 00 	mov    DWORD PTR [rip+0x29f3],0x0        # 5168 <stdin@GLIBC_2.2.5+0x138>
    2772:	00 00 00 
    2775:	66 0f 70 c0 00       	pshufd xmm0,xmm0,0x0
    277a:	48 c7 05 db 29 00 00 	mov    QWORD PTR [rip+0x29db],0x0        # 5160 <stdin@GLIBC_2.2.5+0x130>
    2781:	00 00 00 00 
    2785:	0f 11 43 10          	movups XMMWORD PTR [rbx+0x10],xmm0
    2789:	48 8b 5d f8          	mov    rbx,QWORD PTR [rbp-0x8]
    278d:	c9                   	leave
    278e:	c3                   	ret
    278f:	90                   	nop
    2790:	83 fe 01             	cmp    esi,0x1
    2793:	0f 8e bc 01 00 00    	jle    2955 <fopen@plt+0x1815>
    2799:	55                   	push   rbp
    279a:	48 89 e5             	mov    rbp,rsp
    279d:	41 57                	push   r15
    279f:	41 56                	push   r14
    27a1:	41 89 f6             	mov    r14d,esi
    27a4:	41 55                	push   r13
    27a6:	49 89 fd             	mov    r13,rdi
    27a9:	41 54                	push   r12
    27ab:	53                   	push   rbx
    27ac:	31 db                	xor    ebx,ebx
    27ae:	48 83 ec 08          	sub    rsp,0x8
    27b2:	eb 31                	jmp    27e5 <fopen@plt+0x16a5>
    27b4:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    27b8:	83 fe 02             	cmp    esi,0x2
    27bb:	0f 84 8f 00 00 00    	je     2850 <fopen@plt+0x1710>
    27c1:	83 fe 10             	cmp    esi,0x10
    27c4:	0f 84 de 00 00 00    	je     28a8 <fopen@plt+0x1768>
    27ca:	48 8d 3d cf 0a 00 00 	lea    rdi,[rip+0xacf]        # 32a0 <fopen@plt+0x2160>
    27d1:	31 c0                	xor    eax,eax
    27d3:	e8 d8 e8 ff ff       	call   10b0 <printf@plt>
    27d8:	41 8d 5c 1c 02       	lea    ebx,[r12+rbx*1+0x2]
    27dd:	8d 43 01             	lea    eax,[rbx+0x1]
    27e0:	44 39 f0             	cmp    eax,r14d
    27e3:	7d 4c                	jge    2831 <fopen@plt+0x16f1>
    27e5:	48 63 c3             	movsxd rax,ebx
    27e8:	8d 53 02             	lea    edx,[rbx+0x2]
    27eb:	45 0f b6 64 05 01    	movzx  r12d,BYTE PTR [r13+rax*1+0x1]
    27f1:	42 8d 0c 22          	lea    ecx,[rdx+r12*1]
    27f5:	44 39 f1             	cmp    ecx,r14d
    27f8:	7f 37                	jg     2831 <fopen@plt+0x16f1>
    27fa:	41 0f b6 74 05 00    	movzx  esi,BYTE PTR [r13+rax*1+0x0]
    2800:	49 8d 44 05 02       	lea    rax,[r13+rax*1+0x2]
    2805:	83 fe 01             	cmp    esi,0x1
    2808:	75 ae                	jne    27b8 <fopen@plt+0x1678>
    280a:	45 85 e4             	test   r12d,r12d
    280d:	74 09                	je     2818 <fopen@plt+0x16d8>
    280f:	80 38 0e             	cmp    BYTE PTR [rax],0xe
    2812:	0f 84 d8 00 00 00    	je     28f0 <fopen@plt+0x17b0>
    2818:	48 8d 3d 27 0a 00 00 	lea    rdi,[rip+0xa27]        # 3246 <fopen@plt+0x2106>
    281f:	41 8d 5c 1c 02       	lea    ebx,[r12+rbx*1+0x2]
    2824:	e8 47 e8 ff ff       	call   1070 <puts@plt>
    2829:	8d 43 01             	lea    eax,[rbx+0x1]
    282c:	44 39 f0             	cmp    eax,r14d
    282f:	7c b4                	jl     27e5 <fopen@plt+0x16a5>
    2831:	48 8b 3d e8 27 00 00 	mov    rdi,QWORD PTR [rip+0x27e8]        # 5020 <stdout@GLIBC_2.2.5>
    2838:	48 83 c4 08          	add    rsp,0x8
    283c:	5b                   	pop    rbx
    283d:	41 5c                	pop    r12
    283f:	41 5d                	pop    r13
    2841:	41 5e                	pop    r14
    2843:	41 5f                	pop    r15
    2845:	5d                   	pop    rbp
    2846:	e9 d5 e8 ff ff       	jmp    1120 <fflush@plt>
    284b:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    2850:	8b 0d 12 29 00 00    	mov    ecx,DWORD PTR [rip+0x2912]        # 5168 <stdin@GLIBC_2.2.5+0x138>
    2856:	85 c9                	test   ecx,ecx
    2858:	74 66                	je     28c0 <fopen@plt+0x1780>
    285a:	45 85 e4             	test   r12d,r12d
    285d:	0f 84 75 ff ff ff    	je     27d8 <fopen@plt+0x1698>
    2863:	44 0f b6 38          	movzx  r15d,BYTE PTR [rax]
    2867:	44 89 f6             	mov    esi,r14d
    286a:	29 d6                	sub    esi,edx
    286c:	43 8d 14 3f          	lea    edx,[r15+r15*1]
    2870:	39 d6                	cmp    esi,edx
    2872:	7e 64                	jle    28d8 <fopen@plt+0x1798>
    2874:	48 8b 3d f5 28 00 00 	mov    rdi,QWORD PTR [rip+0x28f5]        # 5170 <stdin@GLIBC_2.2.5+0x140>
    287b:	41 0f b6 d7          	movzx  edx,r15b
    287f:	48 8d 70 01          	lea    rsi,[rax+0x1]
    2883:	48 01 d2             	add    rdx,rdx
    2886:	e8 75 e8 ff ff       	call   1100 <memcpy@plt>
    288b:	44 89 fe             	mov    esi,r15d
    288e:	48 8d 3d d3 09 00 00 	lea    rdi,[rip+0x9d3]        # 3268 <fopen@plt+0x2128>
    2895:	31 c0                	xor    eax,eax
    2897:	e8 14 e8 ff ff       	call   10b0 <printf@plt>
    289c:	e9 37 ff ff ff       	jmp    27d8 <fopen@plt+0x1698>
    28a1:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    28a8:	48 8d 3d ec 09 00 00 	lea    rdi,[rip+0x9ec]        # 329b <fopen@plt+0x215b>
    28af:	e8 bc e7 ff ff       	call   1070 <puts@plt>
    28b4:	e9 1f ff ff ff       	jmp    27d8 <fopen@plt+0x1698>
    28b9:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    28c0:	48 8d 3d 90 09 00 00 	lea    rdi,[rip+0x990]        # 3257 <fopen@plt+0x2117>
    28c7:	e8 a4 e7 ff ff       	call   1070 <puts@plt>
    28cc:	e9 07 ff ff ff       	jmp    27d8 <fopen@plt+0x1698>
    28d1:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    28d8:	48 8d 3d a7 09 00 00 	lea    rdi,[rip+0x9a7]        # 3286 <fopen@plt+0x2146>
    28df:	e8 8c e7 ff ff       	call   1070 <puts@plt>
    28e4:	e9 ef fe ff ff       	jmp    27d8 <fopen@plt+0x1698>
    28e9:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    28f0:	be 0e 00 00 00       	mov    esi,0xe
    28f5:	31 c0                	xor    eax,eax
    28f7:	45 31 ff             	xor    r15d,r15d
    28fa:	c7 05 64 28 00 00 01 	mov    DWORD PTR [rip+0x2864],0x1        # 5168 <stdin@GLIBC_2.2.5+0x138>
    2901:	00 00 00 
    2904:	48 8d 3d 3d 08 00 00 	lea    rdi,[rip+0x83d]        # 3148 <fopen@plt+0x2008>
    290b:	e8 a0 e7 ff ff       	call   10b0 <printf@plt>
    2910:	48 8d 3d 1f 09 00 00 	lea    rdi,[rip+0x91f]        # 3236 <fopen@plt+0x20f6>
    2917:	31 c0                	xor    eax,eax
    2919:	e8 92 e7 ff ff       	call   10b0 <printf@plt>
    291e:	66 90                	xchg   ax,ax
    2920:	48 8b 15 49 28 00 00 	mov    rdx,QWORD PTR [rip+0x2849]        # 5170 <stdin@GLIBC_2.2.5+0x140>
    2927:	44 89 f8             	mov    eax,r15d
    292a:	48 8d 3d 10 09 00 00 	lea    rdi,[rip+0x910]        # 3241 <fopen@plt+0x2101>
    2931:	41 83 c7 01          	add    r15d,0x1
    2935:	0f b6 34 02          	movzx  esi,BYTE PTR [rdx+rax*1]
    2939:	31 c0                	xor    eax,eax
    293b:	e8 70 e7 ff ff       	call   10b0 <printf@plt>
    2940:	41 83 ff 10          	cmp    r15d,0x10
    2944:	75 da                	jne    2920 <fopen@plt+0x17e0>
    2946:	bf 0a 00 00 00       	mov    edi,0xa
    294b:	e8 00 e7 ff ff       	call   1050 <putchar@plt>
    2950:	e9 83 fe ff ff       	jmp    27d8 <fopen@plt+0x1698>
    2955:	48 8b 3d c4 26 00 00 	mov    rdi,QWORD PTR [rip+0x26c4]        # 5020 <stdout@GLIBC_2.2.5>
    295c:	e9 bf e7 ff ff       	jmp    1120 <fflush@plt>
    2961:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    2965:	66 66 2e 0f 1f 84 00 	data16 cs nop WORD PTR [rax+rax*1+0x0]
    296c:	00 00 00 00 
    2970:	8b 05 ea 27 00 00    	mov    eax,DWORD PTR [rip+0x27ea]        # 5160 <stdin@GLIBC_2.2.5+0x130>
    2976:	48 8d 0d 13 fd ff ff 	lea    rcx,[rip+0xfffffffffffffd13]        # 2690 <fopen@plt+0x1550>
    297d:	8d 50 01             	lea    edx,[rax+0x1]
    2980:	89 15 da 27 00 00    	mov    DWORD PTR [rip+0x27da],edx        # 5160 <stdin@GLIBC_2.2.5+0x130>
    2986:	48 8b 15 eb 27 00 00 	mov    rdx,QWORD PTR [rip+0x27eb]        # 5178 <stdin@GLIBC_2.2.5+0x148>
    298d:	48 8b 12             	mov    rdx,QWORD PTR [rdx]
    2990:	48 39 ca             	cmp    rdx,rcx
    2993:	75 0b                	jne    29a0 <fopen@plt+0x1860>
    2995:	83 c0 02             	add    eax,0x2
    2998:	89 05 c2 27 00 00    	mov    DWORD PTR [rip+0x27c2],eax        # 5160 <stdin@GLIBC_2.2.5+0x130>
    299e:	c3                   	ret
    299f:	90                   	nop
    29a0:	48 8d 3d b9 27 00 00 	lea    rdi,[rip+0x27b9]        # 5160 <stdin@GLIBC_2.2.5+0x130>
    29a7:	ff e2                	jmp    rdx
