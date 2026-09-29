
unpacked/countersign:     file format elf64-x86-64


Disassembly of section .text:

0000000000001140 <.text>:
    1140:	sub    rsp,0x2238
    1147:	mov    rdi,QWORD PTR [rip+0x4f32]        # 6080 <stdout@GLIBC_2.2.5>
    114e:	xor    esi,esi
    1150:	mov    edx,0x2
    1155:	mov    rcx,QWORD PTR fs:0x28
    115e:	mov    QWORD PTR [rsp+0x2208],rcx
    1166:	xor    ecx,ecx
    1168:	call   10f0 <setvbuf@plt>
    116d:	call   1fa0 <open@plt+0xea0>
    1172:	test   eax,eax
    1174:	jne    1615 <open@plt+0x515>
    117a:	lea    rdi,[rip+0x2f2f]        # 40b0 <open@plt+0x2fb0>
    1181:	mov    QWORD PTR [rsp+0x2220],r12
    1189:	mov    r12d,0x2
    118f:	mov    QWORD PTR [rsp+0x2210],rbx
    1197:	mov    QWORD PTR [rsp+0x2218],rbp
    119f:	mov    QWORD PTR [rsp+0x2228],r13
    11a7:	mov    QWORD PTR [rsp+0x2230],r14
    11af:	call   1060 <puts@plt>
    11b4:	lea    rdi,[rip+0x2f1d]        # 40d8 <open@plt+0x2fd8>
    11bb:	call   1060 <puts@plt>
    11c0:	mov    rdx,QWORD PTR [rip+0x4ec9]        # 6090 <stdin@GLIBC_2.2.5>
    11c7:	mov    esi,0x2000
    11cc:	lea    rdi,[rsp+0x200]
    11d4:	call   10d0 <fgets@plt>
    11d9:	test   rax,rax
    11dc:	je     144f <open@plt+0x34f>
    11e2:	cmp    WORD PTR [rsp+0x200],0x4547
    11ec:	je     1240 <open@plt+0x140>
    11ee:	cmp    DWORD PTR [rsp+0x200],0x434e4f4e
    11f9:	je     13e0 <open@plt+0x2e0>
    11ff:	cmp    DWORD PTR [rsp+0x200],0x544e494d
    120a:	je     1410 <open@plt+0x310>
    1210:	cmp    DWORD PTR [rsp+0x200],0x204e5552
    121b:	je     1496 <open@plt+0x396>
    1221:	cmp    DWORD PTR [rsp+0x200],0x54495551
    122c:	je     144d <open@plt+0x34d>
    1232:	lea    rdi,[rip+0x2e31]        # 406a <open@plt+0x2f6a>
    1239:	call   1060 <puts@plt>
    123e:	jmp    11c0 <open@plt+0xc0>
    1240:	cmp    BYTE PTR [rsp+0x202],0x54
    1248:	jne    11ee <open@plt+0xee>
    124a:	movzx  eax,BYTE PTR [rsp+0x203]
    1252:	cmp    al,0xd
    1254:	ja     11ee <open@plt+0xee>
    1256:	mov    edx,0x2401
    125b:	bt     rdx,rax
    125f:	jae    11ee <open@plt+0xee>
    1261:	movzx  edx,WORD PTR [rip+0x45070]        # 462d8 <stdin@GLIBC_2.2.5+0x40248>
    1268:	mov    eax,DWORD PTR [rip+0x4506a]        # 462d8 <stdin@GLIBC_2.2.5+0x40248>
    126e:	mov    DWORD PTR [rip+0x4e28],0x4e475343        # 60a0 <stdin@GLIBC_2.2.5+0x10>
    1278:	lea    rbp,[rip+0x4e21]        # 60a0 <stdin@GLIBC_2.2.5+0x10>
    127f:	mov    WORD PTR [rip+0x4e1d],r12w        # 60a4 <stdin@GLIBC_2.2.5+0x14>
    1287:	mov    WORD PTR [rip+0x4e18],dx        # 60a6 <stdin@GLIBC_2.2.5+0x16>
    128e:	movzx  edx,WORD PTR [rip+0x4503f]        # 462d4 <stdin@GLIBC_2.2.5+0x40244>
    1295:	mov    WORD PTR [rip+0x4e0c],dx        # 60a8 <stdin@GLIBC_2.2.5+0x18>
    129c:	mov    rdx,QWORD PTR [rip+0x75c3d]        # 76ee0 <stdin@GLIBC_2.2.5+0x70e50>
    12a3:	mov    QWORD PTR [rip+0x4e00],rdx        # 60aa <stdin@GLIBC_2.2.5+0x1a>
    12aa:	test   eax,eax
    12ac:	jle    162b <open@plt+0x52b>
    12b2:	mov    ebx,eax
    12b4:	lea    r13,[rip+0x4502d]        # 462e8 <stdin@GLIBC_2.2.5+0x40258>
    12bb:	lea    rdi,[rbp+0x12]
    12bf:	imul   rbx,rbx,0x30c
    12c6:	add    rbx,r13
    12c9:	nop    DWORD PTR [rax+0x0]
    12d0:	movzx  eax,WORD PTR [r13-0x8]
    12d5:	movzx  r14d,WORD PTR [r13-0x2]
    12da:	mov    rsi,r13
    12dd:	add    rdi,0x8
    12e1:	mov    WORD PTR [rdi-0x8],ax
    12e5:	movzx  eax,BYTE PTR [r13-0x6]
    12ea:	mov    rdx,r14
    12ed:	mov    WORD PTR [rdi-0x2],r14w
    12f2:	mov    BYTE PTR [rdi-0x6],al
    12f5:	movzx  eax,BYTE PTR [r13-0x5]
    12fa:	mov    BYTE PTR [rdi-0x5],al
    12fd:	movzx  eax,WORD PTR [r13-0x4]
    1302:	mov    WORD PTR [rdi-0x4],ax
    1306:	call   10e0 <memcpy@plt>
    130b:	movzx  esi,BYTE PTR [r13+0x200]
    1313:	lea    rcx,[rax+r14*1]
    1317:	mov    BYTE PTR [rcx],sil
    131a:	lea    rdi,[rcx+0x1]
    131e:	test   sil,sil
    1321:	je     1389 <open@plt+0x289>
    1323:	sub    esi,0x1
    1326:	lea    rax,[rcx+0x8]
    132a:	lea    rdx,[r13+0x20c]
    1331:	lea    r8,[rsi+rsi*2]
    1335:	lea    r9,[rsi+r8*4]
    1339:	lea    r8,[rcx+r9*1+0x15]
    133e:	xchg   ax,ax
    1340:	movzx  ecx,BYTE PTR [rdx-0x8]
    1344:	add    rax,0xd
    1348:	add    rdx,0x10
    134c:	mov    BYTE PTR [rax-0x14],cl
    134f:	movzx  ecx,WORD PTR [rdx-0x16]
    1353:	mov    BYTE PTR [rax-0x13],cl
    1356:	mov    BYTE PTR [rax-0x12],ch
    1359:	mov    ecx,DWORD PTR [rdx-0x14]
    135c:	mov    esi,ecx
    135e:	mov    BYTE PTR [rax-0x11],cl
    1361:	mov    BYTE PTR [rax-0x10],ch
    1364:	shr    ecx,0x18
    1367:	shr    esi,0x10
    136a:	mov    BYTE PTR [rax-0xe],cl
    136d:	mov    ecx,DWORD PTR [rdx-0x10]
    1370:	mov    BYTE PTR [rax-0xf],sil
    1374:	mov    DWORD PTR [rax-0xd],ecx
    1377:	movzx  ecx,WORD PTR [rdx-0xc]
    137b:	mov    WORD PTR [rax-0x9],cx
    137f:	cmp    r8,rax
    1382:	jne    1340 <open@plt+0x240>
    1384:	lea    rdi,[rdi+r9*1+0xd]
    1389:	add    r13,0x30c
    1390:	cmp    r13,rbx
    1393:	jne    12d0 <open@plt+0x1d0>
    1399:	sub    rdi,rbp
    139c:	test   edi,edi
    139e:	jle    13ca <open@plt+0x2ca>
    13a0:	lea    rbx,[rip+0x4cf9]        # 60a0 <stdin@GLIBC_2.2.5+0x10>
    13a7:	lea    eax,[rdi-0x1]
    13aa:	lea    rbp,[rbx+rax*1+0x1]
    13af:	nop
    13b0:	movzx  esi,BYTE PTR [rbx]
    13b3:	lea    rdi,[rip+0x2c77]        # 4031 <open@plt+0x2f31>
    13ba:	xor    eax,eax
    13bc:	add    rbx,0x1
    13c0:	call   1080 <printf@plt>
    13c5:	cmp    rbp,rbx
    13c8:	jne    13b0 <open@plt+0x2b0>
    13ca:	mov    edi,0xa
    13cf:	call   1040 <putchar@plt>
    13d4:	jmp    11c0 <open@plt+0xc0>
    13d9:	nop    DWORD PTR [rax+0x0]
    13e0:	cmp    BYTE PTR [rsp+0x204],0x45
    13e8:	jne    11ff <open@plt+0xff>
    13ee:	mov    rsi,QWORD PTR [rip+0x75aeb]        # 76ee0 <stdin@GLIBC_2.2.5+0x70e50>
    13f5:	lea    rdi,[rip+0x2c40]        # 403c <open@plt+0x2f3c>
    13fc:	xor    eax,eax
    13fe:	call   1080 <printf@plt>
    1403:	jmp    11c0 <open@plt+0xc0>
    1408:	nop    DWORD PTR [rax+rax*1+0x0]
    1410:	cmp    BYTE PTR [rsp+0x204],0x20
    1418:	jne    1210 <open@plt+0x110>
    141e:	lea    rdi,[rsp+0x205]
    1426:	lea    rsi,[rsp+0x100]
    142e:	call   1eb0 <open@plt+0xdb0>
    1433:	cmp    eax,0x10
    1436:	jbe    14be <open@plt+0x3be>
    143c:	lea    rdi,[rip+0x2c08]        # 404b <open@plt+0x2f4b>
    1443:	call   1060 <puts@plt>
    1448:	jmp    11c0 <open@plt+0xc0>
    144d:	xor    eax,eax
    144f:	mov    rbx,QWORD PTR [rsp+0x2210]
    1457:	mov    rbp,QWORD PTR [rsp+0x2218]
    145f:	mov    r12,QWORD PTR [rsp+0x2220]
    1467:	mov    r13,QWORD PTR [rsp+0x2228]
    146f:	mov    r14,QWORD PTR [rsp+0x2230]
    1477:	mov    rdx,QWORD PTR [rsp+0x2208]
    147f:	sub    rdx,QWORD PTR fs:0x28
    1488:	jne    1658 <open@plt+0x558>
    148e:	add    rsp,0x2238
    1495:	ret
    1496:	lea    rdi,[rsp+0x204]
    149e:	lea    rsi,[rsp+0x40]
    14a3:	call   1eb0 <open@plt+0xdb0>
    14a8:	cmp    eax,0x18
    14ab:	je     1519 <open@plt+0x419>
    14ad:	lea    rdi,[rip+0x2ba0]        # 4054 <open@plt+0x2f54>
    14b4:	call   1060 <puts@plt>
    14b9:	jmp    11c0 <open@plt+0xc0>
    14be:	mov    edx,eax
    14c0:	lea    rcx,[rsp+0x80]
    14c8:	lea    rsi,[rsp+0x100]
    14d0:	mov    edi,0x4d
    14d5:	call   1af0 <open@plt+0x9f0>
    14da:	lea    rbx,[rsp+0x80]
    14e2:	lea    rbp,[rsp+0x86]
    14ea:	nop    WORD PTR [rax+rax*1+0x0]
    14f0:	movzx  esi,BYTE PTR [rbx]
    14f3:	lea    rdi,[rip+0x2b37]        # 4031 <open@plt+0x2f31>
    14fa:	xor    eax,eax
    14fc:	add    rbx,0x1
    1500:	call   1080 <printf@plt>
    1505:	cmp    rbx,rbp
    1508:	jne    14f0 <open@plt+0x3f0>
    150a:	mov    edi,0xa
    150f:	call   1040 <putchar@plt>
    1514:	jmp    11c0 <open@plt+0xc0>
    1519:	xor    eax,eax
    151b:	mov    ecx,0x8
    1520:	lea    rdi,[rsp+0x20]
    1525:	movzx  esi,WORD PTR [rip+0x44da8]        # 462d4 <stdin@GLIBC_2.2.5+0x40244>
    152c:	rep stos DWORD PTR es:[rdi],eax
    152e:	lea    rbp,[rsp+0x80]
    1536:	mov    ecx,0x20
    153b:	mov    r13d,0x30d40
    1541:	mov    rdi,rbp
    1544:	lea    r14,[rip+0x44d95]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    154b:	rep stos DWORD PTR es:[rdi],eax
    154d:	xor    eax,eax
    154f:	mov    DWORD PTR [rsp+0x1c],eax
    1553:	mov    ecx,DWORD PTR [rip+0x44d7f]        # 462d8 <stdin@GLIBC_2.2.5+0x40248>
    1559:	test   ecx,ecx
    155b:	jle    15ea <open@plt+0x4ea>
    1561:	lea    rdx,[rip+0x44d78]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    1568:	xor    eax,eax
    156a:	jmp    158e <open@plt+0x48e>
    156c:	nop    WORD PTR [rax+rax*1+0x0]
    1575:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1580:	add    eax,0x1
    1583:	add    rdx,0x30c
    158a:	cmp    ecx,eax
    158c:	je     15ea <open@plt+0x4ea>
    158e:	cmp    si,WORD PTR [rdx]
    1591:	jne    1580 <open@plt+0x480>
    1593:	mov    edi,eax
    1595:	lea    r8,[rsp+0x1c]
    159a:	lea    rdx,[rsp+0x40]
    159f:	mov    rcx,rbp
    15a2:	imul   rdi,rdi,0x30c
    15a9:	lea    rsi,[rsp+0x20]
    15ae:	add    rdi,r14
    15b1:	mov    QWORD PTR [rsp+0x8],rdi
    15b6:	call   1810 <open@plt+0x710>
    15bb:	cmp    DWORD PTR [rsp+0x1c],0x0
    15c0:	mov    rdi,QWORD PTR [rsp+0x8]
    15c5:	jne    1635 <open@plt+0x535>
    15c7:	test   eax,eax
    15c9:	jne    15ea <open@plt+0x4ea>
    15cb:	cmp    BYTE PTR [rdi+0x208],0x0
    15d2:	je     15ea <open@plt+0x4ea>
    15d4:	lea    rsi,[rsp+0x20]
    15d9:	call   1d50 <open@plt+0xc50>
    15de:	mov    esi,eax
    15e0:	sub    r13d,0x1
    15e4:	jne    1553 <open@plt+0x453>
    15ea:	mov    DWORD PTR [rsp+0x100],0x696e6564
    15f5:	lea    rbx,[rsp+0x100]
    15fd:	mov    DWORD PTR [rsp+0x103],0x646569
    1608:	mov    rdi,rbx
    160b:	call   1060 <puts@plt>
    1610:	jmp    11c0 <open@plt+0xc0>
    1615:	lea    rdi,[rip+0x2a06]        # 4022 <open@plt+0x2f22>
    161c:	call   1060 <puts@plt>
    1621:	mov    eax,0x1
    1626:	jmp    1477 <open@plt+0x377>
    162b:	mov    edi,0x12
    1630:	jmp    13a0 <open@plt+0x2a0>
    1635:	lea    rbx,[rsp+0x100]
    163d:	mov    rcx,rbp
    1640:	mov    esi,0x100
    1645:	xor    eax,eax
    1647:	lea    rdx,[rip+0x2a14]        # 4062 <open@plt+0x2f62>
    164e:	mov    rdi,rbx
    1651:	call   1090 <snprintf@plt>
    1656:	jmp    1608 <open@plt+0x508>
    1658:	mov    QWORD PTR [rsp+0x2210],rbx
    1660:	mov    QWORD PTR [rsp+0x2218],rbp
    1668:	mov    QWORD PTR [rsp+0x2220],r12
    1670:	mov    QWORD PTR [rsp+0x2228],r13
    1678:	mov    QWORD PTR [rsp+0x2230],r14
    1680:	call   1070 <__stack_chk_fail@plt>
    1685:	cs nop WORD PTR [rax+rax*1+0x0]
    168f:	nop
    1690:	endbr64
    1694:	xor    ebp,ebp
    1696:	mov    r9,rdx
    1699:	pop    rsi
    169a:	mov    rdx,rsp
    169d:	and    rsp,0xfffffffffffffff0
    16a1:	push   rax
    16a2:	push   rsp
    16a3:	xor    r8d,r8d
    16a6:	xor    ecx,ecx
    16a8:	lea    rdi,[rip+0xfffffffffffffa91]        # 1140 <open@plt+0x40>
    16af:	call   QWORD PTR [rip+0x490b]        # 5fc0 <open@plt+0x4ec0>
    16b5:	hlt
    16b6:	cs nop WORD PTR [rax+rax*1+0x0]
    16c0:	lea    rdi,[rip+0x49b9]        # 6080 <stdout@GLIBC_2.2.5>
    16c7:	lea    rax,[rip+0x49b2]        # 6080 <stdout@GLIBC_2.2.5>
    16ce:	cmp    rax,rdi
    16d1:	je     16e8 <open@plt+0x5e8>
    16d3:	mov    rax,QWORD PTR [rip+0x48ee]        # 5fc8 <open@plt+0x4ec8>
    16da:	test   rax,rax
    16dd:	je     16e8 <open@plt+0x5e8>
    16df:	jmp    rax
    16e1:	nop    DWORD PTR [rax+0x0]
    16e8:	ret
    16e9:	nop    DWORD PTR [rax+0x0]
    16f0:	lea    rdi,[rip+0x4989]        # 6080 <stdout@GLIBC_2.2.5>
    16f7:	lea    rsi,[rip+0x4982]        # 6080 <stdout@GLIBC_2.2.5>
    16fe:	sub    rsi,rdi
    1701:	mov    rax,rsi
    1704:	shr    rsi,0x3f
    1708:	sar    rax,0x3
    170c:	add    rsi,rax
    170f:	sar    rsi,1
    1712:	je     1728 <open@plt+0x628>
    1714:	mov    rax,QWORD PTR [rip+0x48bd]        # 5fd8 <open@plt+0x4ed8>
    171b:	test   rax,rax
    171e:	je     1728 <open@plt+0x628>
    1720:	jmp    rax
    1722:	nop    WORD PTR [rax+rax*1+0x0]
    1728:	ret
    1729:	nop    DWORD PTR [rax+0x0]
    1730:	endbr64
    1734:	cmp    BYTE PTR [rip+0x495d],0x0        # 6098 <stdin@GLIBC_2.2.5+0x8>
    173b:	jne    1770 <open@plt+0x670>
    173d:	push   rbp
    173e:	cmp    QWORD PTR [rip+0x489a],0x0        # 5fe0 <open@plt+0x4ee0>
    1746:	mov    rbp,rsp
    1749:	je     1758 <open@plt+0x658>
    174b:	mov    rdi,QWORD PTR [rip+0x4926]        # 6078 <open@plt+0x4f78>
    1752:	call   QWORD PTR [rip+0x4888]        # 5fe0 <open@plt+0x4ee0>
    1758:	call   16c0 <open@plt+0x5c0>
    175d:	mov    BYTE PTR [rip+0x4934],0x1        # 6098 <stdin@GLIBC_2.2.5+0x8>
    1764:	pop    rbp
    1765:	ret
    1766:	cs nop WORD PTR [rax+rax*1+0x0]
    1770:	ret
    1771:	nop    DWORD PTR [rax+0x0]
    1775:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1780:	endbr64
    1784:	jmp    16f0 <open@plt+0x5f0>
    1789:	cs nop WORD PTR [rax+rax*1+0x0]
    1793:	cs nop WORD PTR [rax+rax*1+0x0]
    179d:	cs nop WORD PTR [rax+rax*1+0x0]
    17a7:	cs nop WORD PTR [rax+rax*1+0x0]
    17b1:	cs nop WORD PTR [rax+rax*1+0x0]
    17bb:	nop    DWORD PTR [rax+rax*1+0x0]
    17c0:	mov    r8d,edx
    17c3:	movzx  edx,WORD PTR [rdi+0x6]
    17c7:	mov    r9d,esi
    17ca:	movzx  esi,dx
    17cd:	mov    eax,edx
    17cf:	mov    BYTE PTR [rdi+rsi*1+0x8],r9b
    17d4:	lea    esi,[rdx+0x1]
    17d7:	add    eax,0x6
    17da:	mov    BYTE PTR [rdi+rsi*1+0x8],r8b
    17df:	lea    esi,[rdx+0x2]
    17e2:	mov    r8d,ecx
    17e5:	mov    BYTE PTR [rdi+rsi*1+0x8],cl
    17e9:	lea    esi,[rdx+0x3]
    17ec:	shr    r8d,0x10
    17f0:	mov    BYTE PTR [rdi+rsi*1+0x8],ch
    17f4:	lea    esi,[rdx+0x4]
    17f7:	shr    ecx,0x18
    17fa:	add    edx,0x5
    17fd:	mov    BYTE PTR [rdi+rsi*1+0x8],r8b
    1802:	mov    BYTE PTR [rdi+rdx*1+0x8],cl
    1806:	mov    WORD PTR [rdi+0x6],ax
    180a:	ret
    180b:	nop    DWORD PTR [rax+rax*1+0x0]
    1810:	cmp    WORD PTR [rdi+0x6],0x0
    1815:	je     1ae5 <open@plt+0x9e5>
    181b:	push   r12
    181d:	mov    r9,rdi
    1820:	mov    r12,rdx
    1823:	xor    eax,eax
    1825:	push   rbp
    1826:	lea    r11,[rip+0x283f]        # 406c <open@plt+0x2f6c>
    182d:	mov    rbp,r8
    1830:	mov    r8,rsi
    1833:	push   rbx
    1834:	mov    rbx,rcx
    1837:	sub    rsp,0x20
    183b:	nop    DWORD PTR [rax+rax*1+0x0]
    1840:	movsxd rdx,eax
    1843:	lea    r10d,[rax+0x1]
    1847:	cmp    BYTE PTR [r9+rdx*1+0x8],0xf
    184d:	ja     1877 <open@plt+0x777>
    184f:	movzx  edx,BYTE PTR [r9+rdx*1+0x8]
    1855:	movsxd rdx,DWORD PTR [r11+rdx*4]
    1859:	add    rdx,r11
    185c:	jmp    rdx
    185e:	xchg   ax,ax
    1860:	add    rsp,0x20
    1864:	mov    eax,0x1
    1869:	pop    rbx
    186a:	pop    rbp
    186b:	pop    r12
    186d:	ret
    186e:	xchg   ax,ax
    1870:	mov    DWORD PTR [rbp+0x0],0x1
    1877:	mov    eax,r10d
    187a:	nop    WORD PTR [rax+rax*1+0x0]
    1880:	movzx  edx,WORD PTR [r9+0x6]
    1885:	cmp    edx,eax
    1887:	jg     1840 <open@plt+0x740>
    1889:	add    rsp,0x20
    188d:	xor    eax,eax
    188f:	pop    rbx
    1890:	pop    rbp
    1891:	pop    r12
    1893:	ret
    1894:	nop    DWORD PTR [rax+0x0]
    1898:	lea    rdi,[rip+0x2771]        # 4010 <open@plt+0x2f10>
    189f:	mov    QWORD PTR [rsp+0x18],r8
    18a4:	mov    QWORD PTR [rsp+0x10],r9
    18a9:	mov    DWORD PTR [rsp+0xc],r10d
    18ae:	call   1030 <getenv@plt>
    18b3:	lea    rsi,[rip+0x274a]        # 4004 <open@plt+0x2f04>
    18ba:	pxor   xmm0,xmm0
    18be:	mov    rdi,rbx
    18c1:	test   rax,rax
    18c4:	movups XMMWORD PTR [rbx],xmm0
    18c7:	mov    edx,0x7f
    18cc:	cmovne rsi,rax
    18d0:	movups XMMWORD PTR [rbx+0x10],xmm0
    18d4:	movups XMMWORD PTR [rbx+0x20],xmm0
    18d8:	movups XMMWORD PTR [rbx+0x30],xmm0
    18dc:	movups XMMWORD PTR [rbx+0x40],xmm0
    18e0:	movups XMMWORD PTR [rbx+0x50],xmm0
    18e4:	movups XMMWORD PTR [rbx+0x60],xmm0
    18e8:	movups XMMWORD PTR [rbx+0x70],xmm0
    18ec:	call   1050 <strncpy@plt>
    18f1:	mov    r8,QWORD PTR [rsp+0x18]
    18f6:	mov    r9,QWORD PTR [rsp+0x10]
    18fb:	lea    r11,[rip+0x276a]        # 406c <open@plt+0x2f6c>
    1902:	mov    r10d,DWORD PTR [rsp+0xc]
    1907:	jmp    1877 <open@plt+0x777>
    190c:	nop    DWORD PTR [rax+0x0]
    1910:	lea    ecx,[rax+0x2]
    1913:	movsxd r10,r10d
    1916:	add    eax,0x3
    1919:	xor    esi,esi
    191b:	movsxd rcx,ecx
    191e:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    1924:	movzx  ecx,BYTE PTR [r9+rcx*1+0x8]
    192a:	cmp    cl,0x17
    192d:	ja     1934 <open@plt+0x834>
    192f:	movzx  esi,BYTE PTR [r12+rcx*1]
    1934:	mov    DWORD PTR [r8+rdx*4],esi
    1938:	jmp    1880 <open@plt+0x780>
    193d:	nop    DWORD PTR [rax]
    1940:	lea    edx,[rax+0x2]
    1943:	movsxd r10,r10d
    1946:	add    eax,0x6
    1949:	movsxd rdx,edx
    194c:	mov    ecx,DWORD PTR [r9+rdx*1+0x8]
    1951:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    1957:	and    DWORD PTR [r8+rdx*4],ecx
    195b:	jmp    1880 <open@plt+0x780>
    1960:	lea    edx,[rax+0x2]
    1963:	movsxd r10,r10d
    1966:	add    eax,0x6
    1969:	movsxd rdx,edx
    196c:	mov    ecx,DWORD PTR [r9+rdx*1+0x8]
    1971:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    1977:	add    DWORD PTR [r8+rdx*4],ecx
    197b:	jmp    1880 <open@plt+0x780>
    1980:	lea    edx,[rax+0x2]
    1983:	movsxd r10,r10d
    1986:	add    eax,0x3
    1989:	movsxd rdx,edx
    198c:	movzx  ecx,BYTE PTR [r9+rdx*1+0x8]
    1992:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    1998:	lea    rsi,[r8+rdx*4]
    199c:	xor    edx,edx
    199e:	cmp    cl,0x1f
    19a1:	ja     19a7 <open@plt+0x8a7>
    19a3:	mov    edx,DWORD PTR [rsi]
    19a5:	shr    edx,cl
    19a7:	mov    DWORD PTR [rsi],edx
    19a9:	jmp    1880 <open@plt+0x780>
    19ae:	xchg   ax,ax
    19b0:	lea    edx,[rax+0x2]
    19b3:	movsxd r10,r10d
    19b6:	add    eax,0x6
    19b9:	movsxd rdx,edx
    19bc:	mov    ecx,DWORD PTR [r9+rdx*1+0x8]
    19c1:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    19c7:	xor    DWORD PTR [r8+rdx*4],ecx
    19cb:	jmp    1880 <open@plt+0x780>
    19d0:	movsxd r10,r10d
    19d3:	lea    edx,[rax+0x2]
    19d6:	add    eax,0x3
    19d9:	movzx  esi,BYTE PTR [r9+r10*1+0x8]
    19df:	movsxd rdx,edx
    19e2:	movzx  ecx,BYTE PTR [r9+rdx*1+0x8]
    19e8:	rol    DWORD PTR [r8+rsi*4],cl
    19ec:	jmp    1880 <open@plt+0x780>
    19f1:	nop    DWORD PTR [rax+0x0]
    19f8:	lea    edx,[rax+0x2]
    19fb:	movsxd r10,r10d
    19fe:	add    eax,0x3
    1a01:	movsxd rdx,edx
    1a04:	movzx  ecx,BYTE PTR [r9+r10*1+0x8]
    1a0a:	movzx  edx,BYTE PTR [r9+rdx*1+0x8]
    1a10:	mov    edx,DWORD PTR [r8+rdx*4]
    1a14:	or     DWORD PTR [r8+rcx*4],edx
    1a18:	jmp    1880 <open@plt+0x780>
    1a1d:	nop    DWORD PTR [rax]
    1a20:	lea    edx,[rax+0x2]
    1a23:	movsxd r10,r10d
    1a26:	add    eax,0x3
    1a29:	movsxd rdx,edx
    1a2c:	movzx  ecx,BYTE PTR [r9+r10*1+0x8]
    1a32:	movzx  edx,BYTE PTR [r9+rdx*1+0x8]
    1a38:	mov    edx,DWORD PTR [r8+rdx*4]
    1a3c:	and    DWORD PTR [r8+rcx*4],edx
    1a40:	jmp    1880 <open@plt+0x780>
    1a45:	nop    DWORD PTR [rax]
    1a48:	lea    edx,[rax+0x2]
    1a4b:	movsxd r10,r10d
    1a4e:	add    eax,0x3
    1a51:	movsxd rdx,edx
    1a54:	movzx  ecx,BYTE PTR [r9+r10*1+0x8]
    1a5a:	movzx  edx,BYTE PTR [r9+rdx*1+0x8]
    1a60:	mov    edx,DWORD PTR [r8+rdx*4]
    1a64:	xor    DWORD PTR [r8+rcx*4],edx
    1a68:	jmp    1880 <open@plt+0x780>
    1a6d:	nop    DWORD PTR [rax]
    1a70:	lea    edx,[rax+0x2]
    1a73:	movsxd r10,r10d
    1a76:	add    eax,0x3
    1a79:	movsxd rdx,edx
    1a7c:	movzx  ecx,BYTE PTR [r9+r10*1+0x8]
    1a82:	movzx  edx,BYTE PTR [r9+rdx*1+0x8]
    1a88:	mov    edx,DWORD PTR [r8+rdx*4]
    1a8c:	add    DWORD PTR [r8+rcx*4],edx
    1a90:	jmp    1880 <open@plt+0x780>
    1a95:	nop    DWORD PTR [rax]
    1a98:	lea    edx,[rax+0x2]
    1a9b:	movsxd r10,r10d
    1a9e:	add    eax,0x6
    1aa1:	movsxd rdx,edx
    1aa4:	mov    ecx,DWORD PTR [r9+rdx*1+0x8]
    1aa9:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    1aaf:	mov    DWORD PTR [r8+rdx*4],ecx
    1ab3:	jmp    1880 <open@plt+0x780>
    1ab8:	nop    DWORD PTR [rax+rax*1+0x0]
    1ac0:	lea    edx,[rax+0x2]
    1ac3:	movsxd r10,r10d
    1ac6:	add    eax,0x3
    1ac9:	movsxd rdx,edx
    1acc:	movzx  edx,BYTE PTR [r9+rdx*1+0x8]
    1ad2:	mov    ecx,DWORD PTR [r8+rdx*4]
    1ad6:	movzx  edx,BYTE PTR [r9+r10*1+0x8]
    1adc:	mov    DWORD PTR [r8+rdx*4],ecx
    1ae0:	jmp    1880 <open@plt+0x780>
    1ae5:	xor    eax,eax
    1ae7:	ret
    1ae8:	nop    DWORD PTR [rax+rax*1+0x0]
    1af0:	push   r12
    1af2:	pxor   xmm0,xmm0
    1af6:	mov    r9,rcx
    1af9:	mov    ecx,edx
    1afb:	push   rbp
    1afc:	mov    r8,rdx
    1aff:	push   rbx
    1b00:	sub    rsp,0x30
    1b04:	mov    rax,QWORD PTR fs:0x28
    1b0d:	mov    QWORD PTR [rsp+0x28],rax
    1b12:	xor    eax,eax
    1b14:	movups XMMWORD PTR [rsp+0x1],xmm0
    1b19:	mov    BYTE PTR [rsp],dil
    1b1d:	movups XMMWORD PTR [rsp+0x10],xmm0
    1b22:	and    ecx,0x3f
    1b25:	je     1b38 <open@plt+0xa38>
    1b27:	mov    edx,eax
    1b29:	add    eax,0x1
    1b2c:	movzx  edi,BYTE PTR [rsi+rdx*1]
    1b30:	mov    BYTE PTR [rsp+rdx*1],dil
    1b34:	cmp    eax,ecx
    1b36:	jb     1b27 <open@plt+0xa27>
    1b38:	mov    rcx,QWORD PTR [rip+0x753b1]        # 76ef0 <stdin@GLIBC_2.2.5+0x70e60>
    1b3f:	mov    rdx,QWORD PTR [rip+0x753b2]        # 76ef8 <stdin@GLIBC_2.2.5+0x70e68>
    1b46:	mov    rbx,r8
    1b49:	movabs rsi,0x736f6d6570736575
    1b53:	movabs rdi,0x6c7967656e657261
    1b5d:	shl    rbx,0x38
    1b61:	movabs rax,0x646f72616e646f6d
    1b6b:	xor    rsi,rcx
    1b6e:	xor    rcx,rdi
    1b71:	xor    rax,rdx
    1b74:	mov    r12,rcx
    1b77:	movabs rcx,0x7465646279746573
    1b81:	xor    rdx,rcx
    1b84:	cmp    r8,0x7
    1b88:	jbe    1d42 <open@plt+0xc42>
    1b8e:	mov    r10d,0x8
    1b94:	lea    rbp,[rsp-0x8]
    1b99:	jmp    1bbf <open@plt+0xabf>
    1b9b:	nop    DWORD PTR [rax+rax*1+0x0]
    1ba0:	xor    ecx,ecx
    1ba2:	xor    rsi,r11
    1ba5:	cmp    r10,0x8
    1ba9:	mov    r10d,0x10
    1baf:	setne  cl
    1bb2:	lea    rcx,[rcx*8+0x10]
    1bba:	cmp    r8,rcx
    1bbd:	jb     1c10 <open@plt+0xb10>
    1bbf:	mov    r11,QWORD PTR [rbp+r10*1+0x0]
    1bc4:	mov    edi,0x2
    1bc9:	xor    rdx,r11
    1bcc:	add    rsi,rax
    1bcf:	rol    rax,0xd
    1bd3:	lea    rcx,[r12+rdx*1]
    1bd7:	xor    rax,rsi
    1bda:	rol    rdx,0x10
    1bde:	xor    rdx,rcx
    1be1:	rol    rsi,0x20
    1be5:	add    rcx,rax
    1be8:	rol    rax,0x11
    1bec:	add    rsi,rdx
    1bef:	rol    rdx,0x15
    1bf3:	xor    rax,rcx
    1bf6:	rol    rcx,0x20
    1bfa:	xor    rdx,rsi
    1bfd:	mov    r12,rcx
    1c00:	cmp    edi,0x1
    1c03:	je     1ba0 <open@plt+0xaa0>
    1c05:	mov    edi,0x1
    1c0a:	jmp    1bcc <open@plt+0xacc>
    1c0c:	nop    DWORD PTR [rax+0x0]
    1c10:	lea    rcx,[r8-0x8]
    1c14:	and    rcx,0xfffffffffffffff8
    1c18:	add    rcx,0x8
    1c1c:	mov    edi,ecx
    1c1e:	sub    r8d,edi
    1c21:	test   r8d,r8d
    1c24:	jle    1c5b <open@plt+0xb5b>
    1c26:	xor    edi,edi
    1c28:	lea    r11,[rsp+rcx*1]
    1c2c:	nop    WORD PTR [rax+rax*1+0x0]
    1c35:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1c40:	movzx  r10d,BYTE PTR [r11+rdi*1]
    1c45:	lea    ecx,[rdi*8+0x0]
    1c4c:	add    rdi,0x1
    1c50:	shl    r10,cl
    1c53:	or     rbx,r10
    1c56:	cmp    r8,rdi
    1c59:	jne    1c40 <open@plt+0xb40>
    1c5b:	xor    rdx,rbx
    1c5e:	mov    edi,0x2
    1c63:	add    rsi,rax
    1c66:	rol    rax,0xd
    1c6a:	lea    rcx,[r12+rdx*1]
    1c6e:	xor    rax,rsi
    1c71:	rol    rdx,0x10
    1c75:	xor    rdx,rcx
    1c78:	rol    rsi,0x20
    1c7c:	add    rcx,rax
    1c7f:	rol    rax,0x11
    1c83:	add    rsi,rdx
    1c86:	rol    rdx,0x15
    1c8a:	xor    rax,rcx
    1c8d:	rol    rcx,0x20
    1c91:	xor    rdx,rsi
    1c94:	mov    r12,rcx
    1c97:	cmp    edi,0x1
    1c9a:	jne    1d38 <open@plt+0xc38>
    1ca0:	xor    rsi,rbx
    1ca3:	xor    cl,0xff
    1ca6:	mov    r8d,0x4
    1cac:	add    rsi,rax
    1caf:	add    rcx,rdx
    1cb2:	rol    rax,0xd
    1cb6:	rol    rdx,0x10
    1cba:	xor    rax,rsi
    1cbd:	rol    rsi,0x20
    1cc1:	xor    rdx,rcx
    1cc4:	add    rcx,rax
    1cc7:	rol    rax,0x11
    1ccb:	mov    rdi,rdx
    1cce:	add    rsi,rdx
    1cd1:	xor    rax,rcx
    1cd4:	rol    rcx,0x20
    1cd8:	rol    rdi,0x15
    1cdc:	mov    rdx,rsi
    1cdf:	xor    rdx,rdi
    1ce2:	sub    r8d,0x1
    1ce6:	jne    1cac <open@plt+0xbac>
    1ce8:	xor    rax,rcx
    1ceb:	xor    edx,edx
    1ced:	xor    rax,rdi
    1cf0:	nop    DWORD PTR [rax+rax*1+0x0]
    1cf5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1d00:	lea    ecx,[rdx*8+0x0]
    1d07:	mov    rbx,rax
    1d0a:	shr    rbx,cl
    1d0d:	mov    BYTE PTR [r9+rdx*1],bl
    1d11:	add    rdx,0x1
    1d15:	cmp    rdx,0x6
    1d19:	jne    1d00 <open@plt+0xc00>
    1d1b:	mov    rax,QWORD PTR [rsp+0x28]
    1d20:	sub    rax,QWORD PTR fs:0x28
    1d29:	jne    1d4b <open@plt+0xc4b>
    1d2b:	add    rsp,0x30
    1d2f:	pop    rbx
    1d30:	pop    rbp
    1d31:	pop    r12
    1d33:	ret
    1d34:	nop    DWORD PTR [rax+0x0]
    1d38:	mov    edi,0x1
    1d3d:	jmp    1c63 <open@plt+0xb63>
    1d42:	xor    edi,edi
    1d44:	xor    ecx,ecx
    1d46:	jmp    1c1e <open@plt+0xb1e>
    1d4b:	call   1070 <__stack_chk_fail@plt>
    1d50:	sub    rsp,0x48
    1d54:	mov    QWORD PTR [rsp+0x28],rbp
    1d59:	mov    QWORD PTR [rsp+0x30],r12
    1d5e:	mov    QWORD PTR [rsp+0x40],r14
    1d63:	movzx  ebp,BYTE PTR [rdi+0x2]
    1d67:	mov    r14,QWORD PTR fs:0x28
    1d70:	mov    QWORD PTR [rsp+0x18],r14
    1d75:	mov    r14,rdi
    1d78:	cmp    bpl,0xff
    1d7c:	je     1d8d <open@plt+0xc8d>
    1d7e:	mov    edx,DWORD PTR [rsi+rbp*4]
    1d81:	movzx  eax,BYTE PTR [r14+0x3]
    1d86:	bt     edx,eax
    1d89:	setb   bpl
    1d8d:	movzx  eax,BYTE PTR [r14+0x208]
    1d95:	test   al,al
    1d97:	je     1e9a <open@plt+0xd9a>
    1d9d:	sub    eax,0x1
    1da0:	mov    QWORD PTR [rsp+0x20],rbx
    1da5:	lea    rbx,[r14+0x214]
    1dac:	shl    rax,0x4
    1db0:	mov    QWORD PTR [rsp+0x38],r13
    1db5:	lea    r13,[r14+rax*1+0x224]
    1dbd:	jmp    1dcd <open@plt+0xccd>
    1dbf:	nop
    1dc0:	add    rbx,0x10
    1dc4:	cmp    r13,rbx
    1dc7:	je     1e90 <open@plt+0xd90>
    1dcd:	cmp    BYTE PTR [rbx-0x8],bpl
    1dd1:	jne    1dc0 <open@plt+0xcc0>
    1dd3:	movzx  edx,WORD PTR [r14]
    1dd7:	movzx  r12d,WORD PTR [rbx-0x6]
    1ddc:	lea    rsi,[rsp+0xc]
    1de1:	mov    edi,0x45
    1de6:	mov    ecx,DWORD PTR [rbx-0x4]
    1de9:	mov    BYTE PTR [rsp+0x10],bpl
    1dee:	movzx  eax,dh
    1df1:	shl    eax,0x10
    1df4:	mov    DWORD PTR [rsp+0x11],ecx
    1df8:	lea    rcx,[rsp+0x6]
    1dfd:	or     eax,edx
    1dff:	movzx  edx,r12w
    1e03:	movd   xmm0,eax
    1e07:	mov    eax,r12d
    1e0a:	movzx  eax,ah
    1e0d:	movdqa xmm2,xmm0
    1e11:	shl    eax,0x10
    1e14:	or     eax,edx
    1e16:	mov    edx,0x9
    1e1b:	movd   xmm1,eax
    1e1f:	punpcklbw xmm2,xmm1
    1e23:	punpcklbw xmm0,xmm1
    1e27:	pshufd xmm2,xmm2,0x41
    1e2c:	punpcklbw xmm0,xmm2
    1e30:	movd   DWORD PTR [rsp+0xc],xmm0
    1e36:	call   1af0 <open@plt+0x9f0>
    1e3b:	mov    eax,DWORD PTR [rbx]
    1e3d:	cmp    DWORD PTR [rsp+0x6],eax
    1e41:	jne    1dc0 <open@plt+0xcc0>
    1e47:	movzx  eax,WORD PTR [rbx+0x4]
    1e4b:	cmp    WORD PTR [rsp+0xa],ax
    1e50:	jne    1dc0 <open@plt+0xcc0>
    1e56:	mov    rbx,QWORD PTR [rsp+0x20]
    1e5b:	mov    r13,QWORD PTR [rsp+0x38]
    1e60:	mov    rax,QWORD PTR [rsp+0x18]
    1e65:	sub    rax,QWORD PTR fs:0x28
    1e6e:	jne    1ea1 <open@plt+0xda1>
    1e70:	mov    eax,r12d
    1e73:	mov    rbp,QWORD PTR [rsp+0x28]
    1e78:	mov    r12,QWORD PTR [rsp+0x30]
    1e7d:	mov    r14,QWORD PTR [rsp+0x40]
    1e82:	add    rsp,0x48
    1e86:	ret
    1e87:	nop    WORD PTR [rax+rax*1+0x0]
    1e90:	mov    rbx,QWORD PTR [rsp+0x20]
    1e95:	mov    r13,QWORD PTR [rsp+0x38]
    1e9a:	movzx  r12d,WORD PTR [r14+0x4]
    1e9f:	jmp    1e60 <open@plt+0xd60>
    1ea1:	mov    QWORD PTR [rsp+0x20],rbx
    1ea6:	mov    QWORD PTR [rsp+0x38],r13
    1eab:	call   1070 <__stack_chk_fail@plt>
    1eb0:	movzx  edx,BYTE PTR [rdi]
    1eb3:	mov    r9,rsi
    1eb6:	mov    r8d,0x400009
    1ebc:	xor    esi,esi
    1ebe:	test   dl,dl
    1ec0:	je     1ef4 <open@plt+0xdf4>
    1ec2:	nop    DWORD PTR [rax]
    1ec5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1ed0:	movsx  eax,BYTE PTR [rdi+0x1]
    1ed4:	test   al,al
    1ed6:	je     1ef4 <open@plt+0xdf4>
    1ed8:	lea    ecx,[rdx-0xa]
    1edb:	cmp    cl,0x16
    1ede:	ja     1f10 <open@plt+0xe10>
    1ee0:	bt     r8,rcx
    1ee4:	jae    1f00 <open@plt+0xe00>
    1ee6:	add    rdi,0x1
    1eea:	mov    edx,eax
    1eec:	movsx  eax,BYTE PTR [rdi+0x1]
    1ef0:	test   al,al
    1ef2:	jne    1ed8 <open@plt+0xdd8>
    1ef4:	mov    eax,esi
    1ef6:	ret
    1ef7:	nop    WORD PTR [rax+rax*1+0x0]
    1f00:	mov    esi,0xffffffff
    1f05:	mov    eax,esi
    1f07:	ret
    1f08:	nop    DWORD PTR [rax+rax*1+0x0]
    1f10:	movsx  ecx,dl
    1f13:	lea    edx,[rcx-0x30]
    1f16:	cmp    edx,0x9
    1f19:	ja     1f60 <open@plt+0xe60>
    1f1b:	lea    ecx,[rax-0x30]
    1f1e:	cmp    ecx,0x9
    1f21:	jbe    1f36 <open@plt+0xe36>
    1f23:	lea    ecx,[rax-0x61]
    1f26:	cmp    ecx,0x5
    1f29:	jbe    1f70 <open@plt+0xe70>
    1f2b:	lea    ecx,[rax-0x41]
    1f2e:	cmp    ecx,0x5
    1f31:	ja     1f00 <open@plt+0xe00>
    1f33:	lea    ecx,[rax-0x37]
    1f36:	cmp    esi,0x3f
    1f39:	jg     1f00 <open@plt+0xe00>
    1f3b:	shl    edx,0x4
    1f3e:	mov    eax,esi
    1f40:	or     edx,ecx
    1f42:	mov    BYTE PTR [r9+rax*1],dl
    1f46:	movzx  edx,BYTE PTR [rdi+0x2]
    1f4a:	test   dl,dl
    1f4c:	je     1f78 <open@plt+0xe78>
    1f4e:	add    rdi,0x2
    1f52:	add    esi,0x1
    1f55:	jmp    1ed0 <open@plt+0xdd0>
    1f5a:	nop    WORD PTR [rax+rax*1+0x0]
    1f60:	lea    edx,[rcx-0x61]
    1f63:	cmp    edx,0x5
    1f66:	ja     1f80 <open@plt+0xe80>
    1f68:	lea    edx,[rcx-0x57]
    1f6b:	jmp    1f1b <open@plt+0xe1b>
    1f6d:	nop    DWORD PTR [rax]
    1f70:	lea    ecx,[rax-0x57]
    1f73:	jmp    1f36 <open@plt+0xe36>
    1f75:	nop    DWORD PTR [rax]
    1f78:	add    esi,0x1
    1f7b:	jmp    1ef4 <open@plt+0xdf4>
    1f80:	lea    edx,[rcx-0x41]
    1f83:	cmp    edx,0x5
    1f86:	ja     1f00 <open@plt+0xe00>
    1f8c:	lea    edx,[rcx-0x37]
    1f8f:	jmp    1f1b <open@plt+0xe1b>
    1f91:	nop    DWORD PTR [rax+0x0]
    1f95:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    1fa0:	push   r15
    1fa2:	xor    esi,esi
    1fa4:	lea    rdi,[rip+0x206a]        # 4015 <open@plt+0x2f15>
    1fab:	push   r14
    1fad:	push   r13
    1faf:	push   r12
    1fb1:	push   rbp
    1fb2:	push   rbx
    1fb3:	sub    rsp,0x10488
    1fba:	mov    rax,QWORD PTR fs:0x28
    1fc3:	mov    QWORD PTR [rsp+0x10478],rax
    1fcb:	xor    eax,eax
    1fcd:	call   1100 <open@plt>
    1fd2:	test   eax,eax
    1fd4:	js     3669 <open@plt+0x2569>
    1fda:	mov    edx,0x10
    1fdf:	lea    rsi,[rip+0x74f0a]        # 76ef0 <stdin@GLIBC_2.2.5+0x70e60>
    1fe6:	mov    edi,eax
    1fe8:	mov    ebx,eax
    1fea:	call   10c0 <read@plt>
    1fef:	cmp    rax,0x10
    1ff3:	jne    3662 <open@plt+0x2562>
    1ff9:	lea    rsi,[rsp+0x3c0]
    2001:	mov    edx,0x8
    2006:	mov    edi,ebx
    2008:	call   10c0 <read@plt>
    200d:	cmp    rax,0x8
    2011:	jne    3662 <open@plt+0x2562>
    2017:	lea    rsi,[rsp+0x3c8]
    201f:	mov    edx,0x8
    2024:	mov    edi,ebx
    2026:	call   10c0 <read@plt>
    202b:	cmp    rax,0x8
    202f:	jne    3662 <open@plt+0x2562>
    2035:	mov    edi,ebx
    2037:	call   10b0 <close@plt>
    203c:	mov    rax,QWORD PTR [rsp+0x3c0]
    2044:	xor    esi,esi
    2046:	movabs rdx,0xa5a5a5a5a5a5a5a5
    2050:	lea    rdi,[rsp+0x470]
    2058:	mov    rbp,QWORD PTR [rsp+0x3c8]
    2060:	mov    QWORD PTR [rip+0x74e79],rax        # 76ee0 <stdin@GLIBC_2.2.5+0x70e50>
    2067:	xor    rax,rdx
    206a:	mov    edx,0x10000
    206f:	mov    r14,rax
    2072:	call   10a0 <memset@plt>
    2077:	lea    r9,[rip+0x44092]        # 46110 <stdin@GLIBC_2.2.5+0x40080>
    207e:	movabs rdi,0x2545f4914f6cdd1d
    2088:	movabs rsi,0xff51afd7ed558ccd
    2092:	movabs rcx,0xc4ceb9fe1a85ec53
    209c:	lea    r8,[r9-0x50]
    20a0:	cs nop WORD PTR [rax+rax*1+0x0]
    20aa:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    20b5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    20c0:	mov    rbx,rbp
    20c3:	add    rbp,rdi
    20c6:	mov    rdx,rbp
    20c9:	shr    rdx,0x21
    20cd:	xor    rdx,rbp
    20d0:	imul   rdx,rsi
    20d4:	mov    rax,rdx
    20d7:	shr    rax,0x21
    20db:	xor    rax,rdx
    20de:	imul   rax,rcx
    20e2:	mov    rdx,rax
    20e5:	shr    rdx,0x21
    20e9:	xor    rax,rdx
    20ec:	test   ax,ax
    20ef:	je     20c0 <open@plt+0xfc0>
    20f1:	movzx  edx,ax
    20f4:	cmp    BYTE PTR [rsp+rdx*1+0x470],0x0
    20fc:	jne    20c0 <open@plt+0xfc0>
    20fe:	mov    WORD PTR [r8],ax
    2102:	add    r8,0x2
    2106:	mov    BYTE PTR [rsp+rdx*1+0x470],0x1
    210e:	cmp    r9,r8
    2111:	jne    20c0 <open@plt+0xfc0>
    2113:	movzx  eax,WORD PTR [rip+0x43ff2]        # 4610c <stdin@GLIBC_2.2.5+0x4007c>
    211a:	mov    r12d,DWORD PTR [rip+0x441b7]        # 462d8 <stdin@GLIBC_2.2.5+0x40248>
    2121:	xor    esi,esi
    2123:	mov    QWORD PTR [rip+0x44196],rbp        # 462c0 <stdin@GLIBC_2.2.5+0x40230>
    212a:	movzx  r15d,WORD PTR [rip+0x43f8e]        # 460c0 <stdin@GLIBC_2.2.5+0x40030>
    2132:	mov    edx,0x30c
    2137:	mov    WORD PTR [rsp+0x84],ax
    213f:	mov    WORD PTR [rip+0x4418c],ax        # 462d2 <stdin@GLIBC_2.2.5+0x40242>
    2146:	movzx  eax,WORD PTR [rip+0x43fc1]        # 4610e <stdin@GLIBC_2.2.5+0x4007e>
    214d:	mov    WORD PTR [rsp+0x86],r15w
    2156:	mov    WORD PTR [rsp+0x82],ax
    215e:	mov    WORD PTR [rip+0x4416b],ax        # 462d0 <stdin@GLIBC_2.2.5+0x40240>
    2165:	lea    eax,[r12+0x1]
    216a:	mov    DWORD PTR [rsp+0x10],eax
    216e:	movsxd rax,r12d
    2171:	imul   r13,rax,0x30c
    2178:	lea    rax,[rip+0x44161]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    217f:	mov    WORD PTR [rip+0x4414d],r15w        # 462d4 <stdin@GLIBC_2.2.5+0x40244>
    2187:	lea    rbp,[rax+r13*1]
    218b:	mov    rdi,rbp
    218e:	call   10a0 <memset@plt>
    2193:	lea    rax,[rip+0x44146]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    219a:	mov    edi,0xff
    219f:	xor    r10d,r10d
    21a2:	mov    WORD PTR [rbp+0x0],r15w
    21a7:	mov    WORD PTR [rax+r13*1+0x2],di
    21ad:	movzx  edx,r10b
    21b1:	mov    esi,0x1
    21b6:	mov    rdi,rbp
    21b9:	xor    ecx,ecx
    21bb:	call   17c0 <open@plt+0x6c0>
    21c0:	movzx  edi,WORD PTR [rbp+0x6]
    21c4:	mov    r11d,r10d
    21c7:	xor    edx,edx
    21c9:	lea    esi,[r10*4+0x0]
    21d1:	mov    eax,edi
    21d3:	movzx  ecx,ax
    21d6:	mov    BYTE PTR [rbp+rcx*1+0x8],0xc
    21db:	lea    ecx,[rax+0x1]
    21de:	movzx  ecx,cx
    21e1:	mov    BYTE PTR [rbp+rcx*1+0x8],0x6
    21e6:	lea    ecx,[rax+0x2]
    21e9:	movzx  ecx,cx
    21ec:	mov    BYTE PTR [rbp+rcx*1+0x8],sil
    21f1:	lea    ecx,[rax+0x3]
    21f4:	add    esi,0x1
    21f7:	movzx  ecx,cx
    21fa:	mov    BYTE PTR [rbp+rcx*1+0x8],0x7
    21ff:	lea    ecx,[rax+0x4]
    2202:	movzx  ecx,cx
    2205:	mov    BYTE PTR [rbp+rcx*1+0x8],0x6
    220a:	lea    ecx,[rax+0x5]
    220d:	movzx  ecx,cx
    2210:	mov    BYTE PTR [rbp+rcx*1+0x8],dl
    2214:	lea    ecx,[rax+0x6]
    2217:	add    edx,0x8
    221a:	movzx  ecx,cx
    221d:	mov    BYTE PTR [rbp+rcx*1+0x8],0x6
    2222:	lea    ecx,[rax+0x7]
    2225:	movzx  ecx,cx
    2228:	mov    BYTE PTR [rbp+rcx*1+0x8],r11b
    222d:	lea    ecx,[rax+0x8]
    2230:	add    eax,0x9
    2233:	movzx  ecx,cx
    2236:	mov    BYTE PTR [rbp+rcx*1+0x8],0x6
    223b:	cmp    dl,0x20
    223e:	jne    21d3 <open@plt+0x10d3>
    2240:	add    edi,0x24
    2243:	add    r10d,0x1
    2247:	mov    WORD PTR [rbp+0x6],di
    224b:	cmp    r10d,0x6
    224f:	jne    21ad <open@plt+0x10ad>
    2255:	movzx  eax,WORD PTR [rip+0x43e66]        # 460c2 <stdin@GLIBC_2.2.5+0x40032>
    225c:	lea    rdi,[rip+0x4407d]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2263:	mov    BYTE PTR [rbp+0x20c],0xff
    226a:	lea    r8,[rip+0x43e51]        # 460c2 <stdin@GLIBC_2.2.5+0x40032>
    2271:	mov    BYTE PTR [rbp+0x208],0x1
    2278:	movabs r15,0xbf58476d1ce4e5b9
    2282:	movabs r10,0x94d049bb133111eb
    228c:	mov    WORD PTR [rbp+0x20e],ax
    2293:	movsxd rax,DWORD PTR [rsp+0x10]
    2298:	movabs rbp,0x2e2ac13ef8e8d8d2
    22a2:	add    rbp,r14
    22a5:	lea    r14,[rdi+r13*1]
    22a9:	mov    QWORD PTR [rsp+0x88],rbx
    22b1:	mov    QWORD PTR [rsp+0x20],rax
    22b6:	mov    r13,rax
    22b9:	imul   rax,rax,0x30c
    22c0:	lea    r11,[rdi+rax*1]
    22c4:	lea    eax,[r12+0x2]
    22c9:	cdqe
    22cb:	mov    rbx,r11
    22ce:	imul   rax,rax,0x30c
    22d5:	lea    r9,[rdi+rax*1]
    22d9:	lea    eax,[r12+0x3]
    22de:	cdqe
    22e0:	imul   rax,rax,0x30c
    22e7:	lea    r12,[rdi+rax*1]
    22eb:	jmp    23a0 <open@plt+0x12a0>
    22f0:	movzx  eax,WORD PTR [r8+0x6]
    22f5:	mov    r9,QWORD PTR [rsp+0x38]
    22fa:	mov    BYTE PTR [rbx+0x20c],0x0
    2301:	add    r8,0x6
    2305:	movzx  r11d,WORD PTR [rsp+0x8]
    230b:	mov    BYTE PTR [rbx+0x21c],0x1
    2312:	add    r12,0x924
    2319:	add    rbx,0x924
    2320:	mov    WORD PTR [rbx-0x706],r10w
    2328:	add    r9,0x924
    232f:	mov    WORD PTR [rbx-0x716],r11w
    2337:	mov    BYTE PTR [rbx-0x71c],0x2
    233e:	mov    WORD PTR [r9-0x716],ax
    2346:	mov    BYTE PTR [r9-0x718],0xff
    234e:	mov    BYTE PTR [r9-0x71c],0x1
    2356:	mov    WORD PTR [r12-0x716],ax
    235f:	movabs rax,0x2e2ac13ef8e8d8d2
    2369:	mov    BYTE PTR [r12-0x718],0xff
    2372:	add    rbp,rax
    2375:	lea    rax,[rip+0x43d8e]        # 4610a <stdin@GLIBC_2.2.5+0x4007a>
    237c:	mov    BYTE PTR [r12-0x71c],0x1
    2385:	cmp    rax,r8
    2388:	je     3678 <open@plt+0x2578>
    238e:	movabs r10,0x94d049bb133111eb
    2398:	movsxd rax,r13d
    239b:	mov    QWORD PTR [rsp+0x20],rax
    23a0:	movzx  eax,WORD PTR [r8]
    23a4:	movzx  r11d,WORD PTR [r8+0x2]
    23a9:	mov    QWORD PTR [rsp+0x70],r9
    23ae:	movabs rdi,0x700cb87a8661a343
    23b8:	lea    rdx,[rbp+rdi*1+0x0]
    23bd:	mov    QWORD PTR [rsp+0x68],r8
    23c2:	movabs rdi,0xe44323405ac1f58
    23cc:	mov    WORD PTR [rsp+0x28],ax
    23d1:	movzx  eax,WORD PTR [r8+0x4]
    23d6:	mov    WORD PTR [rsp+0x8],r11w
    23dc:	mov    WORD PTR [rsp+0x18],ax
    23e1:	mov    rax,rdx
    23e4:	shr    rax,0x1e
    23e8:	mov    DWORD PTR [rsp+0x7c],r13d
    23ed:	xor    rax,rdx
    23f0:	imul   rax,r15
    23f4:	mov    rdx,rax
    23f7:	shr    rdx,0x1b
    23fb:	xor    rax,rdx
    23fe:	lea    rdx,[rbp+rdi*1+0x0]
    2403:	imul   rax,r10
    2407:	mov    rdi,rdx
    240a:	shr    rdi,0x1e
    240e:	mov    QWORD PTR [rsp+0x50],rax
    2413:	mov    rax,rdi
    2416:	xor    rax,rdx
    2419:	imul   rax,r15
    241d:	mov    rdx,rax
    2420:	shr    rdx,0x1b
    2424:	xor    rax,rdx
    2427:	movabs rdx,0xac7babed84f69b6d
    2431:	add    rdx,rbp
    2434:	mov    rdi,rax
    2437:	mov    rcx,rdx
    243a:	imul   rdi,r10
    243e:	shr    rcx,0x1e
    2442:	mov    rax,rcx
    2445:	xor    rax,rdx
    2448:	mov    QWORD PTR [rsp+0x48],rdi
    244d:	imul   rax,r15
    2451:	mov    rdx,rax
    2454:	shr    rdx,0x1b
    2458:	xor    rax,rdx
    245b:	movabs rdx,0x4ab325a704411782
    2465:	add    rdx,rbp
    2468:	mov    rcx,rax
    246b:	mov    rsi,rdx
    246e:	imul   rcx,r10
    2472:	shr    rsi,0x1e
    2476:	mov    rax,rsi
    2479:	xor    rax,rdx
    247c:	mov    QWORD PTR [rsp+0x40],rcx
    2481:	imul   rax,r15
    2485:	mov    rdx,rax
    2488:	shr    rdx,0x1b
    248c:	xor    rax,rdx
    248f:	movabs rdx,0xe8ea9f60838b9397
    2499:	add    rdx,rbp
    249c:	mov    rsi,rax
    249f:	mov    r9,rdx
    24a2:	imul   rsi,r10
    24a6:	shr    r9,0x1e
    24aa:	mov    rax,r9
    24ad:	xor    rax,rdx
    24b0:	mov    QWORD PTR [rsp+0x30],rsi
    24b5:	imul   rax,r15
    24b9:	mov    rdx,rax
    24bc:	shr    rdx,0x1b
    24c0:	mov    r11,rdx
    24c3:	movabs rdx,0x8722191a02d60fac
    24cd:	xor    r11,rax
    24d0:	imul   r11,r10
    24d4:	add    rdx,rbp
    24d7:	xor    esi,esi
    24d9:	mov    r9,rdx
    24dc:	shr    r9,0x1e
    24e0:	mov    rax,r9
    24e3:	lea    r9d,[r13+0x1]
    24e7:	mov    QWORD PTR [rsp+0x60],r11
    24ec:	xor    rax,rdx
    24ef:	mov    DWORD PTR [rsp+0x38],r9d
    24f4:	lea    r9,[r14+0x30c]
    24fb:	mov    edx,0x30c
    2500:	imul   rax,r15
    2504:	mov    rdi,r9
    2507:	mov    QWORD PTR [rsp+0x10],r9
    250c:	mov    rcx,rax
    250f:	shr    rcx,0x1b
    2513:	xor    rcx,rax
    2516:	imul   rcx,r10
    251a:	mov    QWORD PTR [rsp+0x58],rcx
    251f:	call   10a0 <memset@plt>
    2524:	mov    r11,QWORD PTR [rsp+0x60]
    2529:	movzx  edx,WORD PTR [rsp+0x28]
    252e:	movabs r10,0x94d049bb133111eb
    2538:	imul   rsi,QWORD PTR [rsp+0x20],0x30c
    2541:	mov    rcx,QWORD PTR [rsp+0x58]
    2546:	mov    WORD PTR [rbx],dx
    2549:	mov    rdx,r11
    254c:	shr    rdx,0x1f
    2550:	mov    rax,rdx
    2553:	mov    rdx,rcx
    2556:	xor    rax,r11
    2559:	shr    rdx,0x1f
    255d:	and    eax,0x3
    2560:	mov    BYTE PTR [rbx+0x2],al
    2563:	mov    rax,rdx
    2566:	lea    rdx,[rip+0x43d73]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    256d:	xor    rax,rcx
    2570:	add    rsi,rdx
    2573:	and    eax,0x1f
    2576:	mov    BYTE PTR [rbx+0x3],al
    2579:	movzx  eax,WORD PTR [rbx+0x6]
    257d:	mov    BYTE PTR [rax+rsi*1+0x8],0x3
    2582:	mov    rcx,rax
    2585:	lea    eax,[rax+0x1]
    2588:	movzx  eax,ax
    258b:	lea    r11d,[rcx+0x5]
    258f:	mov    BYTE PTR [rsi+rax*1+0x8],0x0
    2594:	lea    eax,[rcx+0x2]
    2597:	movzx  r11d,r11w
    259b:	movzx  eax,ax
    259e:	mov    BYTE PTR [rsi+rax*1+0x8],0x1
    25a3:	lea    eax,[rcx+0x3]
    25a6:	movzx  eax,ax
    25a9:	mov    BYTE PTR [rsi+rax*1+0x8],0x7
    25ae:	lea    eax,[rcx+0x4]
    25b1:	movzx  eax,ax
    25b4:	mov    BYTE PTR [rsi+rax*1+0x8],0x0
    25b9:	mov    rax,QWORD PTR [rsp+0x50]
    25be:	mov    rdi,rax
    25c1:	shr    rdi,0x1f
    25c5:	xor    rdi,rax
    25c8:	movabs rax,0x8888888888888889
    25d2:	mul    rdi
    25d5:	shr    rdx,0x4
    25d9:	imul   rax,rdx,0x1e
    25dd:	sub    rdi,rax
    25e0:	lea    eax,[rdi+0x1]
    25e3:	mov    BYTE PTR [rsi+r11*1+0x8],al
    25e8:	lea    eax,[rcx+0x6]
    25eb:	lea    r11d,[rcx+0xe]
    25ef:	movzx  eax,ax
    25f2:	movzx  r11d,r11w
    25f6:	mov    BYTE PTR [rsi+rax*1+0x8],0x4
    25fb:	lea    eax,[rcx+0x7]
    25fe:	movzx  eax,ax
    2601:	mov    BYTE PTR [rsi+rax*1+0x8],0x2
    2606:	lea    eax,[rcx+0x8]
    2609:	movzx  eax,ax
    260c:	mov    BYTE PTR [rsi+rax*1+0x8],0x0
    2611:	lea    eax,[rcx+0x9]
    2614:	movzx  eax,ax
    2617:	mov    BYTE PTR [rsi+rax*1+0x8],0x3
    261c:	lea    eax,[rcx+0xa]
    261f:	movzx  eax,ax
    2622:	mov    BYTE PTR [rsi+rax*1+0x8],0x3
    2627:	lea    eax,[rcx+0xb]
    262a:	movzx  eax,ax
    262d:	mov    BYTE PTR [rsi+rax*1+0x8],0x2
    2632:	lea    eax,[rcx+0xc]
    2635:	movzx  eax,ax
    2638:	mov    BYTE PTR [rsi+rax*1+0x8],0x7
    263d:	lea    eax,[rcx+0xd]
    2640:	movzx  eax,ax
    2643:	mov    BYTE PTR [rsi+rax*1+0x8],0x3
    2648:	mov    rax,QWORD PTR [rsp+0x48]
    264d:	mov    rdi,rax
    2650:	shr    rdi,0x1f
    2654:	xor    rdi,rax
    2657:	movabs rax,0x8888888888888889
    2661:	mul    rdi
    2664:	shr    rdx,0x4
    2668:	imul   rax,rdx,0x1e
    266c:	sub    rdi,rax
    266f:	lea    eax,[rdi+0x1]
    2672:	mov    rdi,QWORD PTR [rsp+0x10]
    2677:	mov    BYTE PTR [rsi+r11*1+0x8],al
    267c:	lea    eax,[rcx+0xf]
    267f:	movzx  eax,ax
    2682:	mov    BYTE PTR [rsi+rax*1+0x8],0x4
    2687:	lea    eax,[rcx+0x10]
    268a:	movzx  eax,ax
    268d:	mov    BYTE PTR [rsi+rax*1+0x8],0x1
    2692:	lea    eax,[rcx+0x12]
    2695:	mov    WORD PTR [rbx+0x6],ax
    2699:	lea    eax,[rcx+0x11]
    269c:	mov    rcx,QWORD PTR [rsp+0x40]
    26a1:	movzx  eax,ax
    26a4:	mov    BYTE PTR [rsi+rax*1+0x8],0x3
    26a9:	shr    rcx,0x1f
    26ad:	mov    esi,0x9
    26b2:	xor    ecx,DWORD PTR [rsp+0x40]
    26b6:	xor    edx,edx
    26b8:	call   17c0 <open@plt+0x6c0>
    26bd:	mov    rcx,QWORD PTR [rsp+0x30]
    26c2:	mov    edx,0x2
    26c7:	mov    esi,0xa
    26cc:	shr    rcx,0x1f
    26d0:	xor    ecx,DWORD PTR [rsp+0x30]
    26d4:	call   17c0 <open@plt+0x6c0>
    26d9:	mov    QWORD PTR [rip+0x43be8],rbp        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    26e0:	movabs rdx,0x255992d382208bc1
    26ea:	add    rdx,rbp
    26ed:	mov    rax,rdx
    26f0:	shr    rax,0x1e
    26f4:	xor    rax,rdx
    26f7:	movabs rdx,0xc3910c8d016b07d6
    2701:	imul   rax,r15
    2705:	add    rdx,rbp
    2708:	mov    rdi,rax
    270b:	shr    rdi,0x1b
    270f:	xor    rax,rdi
    2712:	mov    rdi,rdx
    2715:	imul   rax,r10
    2719:	shr    rdi,0x1e
    271d:	mov    QWORD PTR [rsp+0x30],rax
    2722:	mov    rax,rdi
    2725:	xor    rax,rdx
    2728:	movabs rdx,0x61c8864680b583eb
    2732:	imul   rax,r15
    2736:	add    rdx,rbp
    2739:	mov    rcx,rdx
    273c:	shr    rcx,0x1e
    2740:	mov    rdi,rax
    2743:	shr    rdi,0x1b
    2747:	xor    rax,rdi
    274a:	mov    rdi,rax
    274d:	mov    rax,rcx
    2750:	xor    rax,rdx
    2753:	imul   rdi,r10
    2757:	mov    edx,0x30c
    275c:	imul   rax,r15
    2760:	mov    QWORD PTR [rsp+0x28],rdi
    2765:	lea    rdi,[r14+0x618]
    276c:	mov    rcx,rax
    276f:	shr    rcx,0x1b
    2773:	mov    r11,rcx
    2776:	mov    rcx,rbp
    2779:	shr    rcx,0x1e
    277d:	xor    r11,rax
    2780:	mov    rax,rcx
    2783:	imul   r11,r10
    2787:	xor    rax,rbp
    278a:	imul   rax,r15
    278e:	mov    QWORD PTR [rsp+0x50],r11
    2793:	mov    rcx,rax
    2796:	shr    rcx,0x1b
    279a:	xor    rax,rcx
    279d:	mov    rcx,rax
    27a0:	imul   rcx,r10
    27a4:	xor    esi,esi
    27a6:	mov    QWORD PTR [rsp+0x20],rcx
    27ab:	lea    ecx,[r13+0x2]
    27af:	mov    DWORD PTR [rsp+0x10],ecx
    27b3:	call   10a0 <memset@plt>
    27b8:	mov    r9,QWORD PTR [rsp+0x70]
    27bd:	movzx  r11d,WORD PTR [rsp+0x8]
    27c3:	mov    esi,0xff
    27c8:	mov    rdi,rax
    27cb:	mov    edx,0x4
    27d0:	mov    QWORD PTR [rsp+0x40],r14
    27d5:	add    r14,0x924
    27dc:	mov    WORD PTR [r9],r11w
    27e0:	mov    r11,QWORD PTR [rsp+0x50]
    27e5:	mov    WORD PTR [r14-0x30a],si
    27ed:	mov    esi,0xa
    27f2:	mov    rcx,r11
    27f5:	mov    QWORD PTR [rsp+0x48],r9
    27fa:	shr    rcx,0x1f
    27fe:	xor    ecx,r11d
    2801:	call   17c0 <open@plt+0x6c0>
    2806:	movsxd r11,DWORD PTR [rsp+0x38]
    280b:	mov    r9,QWORD PTR [rsp+0x48]
    2810:	mov    rdi,r14
    2813:	lea    r8,[rip+0x43ac6]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    281a:	mov    DWORD PTR [rsp+0x48],r13d
    281f:	add    r13d,0x3
    2823:	imul   r11,r11,0x30c
    282a:	movzx  edx,WORD PTR [r9+0x6]
    282f:	mov    QWORD PTR [rsp+0x38],r9
    2834:	mov    DWORD PTR [rip+0x43a9d],r13d        # 462d8 <stdin@GLIBC_2.2.5+0x40248>
    283b:	mov    rax,rdx
    283e:	add    r11,r8
    2841:	mov    BYTE PTR [rdx+r11*1+0x8],0x3
    2847:	lea    edx,[rdx+0x1]
    284a:	movzx  edx,dx
    284d:	mov    BYTE PTR [r11+rdx*1+0x8],0x5
    2853:	lea    edx,[rax+0x2]
    2856:	movzx  edx,dx
    2859:	mov    BYTE PTR [r11+rdx*1+0x8],0x4
    285f:	lea    edx,[rax+0x3]
    2862:	movzx  edx,dx
    2865:	mov    BYTE PTR [r11+rdx*1+0x8],0x7
    286b:	lea    edx,[rax+0x4]
    286e:	movzx  edx,dx
    2871:	mov    BYTE PTR [r11+rdx*1+0x8],0x5
    2877:	lea    edx,[rax+0x6]
    287a:	add    eax,0x5
    287d:	movzx  ecx,ax
    2880:	mov    rax,QWORD PTR [rsp+0x30]
    2885:	mov    WORD PTR [r9+0x6],dx
    288a:	mov    QWORD PTR [rsp+0x30],r11
    288f:	mov    rsi,rax
    2892:	shr    rsi,0x1f
    2896:	xor    rsi,rax
    2899:	movabs rax,0x8888888888888889
    28a3:	mul    rsi
    28a6:	shr    rdx,0x4
    28aa:	imul   rax,rdx,0x1e
    28ae:	mov    edx,0x30c
    28b3:	sub    rsi,rax
    28b6:	lea    eax,[rsi+0x1]
    28b9:	xor    esi,esi
    28bb:	mov    BYTE PTR [r11+rcx*1+0x8],al
    28c0:	call   10a0 <memset@plt>
    28c5:	mov    rsi,QWORD PTR [rsp+0x20]
    28ca:	movzx  r10d,WORD PTR [rsp+0x18]
    28d0:	mov    rdi,r14
    28d3:	mov    r9,QWORD PTR [rsp+0x40]
    28d8:	mov    edx,0xff
    28dd:	mov    WORD PTR [r12],r10w
    28e2:	mov    rcx,rsi
    28e5:	mov    WORD PTR [r9+0x926],dx
    28ed:	shr    rcx,0x1f
    28f1:	mov    edx,0x4
    28f6:	xor    ecx,esi
    28f8:	mov    esi,0xa
    28fd:	call   17c0 <open@plt+0x6c0>
    2902:	movsxd rcx,DWORD PTR [rsp+0x10]
    2907:	movzx  edx,WORD PTR [r12+0x6]
    290d:	lea    r8,[rip+0x439cc]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2914:	imul   rcx,rcx,0x30c
    291b:	mov    rax,rdx
    291e:	add    rcx,r8
    2921:	mov    r8,QWORD PTR [rsp+0x68]
    2926:	mov    BYTE PTR [rdx+rcx*1+0x8],0x3
    292b:	lea    edx,[rdx+0x1]
    292e:	movzx  edx,dx
    2931:	mov    BYTE PTR [rcx+rdx*1+0x8],0x5
    2936:	lea    edx,[rax+0x2]
    2939:	movzx  edx,dx
    293c:	mov    BYTE PTR [rcx+rdx*1+0x8],0x4
    2941:	lea    edx,[rax+0x3]
    2944:	movzx  edx,dx
    2947:	mov    BYTE PTR [rcx+rdx*1+0x8],0x7
    294c:	lea    edx,[rax+0x4]
    294f:	movzx  edx,dx
    2952:	mov    BYTE PTR [rcx+rdx*1+0x8],0x5
    2957:	lea    edx,[rax+0x6]
    295a:	add    eax,0x5
    295d:	movzx  esi,ax
    2960:	mov    rax,QWORD PTR [rsp+0x28]
    2965:	mov    WORD PTR [r12+0x6],dx
    296b:	mov    rdi,rax
    296e:	shr    rdi,0x1f
    2972:	xor    rdi,rax
    2975:	movabs rax,0x8888888888888889
    297f:	mul    rdi
    2982:	shr    rdx,0x4
    2986:	imul   rax,rdx,0x1e
    298a:	sub    rdi,rax
    298d:	lea    eax,[rdi+0x1]
    2990:	mov    BYTE PTR [rcx+rsi*1+0x8],al
    2994:	lea    rax,[rip+0x43769]        # 46104 <stdin@GLIBC_2.2.5+0x40074>
    299b:	cmp    rax,r8
    299e:	jne    22f0 <open@plt+0x11f0>
    29a4:	movsxd rax,DWORD PTR [rsp+0x7c]
    29a9:	lea    rdi,[rip+0x43930]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    29b0:	mov    r12,QWORD PTR [rsp+0x30]
    29b5:	mov    DWORD PTR [rsp+0x10],r13d
    29ba:	movzx  r14d,WORD PTR [rip+0x43748]        # 4610a <stdin@GLIBC_2.2.5+0x4007a>
    29c2:	mov    rbx,QWORD PTR [rsp+0x88]
    29ca:	imul   rax,rax,0x30c
    29d1:	add    rax,rdi
    29d4:	movzx  edi,WORD PTR [rsp+0x8]
    29d9:	mov    BYTE PTR [rax+0x20c],0x0
    29e0:	mov    WORD PTR [rax+0x20e],di
    29e7:	movzx  edi,WORD PTR [rsp+0x18]
    29ec:	mov    BYTE PTR [rax+0x208],0x2
    29f3:	mov    BYTE PTR [r12+0x20c],0xff
    29fc:	mov    WORD PTR [r12+0x20e],r14w
    2a05:	mov    BYTE PTR [r12+0x208],0x1
    2a0e:	mov    BYTE PTR [rax+0x21c],0x1
    2a15:	mov    WORD PTR [rax+0x21e],di
    2a1c:	mov    BYTE PTR [rcx+0x20c],0xff
    2a23:	mov    WORD PTR [rcx+0x20e],r14w
    2a2b:	mov    BYTE PTR [rcx+0x208],0x1
    2a32:	mov    eax,DWORD PTR [rsp+0x10]
    2a36:	test   eax,eax
    2a38:	jle    2b69 <open@plt+0x1a69>
    2a3e:	mov    edx,eax
    2a40:	lea    r12,[rip+0x43aad]        # 464f4 <stdin@GLIBC_2.2.5+0x40464>
    2a47:	mov    WORD PTR [rsp+0x18],r14w
    2a4d:	movabs rbp,0x9e3779b97f4a7c15
    2a57:	imul   rdx,rdx,0x30c
    2a5e:	mov    QWORD PTR [rsp+0x20],rbx
    2a63:	mov    r15,r12
    2a66:	movabs r13,0xbf58476d1ce4e5b9
    2a70:	lea    rax,[rdx+r12*1]
    2a74:	mov    QWORD PTR [rsp+0x8],rax
    2a79:	movzx  eax,WORD PTR [rsp+0x82]
    2a81:	mov    WORD PTR [r15-0x210],ax
    2a89:	cmp    BYTE PTR [r15-0xc],0x0
    2a8e:	je     2b4c <open@plt+0x1a4c>
    2a94:	mov    r12,QWORD PTR [rip+0x4382d]        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    2a9b:	mov    r14,r15
    2a9e:	xor    ebx,ebx
    2aa0:	add    r12,rbp
    2aa3:	xchg   ax,ax
    2aa5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2ab0:	mov    rdx,r12
    2ab3:	movzx  ecx,WORD PTR [r14-0x6]
    2ab8:	add    ebx,0x1
    2abb:	movabs rdi,0x94d049bb133111eb
    2ac5:	shr    rdx,0x1e
    2ac9:	movzx  esi,WORD PTR [r15-0x214]
    2ad1:	mov    QWORD PTR [rip+0x437f0],r12        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    2ad8:	xor    rdx,r12
    2adb:	mov    WORD PTR [rsp+0x3f2],cx
    2ae3:	mov    rcx,r14
    2ae6:	add    r12,rbp
    2ae9:	imul   rdx,r13
    2aed:	mov    WORD PTR [rsp+0x3f0],si
    2af5:	add    r14,0x10
    2af9:	lea    rsi,[rsp+0x3f0]
    2b01:	mov    rax,rdx
    2b04:	shr    rax,0x1b
    2b08:	xor    rax,rdx
    2b0b:	imul   rax,rdi
    2b0f:	mov    edi,0x45
    2b14:	mov    rdx,rax
    2b17:	shr    rdx,0x1f
    2b1b:	xor    rax,rdx
    2b1e:	movzx  edx,BYTE PTR [r14-0x18]
    2b23:	mov    DWORD PTR [r14-0x14],eax
    2b27:	mov    BYTE PTR [rsp+0x3f4],dl
    2b2e:	mov    edx,0x9
    2b33:	mov    DWORD PTR [rsp+0x3f5],eax
    2b3a:	call   1af0 <open@plt+0x9f0>
    2b3f:	movzx  eax,BYTE PTR [r15-0xc]
    2b44:	cmp    eax,ebx
    2b46:	jg     2ab0 <open@plt+0x19b0>
    2b4c:	add    r15,0x30c
    2b53:	cmp    QWORD PTR [rsp+0x8],r15
    2b58:	jne    2a79 <open@plt+0x1979>
    2b5e:	movzx  r14d,WORD PTR [rsp+0x18]
    2b64:	mov    rbx,QWORD PTR [rsp+0x20]
    2b69:	lea    rcx,[rsp+0x3d0]
    2b71:	movabs rdx,0x4a8be9229ed9ba3a
    2b7b:	lea    r9,[rsp+0x3e8]
    2b83:	movabs r8,0xff51afd7ed558ccd
    2b8d:	movabs rdi,0xc4ceb9fe1a85ec53
    2b97:	add    rdx,rbx
    2b9a:	movabs rsi,0x2545f4914f6cdd1d
    2ba4:	nop    WORD PTR [rax+rax*1+0x0]
    2baa:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2bb5:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    2bc0:	mov    r10,rdx
    2bc3:	add    rcx,0x1
    2bc7:	shr    r10,0x21
    2bcb:	xor    r10,rdx
    2bce:	add    rdx,rsi
    2bd1:	imul   r10,r8
    2bd5:	mov    rax,r10
    2bd8:	shr    rax,0x21
    2bdc:	xor    rax,r10
    2bdf:	imul   rax,rdi
    2be3:	mov    r10,rax
    2be6:	shr    r10,0x21
    2bea:	xor    rax,r10
    2bed:	mov    BYTE PTR [rcx-0x1],al
    2bf0:	cmp    r9,rcx
    2bf3:	jne    2bc0 <open@plt+0x1ac0>
    2bf5:	movabs rax,0xa3d4e230c1a197d5
    2bff:	pxor   xmm0,xmm0
    2c03:	add    rbx,rax
    2c06:	movaps XMMWORD PTR [rsp+0x1b0],xmm0
    2c0e:	mov    QWORD PTR [rip+0x436ab],rbx        # 462c0 <stdin@GLIBC_2.2.5+0x40230>
    2c15:	movaps XMMWORD PTR [rsp+0x1c0],xmm0
    2c1d:	cmp    WORD PTR [rsp+0x86],r14w
    2c26:	je     2cd6 <open@plt+0x1bd6>
    2c2c:	mov    edx,DWORD PTR [rsp+0x10]
    2c30:	mov    r12d,DWORD PTR [rsp+0x10]
    2c35:	mov    ebx,0x30d40
    2c3a:	movzx  ecx,WORD PTR [rsp+0x86]
    2c42:	test   edx,edx
    2c44:	jle    2cf5 <open@plt+0x1bf5>
    2c4a:	lea    rdx,[rip+0x4368f]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2c51:	xor    eax,eax
    2c53:	jmp    2c68 <open@plt+0x1b68>
    2c55:	add    eax,0x1
    2c58:	add    rdx,0x30c
    2c5f:	cmp    r12d,eax
    2c62:	je     2cf5 <open@plt+0x1bf5>
    2c68:	cmp    WORD PTR [rdx],cx
    2c6b:	jne    2c55 <open@plt+0x1b55>
    2c6d:	mov    ebp,eax
    2c6f:	lea    rax,[rip+0x4366a]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2c76:	lea    rcx,[rsp+0x3f0]
    2c7e:	imul   rbp,rbp,0x30c
    2c85:	lea    r8,[rsp+0x9c]
    2c8d:	lea    rdx,[rsp+0x3d0]
    2c95:	lea    rsi,[rsp+0x1b0]
    2c9d:	add    rbp,rax
    2ca0:	mov    rdi,rbp
    2ca3:	call   1810 <open@plt+0x710>
    2ca8:	test   eax,eax
    2caa:	jne    2cf5 <open@plt+0x1bf5>
    2cac:	cmp    BYTE PTR [rbp+0x208],0x0
    2cb3:	je     2cf5 <open@plt+0x1bf5>
    2cb5:	lea    rsi,[rsp+0x1b0]
    2cbd:	mov    rdi,rbp
    2cc0:	call   1d50 <open@plt+0xc50>
    2cc5:	mov    ecx,eax
    2cc7:	sub    ebx,0x1
    2cca:	je     2cf5 <open@plt+0x1bf5>
    2ccc:	cmp    ax,r14w
    2cd0:	jne    2c4a <open@plt+0x1b4a>
    2cd6:	mov    rax,QWORD PTR [rsp+0x1c0]
    2cde:	movdqa xmm0,XMMWORD PTR [rsp+0x1b0]
    2ce7:	mov    QWORD PTR [rip+0x433c2],rax        # 460b0 <stdin@GLIBC_2.2.5+0x40020>
    2cee:	movaps XMMWORD PTR [rip+0x433ab],xmm0        # 460a0 <stdin@GLIBC_2.2.5+0x40010>
    2cf5:	movsxd rbx,DWORD PTR [rsp+0x10]
    2cfa:	lea    rdi,[rip+0x435df]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2d01:	mov    edx,0x30c
    2d06:	xor    esi,esi
    2d08:	mov    r15,rdi
    2d0b:	mov    r12d,DWORD PTR [rsp+0x48]
    2d10:	imul   rbx,rbx,0x30c
    2d17:	lea    ebp,[r12+0x4]
    2d1c:	movsxd rbp,ebp
    2d1f:	add    rdi,rbx
    2d22:	imul   rbp,rbp,0x30c
    2d29:	call   10a0 <memset@plt>
    2d2e:	xor    esi,esi
    2d30:	movzx  r13d,WORD PTR [rsp+0x82]
    2d39:	mov    r10,rax
    2d3c:	movzx  eax,WORD PTR [rsp+0x84]
    2d44:	lea    rdi,[r15+rbp*1]
    2d48:	mov    QWORD PTR [rsp+0x18],r10
    2d4d:	mov    WORD PTR [r10],ax
    2d51:	mov    eax,0xff
    2d56:	mov    WORD PTR [rbx+r15*1+0x2],ax
    2d5c:	movzx  edx,WORD PTR [r10+0x6]
    2d61:	lea    ebx,[r12+0x5]
    2d66:	add    r12d,0x6
    2d6a:	mov    WORD PTR [r10+0x4],r13w
    2d6f:	mov    BYTE PTR [r10+rdx*1+0x8],0xd
    2d75:	mov    rax,rdx
    2d78:	lea    edx,[rdx+0x1]
    2d7b:	movzx  edx,dx
    2d7e:	mov    BYTE PTR [r10+0x208],0x0
    2d86:	mov    BYTE PTR [r10+rdx*1+0x8],0xe
    2d8c:	lea    edx,[rax+0x3]
    2d8f:	add    eax,0x2
    2d92:	mov    WORD PTR [r10+0x6],dx
    2d97:	movzx  eax,ax
    2d9a:	mov    edx,0x30c
    2d9f:	mov    BYTE PTR [r10+rax*1+0x8],0xf
    2da5:	call   10a0 <memset@plt>
    2daa:	xor    esi,esi
    2dac:	mov    DWORD PTR [rip+0x43525],r12d        # 462d8 <stdin@GLIBC_2.2.5+0x40248>
    2db3:	mov    r11,rax
    2db6:	mov    WORD PTR [rax],r13w
    2dba:	mov    eax,0xff
    2dbf:	mov    WORD PTR [rbp+r15*1+0x2],ax
    2dc5:	movzx  eax,WORD PTR [r11+0x6]
    2dca:	mov    WORD PTR [r11+0x4],r13w
    2dcf:	mov    r13,r15
    2dd2:	lea    r15,[rbp+r15*1+0x30c]
    2dda:	lea    edx,[rax+0x1]
    2ddd:	mov    rdi,r15
    2de0:	mov    BYTE PTR [r11+rax*1+0x8],0xf
    2de6:	mov    WORD PTR [r11+0x6],dx
    2deb:	mov    edx,0x30c
    2df0:	mov    BYTE PTR [r11+0x208],0x0
    2df8:	mov    QWORD PTR [rsp+0x10],r11
    2dfd:	call   10a0 <memset@plt>
    2e02:	movsxd rax,ebx
    2e05:	mov    r11,QWORD PTR [rsp+0x10]
    2e0a:	mov    r10,QWORD PTR [rsp+0x18]
    2e0f:	imul   rbx,rax,0x30c
    2e16:	mov    QWORD PTR [rsp+0x8],rax
    2e1b:	mov    eax,0x6
    2e20:	mov    WORD PTR [r13+rbx*1+0x0],r14w
    2e26:	lea    r14,[rip+0x43273]        # 460a0 <stdin@GLIBC_2.2.5+0x40010>
    2e2d:	mov    WORD PTR [rbx+r13*1+0x2],ax
    2e33:	xor    r13d,r13d
    2e36:	lea    rax,[rip+0x434a3]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2e3d:	mov    ecx,DWORD PTR [r14+r13*4]
    2e41:	mov    esi,0xa
    2e46:	mov    rdi,r15
    2e49:	lea    rbp,[rax+rbx*1]
    2e4d:	movzx  edx,WORD PTR [rbp+0x6]
    2e51:	mov    BYTE PTR [rbp+rdx*1+0x8],0x2
    2e56:	mov    rax,rdx
    2e59:	lea    edx,[rdx+0x1]
    2e5c:	movzx  edx,dx
    2e5f:	mov    BYTE PTR [rbp+rdx*1+0x8],0x7
    2e64:	lea    edx,[rax+0x3]
    2e67:	add    eax,0x2
    2e6a:	movzx  eax,ax
    2e6d:	mov    WORD PTR [rbp+0x6],dx
    2e71:	mov    edx,0x7
    2e76:	mov    BYTE PTR [rbp+rax*1+0x8],r13b
    2e7b:	call   17c0 <open@plt+0x6c0>
    2e80:	movzx  ecx,WORD PTR [rbp+0x6]
    2e84:	movzx  eax,cx
    2e87:	test   r13,r13
    2e8a:	je     30ce <open@plt+0x1fce>
    2e90:	mov    BYTE PTR [rbp+rax*1+0x8],0x6
    2e95:	lea    eax,[rcx+0x1]
    2e98:	lea    edx,[rcx+0x3]
    2e9b:	add    r13,0x1
    2e9f:	movzx  eax,ax
    2ea2:	mov    WORD PTR [rbp+0x6],dx
    2ea6:	mov    BYTE PTR [rbp+rax*1+0x8],0x6
    2eab:	lea    eax,[rcx+0x2]
    2eae:	movzx  eax,ax
    2eb1:	mov    BYTE PTR [rbp+rax*1+0x8],0x7
    2eb6:	cmp    r13,0x6
    2eba:	jne    2e36 <open@plt+0x1d36>
    2ec0:	imul   rbx,QWORD PTR [rsp+0x8],0x30c
    2ec9:	mov    BYTE PTR [rsp+0x3bf],0x1
    2ed1:	add    ecx,0x30
    2ed4:	lea    rax,[rip+0x43405]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    2edb:	mov    DWORD PTR [rsp+0x3bb],0x2040810
    2ee6:	lea    rdi,[rsp+0x3bb]
    2eee:	add    rax,rbx
    2ef1:	movzx  esi,dx
    2ef4:	movzx  r8d,BYTE PTR [rdi]
    2ef8:	add    rdi,0x1
    2efc:	mov    BYTE PTR [rsi+rax*1+0x8],0x2
    2f01:	lea    esi,[rdx+0x1]
    2f04:	movzx  esi,si
    2f07:	mov    BYTE PTR [rax+rsi*1+0x8],0x7
    2f0c:	lea    esi,[rdx+0x2]
    2f0f:	movzx  esi,si
    2f12:	mov    BYTE PTR [rax+rsi*1+0x8],0x6
    2f17:	lea    esi,[rdx+0x3]
    2f1a:	movzx  esi,si
    2f1d:	mov    BYTE PTR [rax+rsi*1+0x8],0x8
    2f22:	lea    esi,[rdx+0x4]
    2f25:	movzx  esi,si
    2f28:	mov    BYTE PTR [rax+rsi*1+0x8],0x7
    2f2d:	lea    esi,[rdx+0x5]
    2f30:	movzx  esi,si
    2f33:	mov    BYTE PTR [rax+rsi*1+0x8],r8b
    2f38:	lea    esi,[rdx+0x6]
    2f3b:	movzx  esi,si
    2f3e:	mov    BYTE PTR [rax+rsi*1+0x8],0x6
    2f43:	lea    esi,[rdx+0x7]
    2f46:	movzx  esi,si
    2f49:	mov    BYTE PTR [rax+rsi*1+0x8],0x6
    2f4e:	lea    esi,[rdx+0x8]
    2f51:	add    edx,0x9
    2f54:	movzx  esi,si
    2f57:	mov    BYTE PTR [rax+rsi*1+0x8],0x7
    2f5c:	cmp    cx,dx
    2f5f:	jne    2ef1 <open@plt+0x1df1>
    2f61:	movzx  ebx,WORD PTR [rsp+0x84]
    2f69:	mov    WORD PTR [rax+0x6],cx
    2f6d:	xor    esi,esi
    2f6f:	mov    BYTE PTR [rax+0x20c],0x0
    2f76:	mov    WORD PTR [rax+0x20e],bx
    2f7d:	movzx  ebx,WORD PTR [rsp+0x82]
    2f85:	mov    BYTE PTR [rax+0x21c],0x1
    2f8c:	mov    WORD PTR [rax+0x21e],bx
    2f93:	mov    BYTE PTR [rax+0x208],0x2
    2f9a:	mov    WORD PTR [rax+0x4],bx
    2f9e:	cmp    BYTE PTR [r15+0x208],0x0
    2fa6:	je     35e7 <open@plt+0x24e7>
    2fac:	mov    r14,QWORD PTR [rip+0x43315]        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    2fb3:	mov    DWORD PTR [rsp+0x8],esi
    2fb7:	xor    ebp,ebp
    2fb9:	mov    r13,r15
    2fbc:	movabs rbx,0x9e3779b97f4a7c15
    2fc6:	mov    QWORD PTR [rsp+0x18],r11
    2fcb:	add    r14,rbx
    2fce:	mov    QWORD PTR [rsp+0x20],r10
    2fd3:	mov    rdi,r14
    2fd6:	mov    DWORD PTR [rsp+0x10],r12d
    2fdb:	lea    r14,[r15+0x214]
    2fe2:	mov    r12d,ebp
    2fe5:	mov    r15,rdi
    2fe8:	lea    rbp,[rsp+0x3f0]
    2ff0:	mov    rdx,r15
    2ff3:	movzx  esi,WORD PTR [r14-0x6]
    2ff8:	mov    rcx,r14
    2ffb:	add    r12d,0x1
    2fff:	shr    rdx,0x1e
    3003:	mov    QWORD PTR [rip+0x432be],r15        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    300a:	add    r14,0x10
    300e:	movabs rax,0xbf58476d1ce4e5b9
    3018:	xor    rdx,r15
    301b:	mov    WORD PTR [rsp+0x3f2],si
    3023:	mov    rsi,rbp
    3026:	movabs rdi,0x94d049bb133111eb
    3030:	imul   rdx,rax
    3034:	add    r15,rbx
    3037:	mov    rax,rdx
    303a:	shr    rax,0x1b
    303e:	xor    rax,rdx
    3041:	imul   rax,rdi
    3045:	movzx  edi,WORD PTR [r13+0x0]
    304a:	mov    WORD PTR [rsp+0x3f0],di
    3052:	mov    edi,0x45
    3057:	mov    rdx,rax
    305a:	shr    rdx,0x1f
    305e:	xor    rax,rdx
    3061:	movzx  edx,BYTE PTR [r14-0x18]
    3066:	mov    DWORD PTR [r14-0x14],eax
    306a:	mov    BYTE PTR [rsp+0x3f4],dl
    3071:	mov    edx,0x9
    3076:	mov    DWORD PTR [rsp+0x3f5],eax
    307d:	call   1af0 <open@plt+0x9f0>
    3082:	movzx  eax,BYTE PTR [r13+0x208]
    308a:	cmp    eax,r12d
    308d:	jg     2ff0 <open@plt+0x1ef0>
    3093:	mov    esi,DWORD PTR [rsp+0x8]
    3097:	mov    r12d,DWORD PTR [rsp+0x10]
    309c:	mov    r11,QWORD PTR [rsp+0x18]
    30a1:	mov    r10,QWORD PTR [rsp+0x20]
    30a6:	add    esi,0x1
    30a9:	cmp    esi,0x3
    30ac:	je     30fb <open@plt+0x1ffb>
    30ae:	cmp    esi,0x1
    30b1:	je     35ec <open@plt+0x24ec>
    30b7:	mov    esi,0x2
    30bc:	cmp    BYTE PTR [r11+0x208],0x0
    30c4:	je     30fb <open@plt+0x1ffb>
    30c6:	mov    r15,r11
    30c9:	jmp    2fac <open@plt+0x1eac>
    30ce:	mov    BYTE PTR [rbp+rax*1+0x8],0x2
    30d3:	lea    eax,[rcx+0x1]
    30d6:	mov    r13d,0x1
    30dc:	movzx  eax,ax
    30df:	mov    BYTE PTR [rbp+rax*1+0x8],0x6
    30e4:	lea    eax,[rcx+0x3]
    30e7:	mov    WORD PTR [rbp+0x6],ax
    30eb:	lea    eax,[rcx+0x2]
    30ee:	movzx  eax,ax
    30f1:	mov    BYTE PTR [rbp+rax*1+0x8],0x7
    30f6:	jmp    2e36 <open@plt+0x1d36>
    30fb:	test   r12d,r12d
    30fe:	jle    35ad <open@plt+0x24ad>
    3104:	mov    ebx,DWORD PTR [rsp+0x7c]
    3108:	lea    rax,[rsp+0x1b0]
    3110:	lea    edx,[rbx+0x5]
    3113:	lea    rsi,[rsp+rdx*2+0x1b2]
    311b:	lea    rdx,[rip+0x431be]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    3122:	movzx  ecx,WORD PTR [rdx]
    3125:	add    rax,0x2
    3129:	add    rdx,0x30c
    3130:	mov    WORD PTR [rax-0x2],cx
    3134:	cmp    rsi,rax
    3137:	jne    3122 <open@plt+0x2022>
    3139:	mov    r15,QWORD PTR [rip+0x43188]        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    3140:	xor    r11d,r11d
    3143:	xor    edx,edx
    3145:	xor    r14d,r14d
    3148:	lea    r9,[rip+0x4339d]        # 464ec <stdin@GLIBC_2.2.5+0x4045c>
    314f:	movabs rbx,0x9e3779b97f4a7c15
    3159:	movabs r13,0xbf58476d1ce4e5b9
    3163:	movabs rbp,0x94d049bb133111eb
    316d:	jmp    318a <open@plt+0x208a>
    316f:	add    r14d,0x1
    3173:	add    r11,0x30c
    317a:	add    r9,0x30c
    3181:	cmp    r14d,r12d
    3184:	je     35a2 <open@plt+0x24a2>
    318a:	movzx  eax,BYTE PTR [r9-0x4]
    318f:	mov    DWORD PTR [rsp+0x10],eax
    3193:	mov    edi,eax
    3195:	test   eax,eax
    3197:	je     316f <open@plt+0x206f>
    3199:	sub    eax,0x1
    319c:	mov    BYTE PTR [rsp+0x28],dil
    31a1:	mov    r10,r9
    31a4:	xor    r8d,r8d
    31a7:	lea    rcx,[rip+0x43132]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    31ae:	shl    rax,0x4
    31b2:	mov    DWORD PTR [rsp+0x30],r14d
    31b7:	lea    rcx,[rcx+r11*1+0x21c]
    31bf:	mov    QWORD PTR [rsp+0x38],r9
    31c4:	add    rcx,rax
    31c7:	mov    DWORD PTR [rsp+0x18],r12d
    31cc:	mov    QWORD PTR [rsp+0x20],rcx
    31d1:	mov    QWORD PTR [rsp+0x40],r11
    31d6:	cs nop WORD PTR [rax+rax*1+0x0]
    31e0:	mov    eax,DWORD PTR [rsp+0x10]
    31e4:	add    eax,r8d
    31e7:	cmp    eax,0xf
    31ea:	jg     33ce <open@plt+0x22ce>
    31f0:	add    r15,rbx
    31f3:	mov    rdi,r15
    31f6:	shr    rdi,0x1e
    31fa:	xor    rdi,r15
    31fd:	imul   rdi,r13
    3201:	mov    rdx,rdi
    3204:	shr    rdx,0x1b
    3208:	xor    rdx,rdi
    320b:	mov    edi,r8d
    320e:	imul   rdx,rbp
    3212:	shl    rdi,0x4
    3216:	lea    r11,[rsp+rdi*1+0xb0]
    321e:	mov    rdi,rdx
    3221:	shr    rdi,0x1f
    3225:	xor    rdi,rdx
    3228:	and    edi,0x1
    322b:	lea    edi,[r8+rdi*1+0x1]
    3230:	mov    DWORD PTR [rsp+0x8],edi
    3234:	mov    edi,DWORD PTR [rsp+0x18]
    3238:	cmp    eax,0xf
    323b:	ja     33ba <open@plt+0x22ba>
    3241:	nop    DWORD PTR [rax+0x0]
    3245:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    3250:	movzx  r12d,BYTE PTR [r10]
    3254:	movzx  esi,WORD PTR [r10+0x2]
    3259:	nop    WORD PTR [rax+rax*1+0x0]
    325f:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    326a:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    3275:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    3280:	mov    r14,r15
    3283:	add    r15,rbx
    3286:	mov    rax,r15
    3289:	shr    rax,0x1e
    328d:	xor    rax,r15
    3290:	imul   rax,r13
    3294:	mov    rdx,rax
    3297:	shr    rdx,0x1b
    329b:	xor    rdx,rax
    329e:	imul   rdx,rbp
    32a2:	mov    rax,rdx
    32a5:	shr    rax,0x1f
    32a9:	xor    rax,rdx
    32ac:	xor    edx,edx
    32ae:	div    rdi
    32b1:	movzx  ecx,WORD PTR [rsp+rdx*2+0x1b0]
    32b9:	cmp    si,cx
    32bc:	je     3280 <open@plt+0x2180>
    32be:	movabs rax,0x3c6ef372fe94f82a
    32c8:	lea    rdx,[r14+rax*1]
    32cc:	mov    rsi,rdx
    32cf:	shr    rsi,0x1e
    32d3:	xor    rsi,rdx
    32d6:	imul   rsi,r13
    32da:	mov    rax,rsi
    32dd:	shr    rax,0x1b
    32e1:	xor    rax,rsi
    32e4:	lea    rsi,[rsp+0xa8]
    32ec:	imul   rax,rbp
    32f0:	mov    r9,rax
    32f3:	shr    r9,0x1f
    32f7:	xor    r9,rax
    32fa:	movabs rax,0xf1bbcdcbfa53e0a8
    3304:	lea    r15,[r14+rax*1]
    3308:	nop
    3309:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    3314:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    331f:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    332a:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    3335:	data16 cs nop WORD PTR [rax+rax*1+0x0]
    3340:	add    rdx,rbx
    3343:	add    rsi,0x1
    3347:	mov    r14,rdx
    334a:	shr    r14,0x1e
    334e:	xor    r14,rdx
    3351:	imul   r14,r13
    3355:	mov    rax,r14
    3358:	shr    rax,0x1b
    335c:	xor    rax,r14
    335f:	imul   rax,rbp
    3363:	mov    r14,rax
    3366:	shr    r14,0x1f
    336a:	xor    rax,r14
    336d:	mov    BYTE PTR [rsi-0x1],al
    3370:	cmp    rdx,r15
    3373:	jne    3340 <open@plt+0x2240>
    3375:	mov    BYTE PTR [rsp+0xa0],r12b
    337d:	add    r8d,0x1
    3381:	add    r11,0x10
    3385:	mov    WORD PTR [rsp+0xa2],cx
    338d:	mov    DWORD PTR [rsp+0xa4],r9d
    3395:	movdqa xmm0,XMMWORD PTR [rsp+0xa0]
    339e:	movaps XMMWORD PTR [r11-0x10],xmm0
    33a3:	cmp    r8d,DWORD PTR [rsp+0x8]
    33a8:	je     33ba <open@plt+0x22ba>
    33aa:	mov    eax,DWORD PTR [rsp+0x10]
    33ae:	add    eax,r8d
    33b1:	cmp    eax,0xf
    33b4:	jbe    3250 <open@plt+0x2150>
    33ba:	add    r10,0x10
    33be:	mov    edx,0x1
    33c3:	cmp    r10,QWORD PTR [rsp+0x20]
    33c8:	jne    31e0 <open@plt+0x20e0>
    33ce:	movzx  edi,BYTE PTR [rsp+0x28]
    33d3:	mov    r14d,DWORD PTR [rsp+0x30]
    33d8:	mov    r9,QWORD PTR [rsp+0x38]
    33dd:	mov    r12d,DWORD PTR [rsp+0x18]
    33e2:	mov    r11,QWORD PTR [rsp+0x40]
    33e7:	test   r8d,r8d
    33ea:	je     342f <open@plt+0x232f>
    33ec:	movzx  eax,dil
    33f0:	add    rax,0x20
    33f4:	shl    rax,0x4
    33f8:	lea    rcx,[r11+rax*1+0xc]
    33fd:	lea    rax,[rip+0x42edc]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    3404:	add    rcx,rax
    3407:	mov    eax,r8d
    340a:	shl    rax,0x4
    340e:	cmp    eax,0x40
    3411:	jae    3511 <open@plt+0x2411>
    3417:	test   al,0x20
    3419:	jne    3623 <open@plt+0x2523>
    341f:	test   al,0x10
    3421:	jne    3602 <open@plt+0x2502>
    3427:	test   eax,eax
    3429:	jne    35d8 <open@plt+0x24d8>
    342f:	lea    ecx,[rdi+r8*1]
    3433:	movzx  r10d,cl
    3437:	mov    BYTE PTR [r9-0x4],cl
    343b:	cmp    r10d,0x1
    343f:	jle    316f <open@plt+0x206f>
    3445:	lea    esi,[r10-0x1]
    3449:	lea    rax,[rip+0x4309c]        # 464ec <stdin@GLIBC_2.2.5+0x4045c>
    3450:	movzx  ecx,cl
    3453:	movabs rdx,0x61c8864680b583eb
    345d:	add    rax,r11
    3460:	shl    rsi,0x4
    3464:	lea    rdi,[r15+rbx*1]
    3468:	add    rsi,rax
    346b:	lea    eax,[r10-0x2]
    346f:	mov    QWORD PTR [rsp+0x8],rdi
    3474:	imul   rax,rdx
    3478:	sub    rdi,rax
    347b:	mov    r8,rdi
    347e:	mov    edi,r14d
    3481:	imul   rdi,rdi,0x30c
    3488:	nop    DWORD PTR [rax+rax*1+0x0]
    3490:	add    r15,rbx
    3493:	movdqu xmm0,XMMWORD PTR [rsi]
    3497:	sub    rsi,0x10
    349b:	mov    rax,r15
    349e:	shr    rax,0x1e
    34a2:	movaps XMMWORD PTR [rsp+0xa0],xmm0
    34aa:	xor    rax,r15
    34ad:	imul   rax,r13
    34b1:	mov    rdx,rax
    34b4:	shr    rdx,0x1b
    34b8:	xor    rdx,rax
    34bb:	imul   rdx,rbp
    34bf:	mov    rax,rdx
    34c2:	shr    rax,0x1f
    34c6:	xor    rax,rdx
    34c9:	xor    edx,edx
    34cb:	div    rcx
    34ce:	sub    rcx,0x1
    34d2:	mov    eax,edx
    34d4:	lea    rdx,[rip+0x42e05]        # 462e0 <stdin@GLIBC_2.2.5+0x40250>
    34db:	add    rax,0x20
    34df:	shl    rax,0x4
    34e3:	add    rax,rdi
    34e6:	movdqu xmm1,XMMWORD PTR [rax+rdx*1+0xc]
    34ec:	movups XMMWORD PTR [rsi+0x10],xmm1
    34f0:	movups XMMWORD PTR [rax+rdx*1+0xc],xmm0
    34f5:	cmp    r15,r8
    34f8:	jne    3490 <open@plt+0x2390>
    34fa:	lea    r15d,[r10-0x2]
    34fe:	mov    edx,0x1
    3503:	imul   r15,rbx
    3507:	add    r15,QWORD PTR [rsp+0x8]
    350c:	jmp    316f <open@plt+0x206f>
    3511:	mov    r10d,eax
    3514:	sub    eax,0x1
    3517:	lea    rsi,[rcx+r10*1]
    351b:	lea    r10,[rsp+r10*1+0xb0]
    3523:	movdqu xmm0,XMMWORD PTR [r10-0x40]
    3529:	movups XMMWORD PTR [rsi-0x40],xmm0
    352d:	movdqu xmm0,XMMWORD PTR [r10-0x30]
    3533:	movups XMMWORD PTR [rsi-0x30],xmm0
    3537:	movdqu xmm0,XMMWORD PTR [r10-0x20]
    353d:	movups XMMWORD PTR [rsi-0x20],xmm0
    3541:	movdqu xmm0,XMMWORD PTR [r10-0x10]
    3547:	movups XMMWORD PTR [rsi-0x10],xmm0
    354b:	cmp    eax,0x40
    354e:	jb     342f <open@plt+0x232f>
    3554:	and    eax,0xffffffc0
    3557:	xor    r10d,r10d
    355a:	mov    esi,r10d
    355d:	add    r10d,0x40
    3561:	movdqu xmm3,XMMWORD PTR [rsp+rsi*1+0xb0]
    356a:	movdqu xmm2,XMMWORD PTR [rsp+rsi*1+0xc0]
    3573:	movdqu xmm1,XMMWORD PTR [rsp+rsi*1+0xd0]
    357c:	movdqu xmm0,XMMWORD PTR [rsp+rsi*1+0xe0]
    3585:	movups XMMWORD PTR [rcx+rsi*1],xmm3
    3589:	movups XMMWORD PTR [rcx+rsi*1+0x10],xmm2
    358e:	movups XMMWORD PTR [rcx+rsi*1+0x20],xmm1
    3593:	movups XMMWORD PTR [rcx+rsi*1+0x30],xmm0
    3598:	cmp    r10d,eax
    359b:	jb     355a <open@plt+0x245a>
    359d:	jmp    342f <open@plt+0x232f>
    35a2:	test   dl,dl
    35a4:	je     35ad <open@plt+0x24ad>
    35a6:	mov    QWORD PTR [rip+0x42d1b],r15        # 462c8 <stdin@GLIBC_2.2.5+0x40238>
    35ad:	xor    eax,eax
    35af:	mov    rdx,QWORD PTR [rsp+0x10478]
    35b7:	sub    rdx,QWORD PTR fs:0x28
    35c0:	jne    3673 <open@plt+0x2573>
    35c6:	add    rsp,0x10488
    35cd:	pop    rbx
    35ce:	pop    rbp
    35cf:	pop    r12
    35d1:	pop    r13
    35d3:	pop    r14
    35d5:	pop    r15
    35d7:	ret
    35d8:	movzx  eax,BYTE PTR [rsp+0xb0]
    35e0:	mov    BYTE PTR [rcx],al
    35e2:	jmp    342f <open@plt+0x232f>
    35e7:	mov    esi,0x1
    35ec:	mov    r15,r10
    35ef:	cmp    BYTE PTR [r10+0x208],0x0
    35f7:	jne    2fac <open@plt+0x1eac>
    35fd:	jmp    30b7 <open@plt+0x1fb7>
    3602:	movdqu xmm0,XMMWORD PTR [rsp+0xb0]
    360b:	mov    eax,eax
    360d:	movups XMMWORD PTR [rcx],xmm0
    3610:	movdqu xmm0,XMMWORD PTR [rsp+rax*1+0xa0]
    3619:	movups XMMWORD PTR [rcx+rax*1-0x10],xmm0
    361e:	jmp    342f <open@plt+0x232f>
    3623:	movdqu xmm0,XMMWORD PTR [rsp+0xb0]
    362c:	mov    eax,eax
    362e:	movups XMMWORD PTR [rcx],xmm0
    3631:	movdqu xmm0,XMMWORD PTR [rsp+0xc0]
    363a:	movups XMMWORD PTR [rcx+0x10],xmm0
    363e:	lea    rcx,[rcx+rax*1+0x20]
    3643:	lea    rax,[rsp+rax*1+0xd0]
    364b:	movdqu xmm0,XMMWORD PTR [rax-0x40]
    3650:	movups XMMWORD PTR [rcx-0x40],xmm0
    3654:	movdqu xmm0,XMMWORD PTR [rax-0x30]
    3659:	movups XMMWORD PTR [rcx-0x30],xmm0
    365d:	jmp    342f <open@plt+0x232f>
    3662:	mov    edi,ebx
    3664:	call   10b0 <close@plt>
    3669:	mov    eax,0xffffffff
    366e:	jmp    35af <open@plt+0x24af>
    3673:	call   1070 <__stack_chk_fail@plt>
    3678:	mov    DWORD PTR [rsp+0x10],r13d
    367d:	mov    rbx,QWORD PTR [rsp+0x88]
    3685:	movzx  r14d,WORD PTR [rip+0x42a7d]        # 4610a <stdin@GLIBC_2.2.5+0x4007a>
    368d:	jmp    2a32 <open@plt+0x1932>
