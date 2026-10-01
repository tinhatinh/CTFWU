
files/chall:     file format elf64-x86-64


Disassembly of section .interp:

0000000000400318 <.interp>:
  400318:	(bad)
  400319:	ins    BYTE PTR es:[rdi],dx
  40031a:	imul   esp,DWORD PTR [rdx+0x36],0x646c2f34
  400321:	sub    eax,0x756e696c
  400326:	js     400355 <puts@plt-0xcdb>
  400328:	js     400362 <puts@plt-0xcce>
  40032a:	ss sub eax,0x732e3436
  400330:	outs   dx,DWORD PTR ds:[rsi]
  400331:	cs xor al,BYTE PTR [rax]

Disassembly of section .note.gnu.property:

0000000000400338 <.note.gnu.property>:
  400338:	add    al,0x0
  40033a:	add    BYTE PTR [rax],al
  40033c:	adc    BYTE PTR [rax],al
  40033e:	add    BYTE PTR [rax],al
  400340:	add    eax,0x47000000
  400345:	rex.WRX push rbp
  400347:	add    BYTE PTR [rdx],al
  400349:	add    BYTE PTR [rax],0xc0
  40034c:	add    al,0x0
  40034e:	add    BYTE PTR [rax],al
  400350:	add    DWORD PTR [rax],eax
  400352:	add    BYTE PTR [rax],al
  400354:	add    BYTE PTR [rax],al
	...

Disassembly of section .note.gnu.build-id:

0000000000400358 <.note.gnu.build-id>:
  400358:	add    al,0x0
  40035a:	add    BYTE PTR [rax],al
  40035c:	adc    al,0x0
  40035e:	add    BYTE PTR [rax],al
  400360:	add    eax,DWORD PTR [rax]
  400362:	add    BYTE PTR [rax],al
  400364:	rex.RXB
  400365:	rex.WRX push rbp
  400367:	add    BYTE PTR [rbp-0x3a],bl
  40036a:	(bad)
  40036b:	shl    DWORD PTR [rbx+0x698f9686],1
  400371:	(bad)
  400372:	rex.WRXB pop r9
  400374:	rex cmp eax,0x227be781
  40037a:	.byte 0xbe
  40037b:	.byte 0x70

Disassembly of section .note.ABI-tag:

000000000040037c <.note.ABI-tag>:
  40037c:	add    al,0x0
  40037e:	add    BYTE PTR [rax],al
  400380:	adc    BYTE PTR [rax],al
  400382:	add    BYTE PTR [rax],al
  400384:	add    DWORD PTR [rax],eax
  400386:	add    BYTE PTR [rax],al
  400388:	rex.RXB
  400389:	rex.WRX push rbp
  40038b:	add    BYTE PTR [rax],al
  40038d:	add    BYTE PTR [rax],al
  40038f:	add    BYTE PTR [rbx],al
  400391:	add    BYTE PTR [rax],al
  400393:	add    BYTE PTR [rdx],al
  400395:	add    BYTE PTR [rax],al
  400397:	add    BYTE PTR [rax],al
  400399:	add    BYTE PTR [rax],al
	...

Disassembly of section .gnu.hash:

00000000004003a0 <.gnu.hash>:
  4003a0:	add    eax,DWORD PTR [rax]
  4003a2:	add    BYTE PTR [rax],al
  4003a4:	or     eax,0x1000000
  4003a9:	add    BYTE PTR [rax],al
  4003ab:	add    BYTE PTR [rsi],al
  4003ad:	add    BYTE PTR [rax],al
  4003af:	add    BYTE PTR [rax],al
  4003b1:	add    DWORD PTR [rax],esp
  4003b3:	add    BYTE PTR [rax+0xd021001],al
  4003b9:	add    BYTE PTR [rax],al
  4003bb:	add    BYTE PTR [rsi],cl
  4003bd:	add    BYTE PTR [rax],al
  4003bf:	add    BYTE PTR [rax],al
  4003c1:	add    BYTE PTR [rax],al
  4003c3:	add    BYTE PTR [rcx],ch
  4003c5:	sbb    eax,0x55661c8c
  4003ca:	(bad)
  4003cb:	adc    BYTE PTR [rcx],bh
  4003cd:	repnz
  4003ce:	.byte 0x8b
  4003cf:	.byte 0x1c

Disassembly of section .dynsym:

00000000004003d0 <.dynsym>:
	...
  4003e8:	rex.X add BYTE PTR [rax],al
  4003eb:	add    BYTE PTR [rdx],dl
	...
  4003fd:	add    BYTE PTR [rax],al
  4003ff:	add    BYTE PTR [rip+0x12000000],dl        # 12400405 <stderr@GLIBC_2.2.5+0x11ffc385>
	...
  400415:	add    BYTE PTR [rax],al
  400417:	add    BYTE PTR [rbx+0x0],bl
  40041a:	add    BYTE PTR [rax],al
  40041c:	adc    al,BYTE PTR [rax]
	...
  40042e:	add    BYTE PTR [rax],al
  400430:	sbb    al,BYTE PTR [rax]
  400432:	add    BYTE PTR [rax],al
  400434:	adc    al,BYTE PTR [rax]
	...
  400446:	add    BYTE PTR [rax],al
  400448:	imul   eax,DWORD PTR [rax],0x120000
	...
  40045e:	add    BYTE PTR [rax],al
  400460:	(bad)
  400461:	add    BYTE PTR [rax],al
  400463:	add    BYTE PTR [rdx],dl
	...
  400475:	add    BYTE PTR [rax],al
  400477:	add    BYTE PTR [rsi],dh
  400479:	add    BYTE PTR [rax],al
  40047b:	add    BYTE PTR [rdx],dl
	...
  40048d:	add    BYTE PTR [rax],al
  40048f:	add    BYTE PTR [rcx],al
  400491:	add    BYTE PTR [rax],al
  400493:	add    BYTE PTR [rdx],dl
	...
  4004a5:	add    BYTE PTR [rax],al
  4004a7:	add    BYTE PTR [rbx+0x20000000],bl
	...
  4004bd:	add    BYTE PTR [rax],al
  4004bf:	add    BYTE PTR [rdi],al
  4004c1:	add    BYTE PTR [rax],al
  4004c3:	add    BYTE PTR [rdx],dl
	...
  4004d5:	add    BYTE PTR [rax],al
  4004d7:	add    BYTE PTR [rax],dh
  4004d9:	add    BYTE PTR [rax],al
  4004db:	add    BYTE PTR [rdx],dl
	...
  4004ed:	add    BYTE PTR [rax],al
  4004ef:	add    BYTE PTR [rbx],ch
  4004f1:	add    BYTE PTR [rax],al
  4004f3:	add    BYTE PTR [rdx],dl
	...
  400505:	add    BYTE PTR [rax],al
  400507:	add    BYTE PTR [rbx],bh
  400509:	add    BYTE PTR [rax],al
  40050b:	add    BYTE PTR [rcx],dl
  40050d:	add    BYTE PTR [rcx],bl
  40050f:	add    BYTE PTR [rax+0x40],ah
  400512:	rex add BYTE PTR [rax],al
  400515:	add    BYTE PTR [rax],al
  400517:	add    BYTE PTR [rax],cl
  400519:	add    BYTE PTR [rax],al
  40051b:	add    BYTE PTR [rax],al
  40051d:	add    BYTE PTR [rax],al
  40051f:	add    BYTE PTR [rdi],cl
  400521:	add    BYTE PTR [rax],al
  400523:	add    BYTE PTR [rcx],dl
  400525:	add    BYTE PTR [rcx],bl
  400527:	add    BYTE PTR [rax+0x40],dh
  40052a:	rex add BYTE PTR [rax],al
  40052d:	add    BYTE PTR [rax],al
  40052f:	add    BYTE PTR [rax],cl
  400531:	add    BYTE PTR [rax],al
  400533:	add    BYTE PTR [rax],al
  400535:	add    BYTE PTR [rax],al
  400537:	add    BYTE PTR [rax+rax*1+0x0],dl
  40053b:	add    BYTE PTR [rcx],dl
  40053d:	add    BYTE PTR [rcx],bl
  40053f:	add    BYTE PTR [rax+0x4040],al
  400545:	add    BYTE PTR [rax],al
  400547:	add    BYTE PTR [rax],cl
  400549:	add    BYTE PTR [rax],al
  40054b:	add    BYTE PTR [rax],al
  40054d:	add    BYTE PTR [rax],al
	...

Disassembly of section .dynstr:

0000000000400550 <.dynstr>:
  400550:	add    BYTE PTR [rsi+0x67],ah
  400553:	gs je  4005c9 <puts@plt-0xa67>
  400556:	add    BYTE PTR [rbx+0x65],dh
  400559:	je     4005d1 <puts@plt-0xa5f>
  40055b:	(bad)
  400560:	je     4005c6 <puts@plt-0xa6a>
  400562:	imul   ebp,DWORD PTR [rsi+0x0],0x73747570
  400569:	add    BYTE PTR [rdi+0x5f],bl
  40056c:	jae    4005e2 <puts@plt-0xa4e>
  40056e:	(bad)
  40056f:	movsxd ebp,DWORD PTR [rbx+0x5f]
  400572:	movsxd ebp,DWORD PTR [rax+0x6b]
  400575:	pop    rdi
  400576:	data16 (bad)
  400578:	imul   ebp,DWORD PTR [rax+rax*1+0x65],0x746978
  400580:	outs   dx,WORD PTR ds:[rsi]
  400582:	jo     4005e9 <puts@plt-0xa47>
  400584:	outs   dx,BYTE PTR ds:[rsi]
  400585:	add    BYTE PTR [rdx+0x65],dh
  400588:	(bad)
  400589:	add    BYTE PTR fs:[rbx+0x74],dh
  40058d:	outs   dx,DWORD PTR fs:[rsi]
  40058f:	jne    400605 <puts@plt-0xa2b>
  400591:	add    BYTE PTR [rdi+0x5f],bl
  400594:	ins    BYTE PTR es:[rdi],dx
  400595:	imul   esp,DWORD PTR [rdx+0x63],0x6174735f
  40059c:	jb     400612 <puts@plt-0xa1e>
  40059e:	pop    rdi
  40059f:	ins    DWORD PTR es:[rdi],dx
  4005a0:	(bad)
  4005a1:	imul   ebp,DWORD PTR [rsi+0x0],0x65647473
  4005a8:	jb     40061c <puts@plt-0xa14>
  4005aa:	add    BYTE PTR [rsi+0x63],ah
  4005ad:	ins    BYTE PTR es:[rdi],dx
  4005ae:	outs   dx,DWORD PTR ds:[rsi]
  4005af:	jae    400616 <puts@plt-0xa1a>
  4005b1:	add    BYTE PTR [rbp+0x65],ch
  4005b4:	ins    DWORD PTR es:[rdi],dx
  4005b5:	jae    40061c <puts@plt-0xa14>
  4005b7:	je     4005b9 <puts@plt-0xa77>
  4005b9:	jo     40062d <puts@plt-0xa03>
  4005bb:	imul   ebp,DWORD PTR [rsi+0x74],0x696c0066
  4005c2:	(bad)
  4005c7:	cs ss add BYTE PTR [rdi+0x4c],al
  4005cc:	rex.WB
  4005cd:	rex.X
  4005ce:	rex.XB pop r15
  4005d0:	xor    ch,BYTE PTR [rsi]
  4005d2:	xor    al,0x0
  4005d4:	rex.RXB
  4005d5:	rex.WR
  4005d6:	rex.WB
  4005d7:	rex.X
  4005d8:	rex.XB pop r15
  4005da:	xor    ch,BYTE PTR [rsi]
  4005dc:	xor    ch,BYTE PTR [rsi]
  4005de:	xor    eax,0x494c4700
  4005e3:	rex.X
  4005e4:	rex.XB pop r15
  4005e6:	xor    ch,BYTE PTR [rsi]
  4005e8:	xor    esi,DWORD PTR [rax+rax*1]
  4005eb:	pop    rdi
  4005ec:	pop    rdi
  4005ed:	ins    DWORD PTR es:[edi],dx
  4005ef:	outs   dx,DWORD PTR ds:[rsi]
  4005f0:	outs   dx,BYTE PTR ds:[rsi]
  4005f1:	pop    rdi
  4005f2:	jae    400668 <puts@plt-0x9c8>
  4005f4:	(bad)
  4005f5:	jb     40066b <puts@plt-0x9c5>
  4005f7:	pop    rdi
  4005f8:	pop    rdi
	...

Disassembly of section .gnu.version:

00000000004005fa <.gnu.version>:
  4005fa:	add    BYTE PTR [rax],al
  4005fc:	add    al,BYTE PTR [rax]
  4005fe:	add    eax,DWORD PTR [rax]
  400600:	add    eax,DWORD PTR [rax]
  400602:	add    al,0x0
  400604:	add    eax,DWORD PTR [rax]
  400606:	add    eax,DWORD PTR [rax]
  400608:	add    eax,DWORD PTR [rax]
  40060a:	add    eax,DWORD PTR [rax]
  40060c:	add    DWORD PTR [rax],eax
  40060e:	add    eax,DWORD PTR [rax]
  400610:	add    eax,DWORD PTR [rax]
  400612:	add    eax,DWORD PTR [rax]
  400614:	add    eax,DWORD PTR [rax]
  400616:	add    eax,DWORD PTR [rax]
  400618:	add    eax,DWORD PTR [rax]

Disassembly of section .gnu.version_r:

0000000000400620 <.gnu.version_r>:
  400620:	add    DWORD PTR [rax],eax
  400622:	add    eax,DWORD PTR [rax]
  400624:	jo     400626 <puts@plt-0xa0a>
  400626:	add    BYTE PTR [rax],al
  400628:	adc    BYTE PTR [rax],al
  40062a:	add    BYTE PTR [rax],al
  40062c:	add    BYTE PTR [rax],al
  40062e:	add    BYTE PTR [rax],al
  400630:	adc    al,0x69
  400632:	imul   ecx,DWORD PTR [rip+0x40000],0x7a        # 44063c <stderr@GLIBC_2.2.5+0x3c5bc>
  40063c:	adc    BYTE PTR [rax],al
  40063e:	add    BYTE PTR [rax],al
  400640:	jne    40065c <puts@plt-0x9d4>
  400642:	imul   ecx,DWORD PTR [rcx],0x30000
  400648:	test   BYTE PTR [rax],al
  40064a:	add    BYTE PTR [rax],al
  40064c:	adc    BYTE PTR [rax],al
  40064e:	add    BYTE PTR [rax],al
  400650:	mov    ah,0x91
  400652:	xchg   esi,eax
  400653:	(bad)
  400654:	add    BYTE PTR [rax],al
  400656:	add    al,BYTE PTR [rax]
  400658:	nop
  400659:	add    BYTE PTR [rax],al
  40065b:	add    BYTE PTR [rax],al
  40065d:	add    BYTE PTR [rax],al
	...

Disassembly of section .rela.dyn:

0000000000400660 <.rela.dyn>:
  400660:	fdivr  DWORD PTR [rdi]
  400662:	rex add BYTE PTR [rax],al
  400665:	add    BYTE PTR [rax],al
  400667:	add    BYTE PTR [rsi],al
  400669:	add    BYTE PTR [rax],al
  40066b:	add    BYTE PTR [rcx],al
	...
  400675:	add    BYTE PTR [rax],al
  400677:	add    al,ah
  400679:	(bad)
  40067a:	rex add BYTE PTR [rax],al
  40067d:	add    BYTE PTR [rax],al
  40067f:	add    BYTE PTR [rsi],al
  400681:	add    BYTE PTR [rax],al
  400683:	add    BYTE PTR [rcx],cl
	...
  40068d:	add    BYTE PTR [rax],al
  40068f:	add    BYTE PTR [rax+0x40],ah
  400692:	rex add BYTE PTR [rax],al
  400695:	add    BYTE PTR [rax],al
  400697:	add    BYTE PTR [rip+0xd000000],al        # d40069d <stderr@GLIBC_2.2.5+0xcffc61d>
	...
  4006a5:	add    BYTE PTR [rax],al
  4006a7:	add    BYTE PTR [rax+0x40],dh
  4006aa:	rex add BYTE PTR [rax],al
  4006ad:	add    BYTE PTR [rax],al
  4006af:	add    BYTE PTR [rip+0xe000000],al        # e4006b5 <stderr@GLIBC_2.2.5+0xdffc635>
	...
  4006bd:	add    BYTE PTR [rax],al
  4006bf:	add    BYTE PTR [rax+0x4040],al
  4006c5:	add    BYTE PTR [rax],al
  4006c7:	add    BYTE PTR [rip+0xf000000],al        # f4006cd <stderr@GLIBC_2.2.5+0xeffc64d>
	...

Disassembly of section .rela.plt:

00000000004006d8 <.rela.plt>:
  4006d8:	add    BYTE PTR [rax+0x40],al
  4006db:	add    BYTE PTR [rax],al
  4006dd:	add    BYTE PTR [rax],al
  4006df:	add    BYTE PTR [rdi],al
  4006e1:	add    BYTE PTR [rax],al
  4006e3:	add    BYTE PTR [rdx],al
	...
  4006ed:	add    BYTE PTR [rax],al
  4006ef:	add    BYTE PTR [rax],cl
  4006f1:	rex
  4006f2:	rex add BYTE PTR [rax],al
  4006f5:	add    BYTE PTR [rax],al
  4006f7:	add    BYTE PTR [rdi],al
  4006f9:	add    BYTE PTR [rax],al
  4006fb:	add    BYTE PTR [rbx],al
	...
  400705:	add    BYTE PTR [rax],al
  400707:	add    BYTE PTR [rax],dl
  400709:	rex
  40070a:	rex add BYTE PTR [rax],al
  40070d:	add    BYTE PTR [rax],al
  40070f:	add    BYTE PTR [rdi],al
  400711:	add    BYTE PTR [rax],al
  400713:	add    BYTE PTR [rax+rax*1],al
	...
  40071e:	add    BYTE PTR [rax],al
  400720:	sbb    BYTE PTR [rax+0x40],al
  400723:	add    BYTE PTR [rax],al
  400725:	add    BYTE PTR [rax],al
  400727:	add    BYTE PTR [rdi],al
  400729:	add    BYTE PTR [rax],al
  40072b:	add    BYTE PTR [rip+0x0],al        # 400731 <puts@plt-0x8ff>
  400731:	add    BYTE PTR [rax],al
  400733:	add    BYTE PTR [rax],al
  400735:	add    BYTE PTR [rax],al
  400737:	add    BYTE PTR [rax],ah
  400739:	rex
  40073a:	rex add BYTE PTR [rax],al
  40073d:	add    BYTE PTR [rax],al
  40073f:	add    BYTE PTR [rdi],al
  400741:	add    BYTE PTR [rax],al
  400743:	add    BYTE PTR [rsi],al
	...
  40074d:	add    BYTE PTR [rax],al
  40074f:	add    BYTE PTR [rax],ch
  400751:	rex
  400752:	rex add BYTE PTR [rax],al
  400755:	add    BYTE PTR [rax],al
  400757:	add    BYTE PTR [rdi],al
  400759:	add    BYTE PTR [rax],al
  40075b:	add    BYTE PTR [rdi],al
	...
  400765:	add    BYTE PTR [rax],al
  400767:	add    BYTE PTR [rax],dh
  400769:	rex
  40076a:	rex add BYTE PTR [rax],al
  40076d:	add    BYTE PTR [rax],al
  40076f:	add    BYTE PTR [rdi],al
  400771:	add    BYTE PTR [rax],al
  400773:	add    BYTE PTR [rax],cl
	...
  40077d:	add    BYTE PTR [rax],al
  40077f:	add    BYTE PTR [rax],bh
  400781:	rex
  400782:	rex add BYTE PTR [rax],al
  400785:	add    BYTE PTR [rax],al
  400787:	add    BYTE PTR [rdi],al
  400789:	add    BYTE PTR [rax],al
  40078b:	add    BYTE PTR [rdx],cl
	...
  400795:	add    BYTE PTR [rax],al
  400797:	add    BYTE PTR [rax+0x40],al
  40079a:	rex add BYTE PTR [rax],al
  40079d:	add    BYTE PTR [rax],al
  40079f:	add    BYTE PTR [rdi],al
  4007a1:	add    BYTE PTR [rax],al
  4007a3:	add    BYTE PTR [rbx],cl
	...
  4007ad:	add    BYTE PTR [rax],al
  4007af:	add    BYTE PTR [rax+0x40],cl
  4007b2:	rex add BYTE PTR [rax],al
  4007b5:	add    BYTE PTR [rax],al
  4007b7:	add    BYTE PTR [rdi],al
  4007b9:	add    BYTE PTR [rax],al
  4007bb:	add    BYTE PTR [rax+rax*1],cl
	...

Disassembly of section .init:

0000000000401000 <.init>:
  401000:	sub    rsp,0x8
  401004:	mov    rax,QWORD PTR [rip+0x2fd5]        # 403fe0 <exit@plt+0x2f20>
  40100b:	test   rax,rax
  40100e:	je     401012 <puts@plt-0x1e>
  401010:	call   rax
  401012:	add    rsp,0x8
  401016:	ret

Disassembly of section .plt:

0000000000401020 <puts@plt-0x10>:
  401020:	push   QWORD PTR [rip+0x2fca]        # 403ff0 <exit@plt+0x2f30>
  401026:	jmp    QWORD PTR [rip+0x2fcc]        # 403ff8 <exit@plt+0x2f38>
  40102c:	nop    DWORD PTR [rax+0x0]

0000000000401030 <puts@plt>:
  401030:	jmp    QWORD PTR [rip+0x2fca]        # 404000 <exit@plt+0x2f40>
  401036:	push   0x0
  40103b:	jmp    401020 <puts@plt-0x10>

0000000000401040 <fclose@plt>:
  401040:	jmp    QWORD PTR [rip+0x2fc2]        # 404008 <exit@plt+0x2f48>
  401046:	push   0x1
  40104b:	jmp    401020 <puts@plt-0x10>

0000000000401050 <__stack_chk_fail@plt>:
  401050:	jmp    QWORD PTR [rip+0x2fba]        # 404010 <exit@plt+0x2f50>
  401056:	push   0x2
  40105b:	jmp    401020 <puts@plt-0x10>

0000000000401060 <printf@plt>:
  401060:	jmp    QWORD PTR [rip+0x2fb2]        # 404018 <exit@plt+0x2f58>
  401066:	push   0x3
  40106b:	jmp    401020 <puts@plt-0x10>

0000000000401070 <memset@plt>:
  401070:	jmp    QWORD PTR [rip+0x2faa]        # 404020 <exit@plt+0x2f60>
  401076:	push   0x4
  40107b:	jmp    401020 <puts@plt-0x10>

0000000000401080 <read@plt>:
  401080:	jmp    QWORD PTR [rip+0x2fa2]        # 404028 <exit@plt+0x2f68>
  401086:	push   0x5
  40108b:	jmp    401020 <puts@plt-0x10>

0000000000401090 <fgets@plt>:
  401090:	jmp    QWORD PTR [rip+0x2f9a]        # 404030 <exit@plt+0x2f70>
  401096:	push   0x6
  40109b:	jmp    401020 <puts@plt-0x10>

00000000004010a0 <setvbuf@plt>:
  4010a0:	jmp    QWORD PTR [rip+0x2f92]        # 404038 <exit@plt+0x2f78>
  4010a6:	push   0x7
  4010ab:	jmp    401020 <puts@plt-0x10>

00000000004010b0 <fopen@plt>:
  4010b0:	jmp    QWORD PTR [rip+0x2f8a]        # 404040 <exit@plt+0x2f80>
  4010b6:	push   0x8
  4010bb:	jmp    401020 <puts@plt-0x10>

00000000004010c0 <exit@plt>:
  4010c0:	jmp    QWORD PTR [rip+0x2f82]        # 404048 <exit@plt+0x2f88>
  4010c6:	push   0x9
  4010cb:	jmp    401020 <puts@plt-0x10>

Disassembly of section .text:

00000000004010d0 <.text>:
  4010d0:	xor    ebp,ebp
  4010d2:	mov    r9,rdx
  4010d5:	pop    rsi
  4010d6:	mov    rdx,rsp
  4010d9:	and    rsp,0xfffffffffffffff0
  4010dd:	push   rax
  4010de:	push   rsp
  4010df:	xor    r8d,r8d
  4010e2:	xor    ecx,ecx
  4010e4:	mov    rdi,0x401419
  4010eb:	call   QWORD PTR [rip+0x2ee7]        # 403fd8 <exit@plt+0x2f18>
  4010f1:	hlt
  4010f2:	cs nop WORD PTR [rax+rax*1+0x0]
  4010fc:	nop    DWORD PTR [rax+0x0]
  401100:	ret
  401101:	cs nop WORD PTR [rax+rax*1+0x0]
  40110b:	nop    DWORD PTR [rax+rax*1+0x0]
  401110:	mov    eax,0x404060
  401115:	cmp    rax,0x404060
  40111b:	je     401130 <exit@plt+0x70>
  40111d:	mov    eax,0x0
  401122:	test   rax,rax
  401125:	je     401130 <exit@plt+0x70>
  401127:	mov    edi,0x404060
  40112c:	jmp    rax
  40112e:	xchg   ax,ax
  401130:	ret
  401131:	data16 cs nop WORD PTR [rax+rax*1+0x0]
  40113c:	nop    DWORD PTR [rax+0x0]
  401140:	mov    esi,0x404060
  401145:	sub    rsi,0x404060
  40114c:	mov    rax,rsi
  40114f:	shr    rsi,0x3f
  401153:	sar    rax,0x3
  401157:	add    rsi,rax
  40115a:	sar    rsi,1
  40115d:	je     401170 <exit@plt+0xb0>
  40115f:	mov    eax,0x0
  401164:	test   rax,rax
  401167:	je     401170 <exit@plt+0xb0>
  401169:	mov    edi,0x404060
  40116e:	jmp    rax
  401170:	ret
  401171:	data16 cs nop WORD PTR [rax+rax*1+0x0]
  40117c:	nop    DWORD PTR [rax+0x0]
  401180:	endbr64
  401184:	cmp    BYTE PTR [rip+0x2efd],0x0        # 404088 <stderr@GLIBC_2.2.5+0x8>
  40118b:	jne    4011a0 <exit@plt+0xe0>
  40118d:	push   rbp
  40118e:	mov    rbp,rsp
  401191:	call   401110 <exit@plt+0x50>
  401196:	mov    BYTE PTR [rip+0x2eeb],0x1        # 404088 <stderr@GLIBC_2.2.5+0x8>
  40119d:	pop    rbp
  40119e:	ret
  40119f:	nop
  4011a0:	ret
  4011a1:	data16 cs nop WORD PTR [rax+rax*1+0x0]
  4011ac:	nop    DWORD PTR [rax+0x0]
  4011b0:	endbr64
  4011b4:	jmp    401140 <exit@plt+0x80>
  4011b6:	push   rbp
  4011b7:	mov    rbp,rsp
  4011ba:	sub    rsp,0x10
  4011be:	mov    rax,QWORD PTR fs:0x28
  4011c7:	mov    QWORD PTR [rbp-0x8],rax
  4011cb:	xor    eax,eax
  4011cd:	mov    rax,QWORD PTR [rip+0x2e9c]        # 404070 <stdin@GLIBC_2.2.5>
  4011d4:	mov    ecx,0x0
  4011d9:	mov    edx,0x2
  4011de:	mov    esi,0x0
  4011e3:	mov    rdi,rax
  4011e6:	call   4010a0 <setvbuf@plt>
  4011eb:	mov    rax,QWORD PTR [rip+0x2e6e]        # 404060 <stdout@GLIBC_2.2.5>
  4011f2:	mov    ecx,0x0
  4011f7:	mov    edx,0x2
  4011fc:	mov    esi,0x0
  401201:	mov    rdi,rax
  401204:	call   4010a0 <setvbuf@plt>
  401209:	mov    rax,QWORD PTR [rip+0x2e70]        # 404080 <stderr@GLIBC_2.2.5>
  401210:	mov    ecx,0x0
  401215:	mov    edx,0x2
  40121a:	mov    esi,0x0
  40121f:	mov    rdi,rax
  401222:	call   4010a0 <setvbuf@plt>
  401227:	nop
  401228:	mov    rax,QWORD PTR [rbp-0x8]
  40122c:	sub    rax,QWORD PTR fs:0x28
  401235:	je     40123c <exit@plt+0x17c>
  401237:	call   401050 <__stack_chk_fail@plt>
  40123c:	leave
  40123d:	ret
  40123e:	mov    rax,QWORD PTR fs:0x28
  401247:	mov    QWORD PTR [rbp-0x8],rax
  40124b:	xor    eax,eax
  40124d:	pop    rdi
  40124e:	ret
  40124f:	pop    rsi
  401250:	ret
  401251:	nop
  401252:	mov    rax,QWORD PTR [rbp-0x8]
  401256:	sub    rax,QWORD PTR fs:0x28
  40125f:	je     401266 <exit@plt+0x1a6>
  401261:	call   401050 <__stack_chk_fail@plt>
  401266:	ud2
  401268:	push   rbp
  401269:	mov    rbp,rsp
  40126c:	sub    rsp,0x70
  401270:	mov    DWORD PTR [rbp-0x64],edi
  401273:	mov    DWORD PTR [rbp-0x68],esi
  401276:	mov    rax,QWORD PTR fs:0x28
  40127f:	mov    QWORD PTR [rbp-0x8],rax
  401283:	xor    eax,eax
  401285:	cmp    DWORD PTR [rbp-0x64],0xdeadbeef
  40128c:	jne    401322 <exit@plt+0x262>
  401292:	cmp    DWORD PTR [rbp-0x68],0xcafebabe
  401299:	jne    401322 <exit@plt+0x262>
  40129f:	lea    rax,[rip+0xd62]        # 402008 <exit@plt+0xf48>
  4012a6:	mov    rdi,rax
  4012a9:	call   401030 <puts@plt>
  4012ae:	lea    rax,[rip+0xd7a]        # 40202f <exit@plt+0xf6f>
  4012b5:	mov    rsi,rax
  4012b8:	lea    rax,[rip+0xd72]        # 402031 <exit@plt+0xf71>
  4012bf:	mov    rdi,rax
  4012c2:	call   4010b0 <fopen@plt>
  4012c7:	mov    QWORD PTR [rbp-0x58],rax
  4012cb:	cmp    QWORD PTR [rbp-0x58],0x0
  4012d0:	jne    4012eb <exit@plt+0x22b>
  4012d2:	lea    rax,[rip+0xd67]        # 402040 <exit@plt+0xf80>
  4012d9:	mov    rdi,rax
  4012dc:	call   401030 <puts@plt>
  4012e1:	mov    edi,0x1
  4012e6:	call   4010c0 <exit@plt>
  4012eb:	mov    rdx,QWORD PTR [rbp-0x58]
  4012ef:	lea    rax,[rbp-0x50]
  4012f3:	mov    esi,0x40
  4012f8:	mov    rdi,rax
  4012fb:	call   401090 <fgets@plt>
  401300:	lea    rax,[rbp-0x50]
  401304:	mov    rdi,rax
  401307:	call   401030 <puts@plt>
  40130c:	mov    rax,QWORD PTR [rbp-0x58]
  401310:	mov    rdi,rax
  401313:	call   401040 <fclose@plt>
  401318:	mov    edi,0x0
  40131d:	call   4010c0 <exit@plt>
  401322:	lea    rax,[rip+0xd37]        # 402060 <exit@plt+0xfa0>
  401329:	mov    rdi,rax
  40132c:	call   401030 <puts@plt>
  401331:	nop
  401332:	mov    rax,QWORD PTR [rbp-0x8]
  401336:	sub    rax,QWORD PTR fs:0x28
  40133f:	je     401346 <exit@plt+0x286>
  401341:	call   401050 <__stack_chk_fail@plt>
  401346:	leave
  401347:	ret
  401348:	push   rbp
  401349:	mov    rbp,rsp
  40134c:	sub    rsp,0x30
  401350:	lea    rax,[rbp-0x20]
  401354:	mov    edx,0x20
  401359:	mov    esi,0x0
  40135e:	mov    rdi,rax
  401361:	call   401070 <memset@plt>
  401366:	lea    rax,[rip+0xd16]        # 402083 <exit@plt+0xfc3>
  40136d:	mov    rdi,rax
  401370:	mov    eax,0x0
  401375:	call   401060 <printf@plt>
  40137a:	mov    QWORD PTR [rbp-0x28],0x21
  401382:	mov    rdx,QWORD PTR [rbp-0x28]
  401386:	lea    rax,[rbp-0x20]
  40138a:	mov    rsi,rax
  40138d:	mov    edi,0x0
  401392:	call   401080 <read@plt>
  401397:	nop
  401398:	leave
  401399:	ret
  40139a:	push   rbp
  40139b:	mov    rbp,rsp
  40139e:	sub    rsp,0x50
  4013a2:	lea    rax,[rbp-0x50]
  4013a6:	mov    edx,0x50
  4013ab:	mov    esi,0x0
  4013b0:	mov    rdi,rax
  4013b3:	call   401070 <memset@plt>
  4013b8:	lea    rax,[rbp-0x50]
  4013bc:	mov    rsi,rax
  4013bf:	lea    rax,[rip+0xcd2]        # 402098 <exit@plt+0xfd8>
  4013c6:	mov    rdi,rax
  4013c9:	mov    eax,0x0
  4013ce:	call   401060 <printf@plt>
  4013d3:	lea    rax,[rip+0xce2]        # 4020bc <exit@plt+0xffc>
  4013da:	mov    rdi,rax
  4013dd:	mov    eax,0x0
  4013e2:	call   401060 <printf@plt>
  4013e7:	lea    rax,[rbp-0x50]
  4013eb:	mov    edx,0x50
  4013f0:	mov    rsi,rax
  4013f3:	mov    edi,0x0
  4013f8:	call   401080 <read@plt>
  4013fd:	mov    eax,0x0
  401402:	call   401348 <exit@plt+0x288>
  401407:	lea    rax,[rip+0xcc5]        # 4020d3 <exit@plt+0x1013>
  40140e:	mov    rdi,rax
  401411:	call   401030 <puts@plt>
  401416:	nop
  401417:	leave
  401418:	ret
  401419:	push   rbp
  40141a:	mov    rbp,rsp
  40141d:	sub    rsp,0x10
  401421:	mov    rax,QWORD PTR fs:0x28
  40142a:	mov    QWORD PTR [rbp-0x8],rax
  40142e:	xor    eax,eax
  401430:	mov    eax,0x0
  401435:	call   4011b6 <exit@plt+0xf6>
  40143a:	lea    rax,[rip+0xcaf]        # 4020f0 <exit@plt+0x1030>
  401441:	mov    rdi,rax
  401444:	call   401030 <puts@plt>
  401449:	mov    eax,0x0
  40144e:	call   40139a <exit@plt+0x2da>
  401453:	lea    rax,[rip+0xcc2]        # 40211c <exit@plt+0x105c>
  40145a:	mov    rdi,rax
  40145d:	call   401030 <puts@plt>
  401462:	mov    eax,0x0
  401467:	mov    rdx,QWORD PTR [rbp-0x8]
  40146b:	sub    rdx,QWORD PTR fs:0x28
  401474:	je     40147b <exit@plt+0x3bb>
  401476:	call   401050 <__stack_chk_fail@plt>
  40147b:	leave
  40147c:	ret

Disassembly of section .fini:

0000000000401480 <.fini>:
  401480:	sub    rsp,0x8
  401484:	add    rsp,0x8
  401488:	ret

Disassembly of section .rodata:

0000000000402000 <.rodata>:
  402000:	add    DWORD PTR [rax],eax
  402002:	add    al,BYTE PTR [rax]
  402004:	add    BYTE PTR [rax],al
  402006:	add    BYTE PTR [rax],al
  402008:	pop    rbx
  402009:	sub    ebx,DWORD PTR [rbp+0x20]
  40200c:	movsxd esp,DWORD PTR [r11+0x65]
  402010:	jae    402085 <exit@plt+0xfc5>
  402012:	and    BYTE PTR [rdi+0x72],al
  402015:	(bad)
  402016:	outs   dx,BYTE PTR ds:[rsi]
  402017:	je     40207e <exit@plt+0xfbe>
  402019:	and    DWORD PTR fs:[rax],esp
  40201c:	rex.W
  40201d:	gs jb  402085 <exit@plt+0xfc5>
  402020:	and    BYTE PTR [rcx+0x73],ch
  402023:	and    BYTE PTR [rcx+0x6f],bh
  402026:	jne    40209a <exit@plt+0xfda>
  402028:	and    BYTE PTR [rsi+0x6c],ah
  40202b:	(bad)
  40202c:	cmp    al,BYTE PTR [eax]
  40202f:	jb     402031 <exit@plt+0xf71>
  402031:	data16 ins BYTE PTR es:[rdi],dx
  402033:	(bad)
  402034:	addr32 cs je 4020b0 <exit@plt+0xff0>
  402038:	je     40203a <exit@plt+0xf7a>
  40203a:	add    BYTE PTR [rax],al
  40203c:	add    BYTE PTR [rax],al
  40203e:	add    BYTE PTR [rax],al
  402040:	pop    rbx
  402041:	sub    eax,0x6c66205d
  402046:	(bad)
  402047:	addr32 cs je 4020c3 <exit@plt+0x1003>
  40204b:	je     40206d <exit@plt+0xfad>
  40204d:	ins    DWORD PTR es:[rdi],dx
  40204e:	imul   esi,DWORD PTR [rbx+0x73],0x20676e69
  402055:	outs   dx,DWORD PTR ds:[rsi]
  402056:	outs   dx,BYTE PTR ds:[rsi]
  402057:	and    BYTE PTR [rbx+0x65],dh
  40205a:	jb     4020d2 <exit@plt+0x1012>
  40205c:	gs jb  40208d <exit@plt+0xfcd>
  40205f:	add    BYTE PTR [rbx+0x2d],bl
  402062:	pop    rbp
  402063:	and    BYTE PTR [rcx+0x75],al
  402066:	je     4020d0 <exit@plt+0x1010>
  402068:	outs   dx,BYTE PTR gs:[rsi]
  40206a:	je     4020d5 <exit@plt+0x1015>
  40206c:	movsxd esp,DWORD PTR [rcx+0x74]
  40206f:	imul   ebp,DWORD PTR [rdi+0x6e],0x6b6f7420
  402076:	outs   dx,BYTE PTR gs:[rsi]
  402078:	and    BYTE PTR [rbp+0x69],ch
  40207b:	jae    4020ea <exit@plt+0x102a>
  40207d:	(bad)
  40207e:	je     4020e3 <exit@plt+0x1023>
  402080:	push   0x6154002e
  402085:	addr32 imul ebp,DWORD PTR [esi+0x67],0x65706f20
  40208e:	jb     4020f1 <exit@plt+0x1031>
  402090:	je     402101 <exit@plt+0x1041>
  402092:	jb     4020ce <exit@plt+0x100e>
  402094:	and    BYTE PTR [rax],al
  402096:	add    BYTE PTR [rax],al
  402098:	pop    rbx
  402099:	sub    bl,BYTE PTR [rbp+0x20]
  40209c:	push   rdx
  40209d:	gs jo  40210f <exit@plt+0x104f>
  4020a0:	jb     402116 <exit@plt+0x1056>
  4020a2:	and    BYTE PTR [rdx+0x75],ah
  4020a5:	data16 data16 gs jb 4020ca <exit@plt+0x100a>
  4020aa:	(bad)
  4020ab:	ins    BYTE PTR es:[rdi],dx
  4020ac:	ins    BYTE PTR es:[rdi],dx
  4020ad:	outs   dx,DWORD PTR ds:[rsi]
  4020ae:	movsxd esp,DWORD PTR [rcx+0x74]
  4020b1:	gs and BYTE PTR fs:[rcx+0x74],ah
  4020b6:	cmp    ah,BYTE PTR [rax]
  4020b8:	and    eax,0x45000a70
  4020bd:	outs   dx,BYTE PTR ds:[rsi]
  4020be:	je     402125 <exit@plt+0x1065>
  4020c0:	jb     4020e2 <exit@plt+0x1022>
  4020c2:	jb     402129 <exit@plt+0x1069>
  4020c4:	jo     402135 <exit@plt+0x1075>
  4020c6:	jb     40213c <exit@plt+0x107c>
  4020c8:	and    BYTE PTR [rbx+0x75],dh
  4020cb:	ins    DWORD PTR es:[rdi],dx
  4020cc:	ins    DWORD PTR es:[rdi],dx
  4020cd:	(bad)
  4020ce:	jb     402149 <exit@plt+0x1089>
  4020d0:	cmp    ah,BYTE PTR [rax]
  4020d2:	add    BYTE PTR [rbx+0x2a],bl
  4020d5:	pop    rbp
  4020d6:	and    BYTE PTR [rax+0x72],dl
  4020d9:	outs   dx,DWORD PTR ds:[rsi]
  4020da:	movsxd esp,DWORD PTR [rbp+0x73]
  4020dd:	jae    402148 <exit@plt+0x1088>
  4020df:	outs   dx,BYTE PTR ds:[rsi]
  4020e0:	and    BYTE PTR [edx+0x65],dh
  4020e4:	jo     402155 <exit@plt+0x1095>
  4020e6:	jb     40215c <exit@plt+0x109c>
  4020e8:	cs cs cs add BYTE PTR [rax],al
  4020ed:	add    BYTE PTR [rax],al
  4020ef:	add    BYTE PTR [rip+0x53203d3d],bh        # 53605e32 <stderr@GLIBC_2.2.5+0x53201db2>
  4020f5:	movsxd esi,DWORD PTR gs:[rdi+rbp*2+0x72]
  4020fa:	and    BYTE PTR [rax],dh
  4020fc:	xor    DWORD PTR [rdx],edi
  4020fe:	and    BYTE PTR [rbp+0x61],cl
  402101:	imul   ebp,DWORD PTR [rsi+0x74],0x6e616e65
  402108:	movsxd esp,DWORD PTR [rbp+0x20]
  40210b:	rex.WR outs dx,DWORD PTR ds:[rsi]
  40210d:	and    BYTE PTR [ebp+eiz*2+0x72],dl
  402112:	ins    DWORD PTR es:[rdi],dx
  402113:	imul   ebp,DWORD PTR [rsi+0x61],0x3d3d206c
  40211a:	cmp    eax,0x5d2a5b00
  40211f:	and    BYTE PTR [rdi+rbp*2+0x67],cl
  402123:	and    BYTE PTR [rsi+0x69],ah
  402126:	outs   dx,BYTE PTR ds:[rsi]
  402127:	(bad)
  402128:	ins    BYTE PTR es:[rdi],dx
  402129:	imul   edi,DWORD PTR [rdx+0x65],0x45202e64
  402130:	js     40219b <exit@plt+0x10db>
  402132:	je     40219d <exit@plt+0x10dd>
  402134:	outs   dx,BYTE PTR ds:[rsi]
  402135:	addr32
  402136:	cs
	...

Disassembly of section .eh_frame_hdr:

0000000000402138 <.eh_frame_hdr>:
  402138:	add    DWORD PTR [rbx],ebx
  40213a:	add    edi,DWORD PTR [rbx]
  40213c:	push   rsp
  40213d:	add    BYTE PTR [rax],al
  40213f:	add    BYTE PTR [rcx],cl
  402141:	add    BYTE PTR [rax],al
  402143:	add    al,ch
  402145:	out    dx,al
  402146:	(bad)
  402147:	push   QWORD PTR [rax-0x68000000]
  40214d:	out    dx,eax
  40214e:	(bad)
  40214f:	push   QWORD PTR [rax+0x0]
  402152:	add    BYTE PTR [rax],al
  402154:	enter  0xffef,0xff
  402158:	pushf
  402159:	add    BYTE PTR [rax],al
  40215b:	add    BYTE PTR [rsi-0x10],bh
  40215e:	(bad)
  40215f:	call   (bad)
  402160:	fadd   DWORD PTR [rax]
  402162:	add    BYTE PTR [rax],al
  402164:	(bad)
  402165:	int1
  402166:	(bad)
  402167:	(bad)
  402168:	clc
  402169:	add    BYTE PTR [rax],al
  40216b:	add    BYTE PTR [rax],dh
  40216d:	int1
  40216e:	(bad)
  40216f:	dec    DWORD PTR [rcx+rax*1]
  402172:	add    BYTE PTR [rax],al
  402174:	adc    dl,dh
  402176:	(bad)
  402177:	jmp    FWORD PTR [rcx+rax*1]
  40217a:	add    BYTE PTR [rax],al
  40217c:	(bad)  {k7}{z}
  402181:	add    DWORD PTR [rax],eax
  402183:	add    cl,ah
  402185:	repnz (bad)
  402187:	jmp    FWORD PTR [rcx+rax*1+0x0]
	...

Disassembly of section .eh_frame:

0000000000402190 <.eh_frame>:
  402190:	adc    al,0x0
  402192:	add    BYTE PTR [rax],al
  402194:	add    BYTE PTR [rax],al
  402196:	add    BYTE PTR [rax],al
  402198:	add    DWORD PTR [rdx+0x52],edi
  40219b:	add    BYTE PTR [rcx],al
  40219d:	js     4021af <exit@plt+0x10ef>
  40219f:	add    DWORD PTR [rbx],ebx
  4021a1:	or     al,0x7
  4021a3:	or     BYTE PTR [rax+0x10100701],dl
  4021a9:	add    BYTE PTR [rax],al
  4021ab:	add    BYTE PTR [rax+rax*1],bl
  4021ae:	add    BYTE PTR [rax],al
  4021b0:	and    bh,ch
  4021b2:	(bad)
  4021b3:	jmp    QWORD PTR [rdx]
  4021b5:	add    BYTE PTR [rax],al
  4021b7:	add    BYTE PTR [rax],al
  4021b9:	add    BYTE PTR [rax],al
  4021bb:	add    BYTE PTR [rax+rax*1],dl
  4021be:	add    BYTE PTR [rax],al
  4021c0:	add    BYTE PTR [rax],al
  4021c2:	add    BYTE PTR [rax],al
  4021c4:	add    DWORD PTR [rdx+0x52],edi
  4021c7:	add    BYTE PTR [rcx],al
  4021c9:	js     4021db <exit@plt+0x111b>
  4021cb:	add    DWORD PTR [rbx],ebx
  4021cd:	or     al,0x7
  4021cf:	or     BYTE PTR [rax+0x10000001],dl
  4021d5:	add    BYTE PTR [rax],al
  4021d7:	add    BYTE PTR [rax+rax*1],bl
  4021da:	add    BYTE PTR [rax],al
  4021dc:	and    al,0xef
  4021de:	(bad)
  4021df:	inc    DWORD PTR [rcx]
  4021e1:	add    BYTE PTR [rax],al
  4021e3:	add    BYTE PTR [rax],al
  4021e5:	add    BYTE PTR [rax],al
  4021e7:	add    BYTE PTR [rax+rax*1],ah
  4021ea:	add    BYTE PTR [rax],al
  4021ec:	xor    BYTE PTR [rax],al
  4021ee:	add    BYTE PTR [rax],al
  4021f0:	xor    dh,ch
  4021f2:	(bad)
  4021f3:	push   QWORD PTR [rax+0x0]
  4021f9:	(bad)
  4021fa:	adc    BYTE PTR [rsi+0xe],al
  4021fd:	sbb    BYTE PTR [rdx+0xf],cl
  402200:	or     esi,DWORD PTR [rdi+0x8]
  402203:	add    BYTE PTR [rax],0x3f
  402206:	sbb    bh,BYTE PTR [rbx]
  402208:	sub    dh,BYTE PTR [rbx]
  40220a:	and    al,0x22
  40220c:	add    BYTE PTR [rax],al
  40220e:	add    BYTE PTR [rax],al
  402210:	sbb    al,0x0
  402212:	add    BYTE PTR [rax],al
  402214:	pop    rax
  402215:	add    BYTE PTR [rax],al
  402217:	add    BYTE PTR [rsi-0x77000011],bl
  40221d:	add    BYTE PTR [rax],al
  40221f:	add    BYTE PTR [rax],al
  402221:	rex.B (bad)
  402223:	adc    BYTE PTR [rsi+0x60d4302],al
  402229:	add    al,BYTE PTR [rbx+0x8070c]
  40222f:	add    BYTE PTR [rax],dl
  402231:	add    BYTE PTR [rax],al
  402233:	add    BYTE PTR [rax+0x0],bh
  402236:	add    BYTE PTR [rax],al
  402238:	(bad)
  402239:	lock (bad)
  40223b:	jmp    FWORD PTR [rdx]
  40223d:	add    BYTE PTR [rax],al
  40223f:	add    BYTE PTR [rax],al
  402241:	add    BYTE PTR [rax],al
  402243:	add    BYTE PTR [rax+rax*1],bl
  402246:	add    BYTE PTR [rax],al
  402248:	mov    WORD PTR [rax],es
  40224a:	add    BYTE PTR [rax],al
  40224c:	sbb    al,0xf0
  40224e:	(bad)
  40224f:	jmp    rax
  402251:	add    BYTE PTR [rax],al
  402253:	add    BYTE PTR [rax],al
  402255:	rex.B (bad)
  402257:	adc    BYTE PTR [rsi+0x60d4302],al
  40225d:	add    bl,bl
  40225f:	or     al,0x7
  402261:	or     BYTE PTR [rax],al
  402263:	add    BYTE PTR [rax+rax*1],bl
  402266:	add    BYTE PTR [rax],al
  402268:	lods   al,BYTE PTR ds:[rsi]
  402269:	add    BYTE PTR [rax],al
  40226b:	add    ah,bl
  40226d:	lock (bad)
  40226f:	call   QWORD PTR [rdx+0x0]
  402272:	add    BYTE PTR [rax],al
  402274:	add    BYTE PTR [rcx+0xe],al
  402277:	adc    BYTE PTR [rsi+0x60d4302],al
  40227d:	add    cl,BYTE PTR [rbp+0xc]
  402280:	(bad)
  402281:	or     BYTE PTR [rax],al
  402283:	add    BYTE PTR [rax+rax*1],bl
  402286:	add    BYTE PTR [rax],al
  402288:	int3
  402289:	add    BYTE PTR [rax],al
  40228b:	add    BYTE PTR [rsi],cl
  40228d:	int1
  40228e:	(bad)
  40228f:	(bad)
  402290:	jg     402292 <exit@plt+0x11d2>
  402292:	add    BYTE PTR [rax],al
  402294:	add    BYTE PTR [rcx+0xe],al
  402297:	adc    BYTE PTR [rsi+0x60d4302],al
  40229d:	add    bh,BYTE PTR [rdx+0xc]
  4022a0:	(bad)
  4022a1:	or     BYTE PTR [rax],al
  4022a3:	add    BYTE PTR [rax+rax*1],bl
  4022a6:	add    BYTE PTR [rax],al
  4022a8:	in     al,dx
  4022a9:	add    BYTE PTR [rax],al
  4022ab:	add    BYTE PTR [rbp-0xf],ch
  4022ae:	(bad)
  4022af:	jmp    QWORD PTR [rax+rax*1+0x0]
  4022b3:	add    BYTE PTR [rax],al
  4022b5:	rex.B (bad)
  4022b7:	adc    BYTE PTR [rsi+0x60d4302],al
  4022bd:	add    bl,BYTE PTR [rdi+0xc]
  4022c0:	(bad)
  4022c1:	or     BYTE PTR [rax],al
  4022c3:	add    BYTE PTR [rax],al
  4022c5:	add    BYTE PTR [rax],al
	...

Disassembly of section .init_array:

0000000000403df8 <.init_array>:
  403df8:	mov    al,0x11
  403dfa:	rex add BYTE PTR [rax],al
  403dfd:	add    BYTE PTR [rax],al
	...

Disassembly of section .fini_array:

0000000000403e00 <.fini_array>:
  403e00:	adc    BYTE PTR [rcx],0x40
  403e03:	add    BYTE PTR [rax],al
  403e05:	add    BYTE PTR [rax],al
	...

Disassembly of section .dynamic:

0000000000403e08 <.dynamic>:
  403e08:	add    DWORD PTR [rax],eax
  403e0a:	add    BYTE PTR [rax],al
  403e0c:	add    BYTE PTR [rax],al
  403e0e:	add    BYTE PTR [rax],al
  403e10:	jo     403e12 <exit@plt+0x2d52>
  403e12:	add    BYTE PTR [rax],al
  403e14:	add    BYTE PTR [rax],al
  403e16:	add    BYTE PTR [rax],al
  403e18:	or     al,0x0
  403e1a:	add    BYTE PTR [rax],al
  403e1c:	add    BYTE PTR [rax],al
  403e1e:	add    BYTE PTR [rax],al
  403e20:	add    BYTE PTR [rax],dl
  403e22:	rex add BYTE PTR [rax],al
  403e25:	add    BYTE PTR [rax],al
  403e27:	add    BYTE PTR [rip+0x0],cl        # 403e2d <exit@plt+0x2d6d>
  403e2d:	add    BYTE PTR [rax],al
  403e2f:	add    BYTE PTR [rax+0x4014],al
  403e35:	add    BYTE PTR [rax],al
  403e37:	add    BYTE PTR [rcx],bl
  403e39:	add    BYTE PTR [rax],al
  403e3b:	add    BYTE PTR [rax],al
  403e3d:	add    BYTE PTR [rax],al
  403e3f:	add    al,bh
  403e41:	cmp    eax,0x40
  403e46:	add    BYTE PTR [rax],al
  403e48:	sbb    eax,DWORD PTR [rax]
  403e4a:	add    BYTE PTR [rax],al
  403e4c:	add    BYTE PTR [rax],al
  403e4e:	add    BYTE PTR [rax],al
  403e50:	or     BYTE PTR [rax],al
  403e52:	add    BYTE PTR [rax],al
  403e54:	add    BYTE PTR [rax],al
  403e56:	add    BYTE PTR [rax],al
  403e58:	sbb    al,BYTE PTR [rax]
  403e5a:	add    BYTE PTR [rax],al
  403e5c:	add    BYTE PTR [rax],al
  403e5e:	add    BYTE PTR [rax],al
  403e60:	add    BYTE PTR [rsi],bh
  403e62:	rex add BYTE PTR [rax],al
  403e65:	add    BYTE PTR [rax],al
  403e67:	add    BYTE PTR [rax+rax*1],bl
  403e6a:	add    BYTE PTR [rax],al
  403e6c:	add    BYTE PTR [rax],al
  403e6e:	add    BYTE PTR [rax],al
  403e70:	or     BYTE PTR [rax],al
  403e72:	add    BYTE PTR [rax],al
  403e74:	add    BYTE PTR [rax],al
  403e76:	add    BYTE PTR [rax],al
  403e78:	cmc
  403e79:	(bad)
  403e7a:	jmp    FWORD PTR [rdi+0x0]
  403e7d:	add    BYTE PTR [rax],al
  403e7f:	add    BYTE PTR [rax+0x4003],ah
  403e85:	add    BYTE PTR [rax],al
  403e87:	add    BYTE PTR [rip+0x0],al        # 403e8d <exit@plt+0x2dcd>
  403e8d:	add    BYTE PTR [rax],al
  403e8f:	add    BYTE PTR [rax+0x5],dl
  403e92:	rex add BYTE PTR [rax],al
  403e95:	add    BYTE PTR [rax],al
  403e97:	add    BYTE PTR [rsi],al
  403e99:	add    BYTE PTR [rax],al
  403e9b:	add    BYTE PTR [rax],al
  403e9d:	add    BYTE PTR [rax],al
  403e9f:	add    al,dl
  403ea1:	add    eax,DWORD PTR [rax+0x0]
  403ea4:	add    BYTE PTR [rax],al
  403ea6:	add    BYTE PTR [rax],al
  403ea8:	or     al,BYTE PTR [rax]
  403eaa:	add    BYTE PTR [rax],al
  403eac:	add    BYTE PTR [rax],al
  403eae:	add    BYTE PTR [rax],al
  403eb0:	stos   BYTE PTR es:[rdi],al
  403eb1:	add    BYTE PTR [rax],al
  403eb3:	add    BYTE PTR [rax],al
  403eb5:	add    BYTE PTR [rax],al
  403eb7:	add    BYTE PTR [rbx],cl
  403eb9:	add    BYTE PTR [rax],al
  403ebb:	add    BYTE PTR [rax],al
  403ebd:	add    BYTE PTR [rax],al
  403ebf:	add    BYTE PTR [rax],bl
  403ec1:	add    BYTE PTR [rax],al
  403ec3:	add    BYTE PTR [rax],al
  403ec5:	add    BYTE PTR [rax],al
  403ec7:	add    BYTE PTR [rip+0x0],dl        # 403ecd <exit@plt+0x2e0d>
	...
  403ed5:	add    BYTE PTR [rax],al
  403ed7:	add    BYTE PTR [rbx],al
  403ed9:	add    BYTE PTR [rax],al
  403edb:	add    BYTE PTR [rax],al
  403edd:	add    BYTE PTR [rax],al
  403edf:	add    al,ch
  403ee1:	(bad)
  403ee2:	rex add BYTE PTR [rax],al
  403ee5:	add    BYTE PTR [rax],al
  403ee7:	add    BYTE PTR [rdx],al
  403ee9:	add    BYTE PTR [rax],al
  403eeb:	add    BYTE PTR [rax],al
  403eed:	add    BYTE PTR [rax],al
  403eef:	add    al,dh
  403ef1:	add    BYTE PTR [rax],al
  403ef3:	add    BYTE PTR [rax],al
  403ef5:	add    BYTE PTR [rax],al
  403ef7:	add    BYTE PTR [rax+rax*1],dl
  403efa:	add    BYTE PTR [rax],al
  403efc:	add    BYTE PTR [rax],al
  403efe:	add    BYTE PTR [rax],al
  403f00:	(bad)
  403f01:	add    BYTE PTR [rax],al
  403f03:	add    BYTE PTR [rax],al
  403f05:	add    BYTE PTR [rax],al
  403f07:	add    BYTE PTR [rdi],dl
  403f09:	add    BYTE PTR [rax],al
  403f0b:	add    BYTE PTR [rax],al
  403f0d:	add    BYTE PTR [rax],al
  403f0f:	add    al,bl
  403f11:	(bad)
  403f12:	rex add BYTE PTR [rax],al
  403f15:	add    BYTE PTR [rax],al
  403f17:	add    BYTE PTR [rdi],al
  403f19:	add    BYTE PTR [rax],al
  403f1b:	add    BYTE PTR [rax],al
  403f1d:	add    BYTE PTR [rax],al
  403f1f:	add    BYTE PTR [rax+0x6],ah
  403f22:	rex add BYTE PTR [rax],al
  403f25:	add    BYTE PTR [rax],al
  403f27:	add    BYTE PTR [rax],cl
  403f29:	add    BYTE PTR [rax],al
  403f2b:	add    BYTE PTR [rax],al
  403f2d:	add    BYTE PTR [rax],al
  403f2f:	add    BYTE PTR [rax+0x0],bh
  403f32:	add    BYTE PTR [rax],al
  403f34:	add    BYTE PTR [rax],al
  403f36:	add    BYTE PTR [rax],al
  403f38:	or     DWORD PTR [rax],eax
  403f3a:	add    BYTE PTR [rax],al
  403f3c:	add    BYTE PTR [rax],al
  403f3e:	add    BYTE PTR [rax],al
  403f40:	sbb    BYTE PTR [rax],al
  403f42:	add    BYTE PTR [rax],al
  403f44:	add    BYTE PTR [rax],al
  403f46:	add    BYTE PTR [rax],al
  403f48:	(bad)
  403f49:	(bad)
  403f4a:	jmp    FWORD PTR [rdi+0x0]
  403f4d:	add    BYTE PTR [rax],al
  403f4f:	add    BYTE PTR [rax],ah
  403f51:	(bad)
  403f52:	rex add BYTE PTR [rax],al
  403f55:	add    BYTE PTR [rax],al
  403f57:	add    bh,bh
  403f59:	(bad)
  403f5a:	jmp    FWORD PTR [rdi+0x0]
  403f5d:	add    BYTE PTR [rax],al
  403f5f:	add    BYTE PTR [rcx],al
  403f61:	add    BYTE PTR [rax],al
  403f63:	add    BYTE PTR [rax],al
  403f65:	add    BYTE PTR [rax],al
  403f67:	add    al,dh
  403f69:	(bad)
  403f6a:	jmp    FWORD PTR [rdi+0x0]
  403f6d:	add    BYTE PTR [rax],al
  403f6f:	add    dl,bh
  403f71:	add    eax,0x40
	...

Disassembly of section .got:

0000000000403fd8 <.got>:
	...

Disassembly of section .got.plt:

0000000000403fe8 <.got.plt>:
  403fe8:	or     BYTE PTR [rsi],bh
  403fea:	rex add BYTE PTR [rax],al
	...
  403ffd:	add    BYTE PTR [rax],al
  403fff:	add    BYTE PTR [rsi],dh
  404001:	adc    BYTE PTR [rax+0x0],al
  404004:	add    BYTE PTR [rax],al
  404006:	add    BYTE PTR [rax],al
  404008:	rex.RX adc BYTE PTR [rax+0x0],r8b
  40400c:	add    BYTE PTR [rax],al
  40400e:	add    BYTE PTR [rax],al
  404010:	push   rsi
  404011:	adc    BYTE PTR [rax+0x0],al
  404014:	add    BYTE PTR [rax],al
  404016:	add    BYTE PTR [rax],al
  404018:	data16 adc BYTE PTR [rax+0x0],al
  40401c:	add    BYTE PTR [rax],al
  40401e:	add    BYTE PTR [rax],al
  404020:	jbe    404032 <exit@plt+0x2f72>
  404022:	rex add BYTE PTR [rax],al
  404025:	add    BYTE PTR [rax],al
  404027:	add    BYTE PTR [rsi+0x4010],al
  40402d:	add    BYTE PTR [rax],al
  40402f:	add    BYTE PTR [rsi+0x4010],dl
  404035:	add    BYTE PTR [rax],al
  404037:	add    BYTE PTR [rsi+0x4010],ah
  40403d:	add    BYTE PTR [rax],al
  40403f:	add    BYTE PTR [rsi+0x4010],dh
  404045:	add    BYTE PTR [rax],al
  404047:	add    dh,al
  404049:	adc    BYTE PTR [rax+0x0],al
  40404c:	add    BYTE PTR [rax],al
	...

Disassembly of section .data:

0000000000404050 <.data>:
	...

Disassembly of section .comment:

0000000000000000 <.comment>:
   0:	rex.RXB
   1:	rex.XB
   2:	rex.XB cmp spl,BYTE PTR [r8]
   5:	sub    BYTE PTR [rbp+riz*2+0x62],al
   9:	imul   esp,DWORD PTR [rcx+0x6e],0x2e323120
  10:	xor    ch,BYTE PTR [rsi]
  12:	xor    BYTE PTR [rip+0x642b3431],ch        # 642b3449 <stderr@GLIBC_2.2.5+0x63eaf3c9>
  18:	(bad)
  1e:	sub    DWORD PTR [rax],esp
  20:	xor    DWORD PTR [rdx],esi
  22:	cs xor ch,BYTE PTR [rsi]
  25:	xor    BYTE PTR [rax],al
