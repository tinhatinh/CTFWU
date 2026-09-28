
files/robocall:     file format elf64-x86-64


Disassembly of section .text:

0000000000001120 <_start>:
    1120:	f3 0f 1e fa          	endbr64
    1124:	31 ed                	xor    ebp,ebp
    1126:	49 89 d1             	mov    r9,rdx
    1129:	5e                   	pop    rsi
    112a:	48 89 e2             	mov    rdx,rsp
    112d:	48 83 e4 f0          	and    rsp,0xfffffffffffffff0
    1131:	50                   	push   rax
    1132:	54                   	push   rsp
    1133:	45 31 c0             	xor    r8d,r8d
    1136:	31 c9                	xor    ecx,ecx
    1138:	48 8d 3d ce 08 00 00 	lea    rdi,[rip+0x8ce]        # 1a0d <main>
    113f:	ff 15 b3 63 00 00    	call   QWORD PTR [rip+0x63b3]        # 74f8 <__libc_start_main@GLIBC_2.34>
    1145:	f4                   	hlt
    1146:	66 2e 0f 1f 84 00 00 	cs nop WORD PTR [rax+rax*1+0x0]
    114d:	00 00 00 

0000000000001150 <deregister_tm_clones>:
    1150:	48 8d 3d e1 63 00 00 	lea    rdi,[rip+0x63e1]        # 7538 <__TMC_END__>
    1157:	48 8d 05 da 63 00 00 	lea    rax,[rip+0x63da]        # 7538 <__TMC_END__>
    115e:	48 39 f8             	cmp    rax,rdi
    1161:	74 15                	je     1178 <deregister_tm_clones+0x28>
    1163:	48 8b 05 96 63 00 00 	mov    rax,QWORD PTR [rip+0x6396]        # 7500 <_ITM_deregisterTMCloneTable@Base>
    116a:	48 85 c0             	test   rax,rax
    116d:	74 09                	je     1178 <deregister_tm_clones+0x28>
    116f:	ff e0                	jmp    rax
    1171:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]
    1178:	c3                   	ret
    1179:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]

0000000000001180 <register_tm_clones>:
    1180:	48 8d 3d b1 63 00 00 	lea    rdi,[rip+0x63b1]        # 7538 <__TMC_END__>
    1187:	48 8d 35 aa 63 00 00 	lea    rsi,[rip+0x63aa]        # 7538 <__TMC_END__>
    118e:	48 29 fe             	sub    rsi,rdi
    1191:	48 89 f0             	mov    rax,rsi
    1194:	48 c1 ee 3f          	shr    rsi,0x3f
    1198:	48 c1 f8 03          	sar    rax,0x3
    119c:	48 01 c6             	add    rsi,rax
    119f:	48 d1 fe             	sar    rsi,1
    11a2:	74 14                	je     11b8 <register_tm_clones+0x38>
    11a4:	48 8b 05 65 63 00 00 	mov    rax,QWORD PTR [rip+0x6365]        # 7510 <_ITM_registerTMCloneTable@Base>
    11ab:	48 85 c0             	test   rax,rax
    11ae:	74 08                	je     11b8 <register_tm_clones+0x38>
    11b0:	ff e0                	jmp    rax
    11b2:	66 0f 1f 44 00 00    	nop    WORD PTR [rax+rax*1+0x0]
    11b8:	c3                   	ret
    11b9:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]

00000000000011c0 <__do_global_dtors_aux>:
    11c0:	f3 0f 1e fa          	endbr64
    11c4:	80 3d 9d 63 00 00 00 	cmp    BYTE PTR [rip+0x639d],0x0        # 7568 <completed.0>
    11cb:	75 2b                	jne    11f8 <__do_global_dtors_aux+0x38>
    11cd:	55                   	push   rbp
    11ce:	48 83 3d 42 63 00 00 	cmp    QWORD PTR [rip+0x6342],0x0        # 7518 <__cxa_finalize@GLIBC_2.2.5>
    11d5:	00 
    11d6:	48 89 e5             	mov    rbp,rsp
    11d9:	74 0c                	je     11e7 <__do_global_dtors_aux+0x27>
    11db:	48 8b 3d 46 63 00 00 	mov    rdi,QWORD PTR [rip+0x6346]        # 7528 <__dso_handle>
    11e2:	e8 b9 fe ff ff       	call   10a0 <__cxa_finalize@plt>
    11e7:	e8 64 ff ff ff       	call   1150 <deregister_tm_clones>
    11ec:	c6 05 75 63 00 00 01 	mov    BYTE PTR [rip+0x6375],0x1        # 7568 <completed.0>
    11f3:	5d                   	pop    rbp
    11f4:	c3                   	ret
    11f5:	0f 1f 00             	nop    DWORD PTR [rax]
    11f8:	c3                   	ret
    11f9:	0f 1f 80 00 00 00 00 	nop    DWORD PTR [rax+0x0]

0000000000001200 <frame_dummy>:
    1200:	f3 0f 1e fa          	endbr64
    1204:	e9 77 ff ff ff       	jmp    1180 <register_tm_clones>

0000000000001209 <raw_print>:
    1209:	f3 0f 1e fa          	endbr64
    120d:	55                   	push   rbp
    120e:	48 89 e5             	mov    rbp,rsp
    1211:	48 83 ec 20          	sub    rsp,0x20
    1215:	48 89 7d e8          	mov    QWORD PTR [rbp-0x18],rdi
    1219:	48 c7 45 f8 00 00 00 	mov    QWORD PTR [rbp-0x8],0x0
    1220:	00 
    1221:	eb 05                	jmp    1228 <raw_print+0x1f>
    1223:	48 83 45 f8 01       	add    QWORD PTR [rbp-0x8],0x1
    1228:	48 8b 55 f8          	mov    rdx,QWORD PTR [rbp-0x8]
    122c:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1230:	48 01 d0             	add    rax,rdx
    1233:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    1236:	84 c0                	test   al,al
    1238:	75 e9                	jne    1223 <raw_print+0x1a>
    123a:	48 83 7d f8 00       	cmp    QWORD PTR [rbp-0x8],0x0
    123f:	74 15                	je     1256 <raw_print+0x4d>
    1241:	48 8b 55 f8          	mov    rdx,QWORD PTR [rbp-0x8]
    1245:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1249:	48 89 c6             	mov    rsi,rax
    124c:	bf 01 00 00 00       	mov    edi,0x1
    1251:	e8 6a fe ff ff       	call   10c0 <write@plt>
    1256:	90                   	nop
    1257:	c9                   	leave
    1258:	c3                   	ret

0000000000001259 <raw_eprint>:
    1259:	f3 0f 1e fa          	endbr64
    125d:	55                   	push   rbp
    125e:	48 89 e5             	mov    rbp,rsp
    1261:	48 83 ec 20          	sub    rsp,0x20
    1265:	48 89 7d e8          	mov    QWORD PTR [rbp-0x18],rdi
    1269:	48 c7 45 f8 00 00 00 	mov    QWORD PTR [rbp-0x8],0x0
    1270:	00 
    1271:	eb 05                	jmp    1278 <raw_eprint+0x1f>
    1273:	48 83 45 f8 01       	add    QWORD PTR [rbp-0x8],0x1
    1278:	48 8b 55 f8          	mov    rdx,QWORD PTR [rbp-0x8]
    127c:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1280:	48 01 d0             	add    rax,rdx
    1283:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    1286:	84 c0                	test   al,al
    1288:	75 e9                	jne    1273 <raw_eprint+0x1a>
    128a:	48 83 7d f8 00       	cmp    QWORD PTR [rbp-0x8],0x0
    128f:	74 15                	je     12a6 <raw_eprint+0x4d>
    1291:	48 8b 55 f8          	mov    rdx,QWORD PTR [rbp-0x8]
    1295:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1299:	48 89 c6             	mov    rsi,rax
    129c:	bf 02 00 00 00       	mov    edi,0x2
    12a1:	e8 1a fe ff ff       	call   10c0 <write@plt>
    12a6:	90                   	nop
    12a7:	c9                   	leave
    12a8:	c3                   	ret

00000000000012a9 <raw_print_int>:
    12a9:	f3 0f 1e fa          	endbr64
    12ad:	55                   	push   rbp
    12ae:	48 89 e5             	mov    rbp,rsp
    12b1:	48 83 ec 50          	sub    rsp,0x50
    12b5:	89 7d bc             	mov    DWORD PTR [rbp-0x44],edi
    12b8:	c7 45 fc 00 00 00 00 	mov    DWORD PTR [rbp-0x4],0x0
    12bf:	c7 45 f8 00 00 00 00 	mov    DWORD PTR [rbp-0x8],0x0
    12c6:	83 7d bc 00          	cmp    DWORD PTR [rbp-0x44],0x0
    12ca:	79 1a                	jns    12e6 <raw_print_int+0x3d>
    12cc:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    12cf:	8d 50 01             	lea    edx,[rax+0x1]
    12d2:	89 55 f8             	mov    DWORD PTR [rbp-0x8],edx
    12d5:	48 98                	cdqe
    12d7:	c6 44 05 c0 2d       	mov    BYTE PTR [rbp+rax*1-0x40],0x2d
    12dc:	8b 45 bc             	mov    eax,DWORD PTR [rbp-0x44]
    12df:	f7 d8                	neg    eax
    12e1:	89 45 f4             	mov    DWORD PTR [rbp-0xc],eax
    12e4:	eb 06                	jmp    12ec <raw_print_int+0x43>
    12e6:	8b 45 bc             	mov    eax,DWORD PTR [rbp-0x44]
    12e9:	89 45 f4             	mov    DWORD PTR [rbp-0xc],eax
    12ec:	83 7d f4 00          	cmp    DWORD PTR [rbp-0xc],0x0
    12f0:	75 64                	jne    1356 <raw_print_int+0xad>
    12f2:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    12f5:	8d 50 01             	lea    edx,[rax+0x1]
    12f8:	89 55 fc             	mov    DWORD PTR [rbp-0x4],edx
    12fb:	48 98                	cdqe
    12fd:	c6 44 05 e0 30       	mov    BYTE PTR [rbp+rax*1-0x20],0x30
    1302:	eb 52                	jmp    1356 <raw_print_int+0xad>
    1304:	8b 4d f4             	mov    ecx,DWORD PTR [rbp-0xc]
    1307:	89 ca                	mov    edx,ecx
    1309:	b8 cd cc cc cc       	mov    eax,0xcccccccd
    130e:	48 0f af c2          	imul   rax,rdx
    1312:	48 c1 e8 20          	shr    rax,0x20
    1316:	89 c2                	mov    edx,eax
    1318:	c1 ea 03             	shr    edx,0x3
    131b:	89 d0                	mov    eax,edx
    131d:	c1 e0 02             	shl    eax,0x2
    1320:	01 d0                	add    eax,edx
    1322:	01 c0                	add    eax,eax
    1324:	29 c1                	sub    ecx,eax
    1326:	89 ca                	mov    edx,ecx
    1328:	89 d0                	mov    eax,edx
    132a:	8d 48 30             	lea    ecx,[rax+0x30]
    132d:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1330:	8d 50 01             	lea    edx,[rax+0x1]
    1333:	89 55 fc             	mov    DWORD PTR [rbp-0x4],edx
    1336:	89 ca                	mov    edx,ecx
    1338:	48 98                	cdqe
    133a:	88 54 05 e0          	mov    BYTE PTR [rbp+rax*1-0x20],dl
    133e:	8b 45 f4             	mov    eax,DWORD PTR [rbp-0xc]
    1341:	89 c2                	mov    edx,eax
    1343:	b8 cd cc cc cc       	mov    eax,0xcccccccd
    1348:	48 0f af c2          	imul   rax,rdx
    134c:	48 c1 e8 20          	shr    rax,0x20
    1350:	c1 e8 03             	shr    eax,0x3
    1353:	89 45 f4             	mov    DWORD PTR [rbp-0xc],eax
    1356:	83 7d f4 00          	cmp    DWORD PTR [rbp-0xc],0x0
    135a:	75 a8                	jne    1304 <raw_print_int+0x5b>
    135c:	eb 1e                	jmp    137c <raw_print_int+0xd3>
    135e:	83 6d fc 01          	sub    DWORD PTR [rbp-0x4],0x1
    1362:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    1365:	8d 50 01             	lea    edx,[rax+0x1]
    1368:	89 55 f8             	mov    DWORD PTR [rbp-0x8],edx
    136b:	8b 55 fc             	mov    edx,DWORD PTR [rbp-0x4]
    136e:	48 63 d2             	movsxd rdx,edx
    1371:	0f b6 54 15 e0       	movzx  edx,BYTE PTR [rbp+rdx*1-0x20]
    1376:	48 98                	cdqe
    1378:	88 54 05 c0          	mov    BYTE PTR [rbp+rax*1-0x40],dl
    137c:	83 7d fc 00          	cmp    DWORD PTR [rbp-0x4],0x0
    1380:	75 dc                	jne    135e <raw_print_int+0xb5>
    1382:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    1385:	48 63 d0             	movsxd rdx,eax
    1388:	48 8d 45 c0          	lea    rax,[rbp-0x40]
    138c:	48 89 c6             	mov    rsi,rax
    138f:	bf 01 00 00 00       	mov    edi,0x1
    1394:	e8 27 fd ff ff       	call   10c0 <write@plt>
    1399:	90                   	nop
    139a:	c9                   	leave
    139b:	c3                   	ret

000000000000139c <raw_readline>:
    139c:	f3 0f 1e fa          	endbr64
    13a0:	55                   	push   rbp
    13a1:	48 89 e5             	mov    rbp,rsp
    13a4:	48 83 ec 30          	sub    rsp,0x30
    13a8:	48 89 7d d8          	mov    QWORD PTR [rbp-0x28],rdi
    13ac:	89 75 d4             	mov    DWORD PTR [rbp-0x2c],esi
    13af:	c7 45 fc 00 00 00 00 	mov    DWORD PTR [rbp-0x4],0x0
    13b6:	eb 52                	jmp    140a <raw_readline+0x6e>
    13b8:	48 8d 45 ef          	lea    rax,[rbp-0x11]
    13bc:	ba 01 00 00 00       	mov    edx,0x1
    13c1:	48 89 c6             	mov    rsi,rax
    13c4:	bf 00 00 00 00       	mov    edi,0x0
    13c9:	e8 22 fd ff ff       	call   10f0 <read@plt>
    13ce:	48 89 45 f0          	mov    QWORD PTR [rbp-0x10],rax
    13d2:	48 83 7d f0 00       	cmp    QWORD PTR [rbp-0x10],0x0
    13d7:	7f 10                	jg     13e9 <raw_readline+0x4d>
    13d9:	83 7d fc 00          	cmp    DWORD PTR [rbp-0x4],0x0
    13dd:	75 38                	jne    1417 <raw_readline+0x7b>
    13df:	bf 00 00 00 00       	mov    edi,0x0
    13e4:	e8 c7 fc ff ff       	call   10b0 <_exit@plt>
    13e9:	0f b6 45 ef          	movzx  eax,BYTE PTR [rbp-0x11]
    13ed:	3c 0a                	cmp    al,0xa
    13ef:	74 29                	je     141a <raw_readline+0x7e>
    13f1:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    13f4:	8d 50 01             	lea    edx,[rax+0x1]
    13f7:	89 55 fc             	mov    DWORD PTR [rbp-0x4],edx
    13fa:	48 63 d0             	movsxd rdx,eax
    13fd:	48 8b 45 d8          	mov    rax,QWORD PTR [rbp-0x28]
    1401:	48 01 c2             	add    rdx,rax
    1404:	0f b6 45 ef          	movzx  eax,BYTE PTR [rbp-0x11]
    1408:	88 02                	mov    BYTE PTR [rdx],al
    140a:	8b 45 d4             	mov    eax,DWORD PTR [rbp-0x2c]
    140d:	83 e8 01             	sub    eax,0x1
    1410:	39 45 fc             	cmp    DWORD PTR [rbp-0x4],eax
    1413:	7c a3                	jl     13b8 <raw_readline+0x1c>
    1415:	eb 04                	jmp    141b <raw_readline+0x7f>
    1417:	90                   	nop
    1418:	eb 01                	jmp    141b <raw_readline+0x7f>
    141a:	90                   	nop
    141b:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    141e:	48 63 d0             	movsxd rdx,eax
    1421:	48 8b 45 d8          	mov    rax,QWORD PTR [rbp-0x28]
    1425:	48 01 d0             	add    rax,rdx
    1428:	c6 00 00             	mov    BYTE PTR [rax],0x0
    142b:	48 8b 45 d8          	mov    rax,QWORD PTR [rbp-0x28]
    142f:	c9                   	leave
    1430:	c3                   	ret

0000000000001431 <raw_parse_int>:
    1431:	f3 0f 1e fa          	endbr64
    1435:	55                   	push   rbp
    1436:	48 89 e5             	mov    rbp,rsp
    1439:	48 89 7d e8          	mov    QWORD PTR [rbp-0x18],rdi
    143d:	48 89 75 e0          	mov    QWORD PTR [rbp-0x20],rsi
    1441:	c7 45 fc 00 00 00 00 	mov    DWORD PTR [rbp-0x4],0x0
    1448:	eb 04                	jmp    144e <raw_parse_int+0x1d>
    144a:	83 45 fc 01          	add    DWORD PTR [rbp-0x4],0x1
    144e:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1451:	48 63 d0             	movsxd rdx,eax
    1454:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1458:	48 01 d0             	add    rax,rdx
    145b:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    145e:	3c 20                	cmp    al,0x20
    1460:	74 e8                	je     144a <raw_parse_int+0x19>
    1462:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1465:	48 63 d0             	movsxd rdx,eax
    1468:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    146c:	48 01 d0             	add    rax,rdx
    146f:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    1472:	3c 09                	cmp    al,0x9
    1474:	74 d4                	je     144a <raw_parse_int+0x19>
    1476:	c7 45 f8 01 00 00 00 	mov    DWORD PTR [rbp-0x8],0x1
    147d:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1480:	48 63 d0             	movsxd rdx,eax
    1483:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1487:	48 01 d0             	add    rax,rdx
    148a:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    148d:	3c 2d                	cmp    al,0x2d
    148f:	75 0d                	jne    149e <raw_parse_int+0x6d>
    1491:	c7 45 f8 ff ff ff ff 	mov    DWORD PTR [rbp-0x8],0xffffffff
    1498:	83 45 fc 01          	add    DWORD PTR [rbp-0x4],0x1
    149c:	eb 18                	jmp    14b6 <raw_parse_int+0x85>
    149e:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    14a1:	48 63 d0             	movsxd rdx,eax
    14a4:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    14a8:	48 01 d0             	add    rax,rdx
    14ab:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    14ae:	3c 2b                	cmp    al,0x2b
    14b0:	75 04                	jne    14b6 <raw_parse_int+0x85>
    14b2:	83 45 fc 01          	add    DWORD PTR [rbp-0x4],0x1
    14b6:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    14b9:	48 63 d0             	movsxd rdx,eax
    14bc:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    14c0:	48 01 d0             	add    rax,rdx
    14c3:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    14c6:	3c 2f                	cmp    al,0x2f
    14c8:	7e 14                	jle    14de <raw_parse_int+0xad>
    14ca:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    14cd:	48 63 d0             	movsxd rdx,eax
    14d0:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    14d4:	48 01 d0             	add    rax,rdx
    14d7:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    14da:	3c 39                	cmp    al,0x39
    14dc:	7e 0a                	jle    14e8 <raw_parse_int+0xb7>
    14de:	b8 00 00 00 00       	mov    eax,0x0
    14e3:	e9 82 00 00 00       	jmp    156a <raw_parse_int+0x139>
    14e8:	48 c7 45 f0 00 00 00 	mov    QWORD PTR [rbp-0x10],0x0
    14ef:	00 
    14f0:	eb 37                	jmp    1529 <raw_parse_int+0xf8>
    14f2:	48 8b 55 f0          	mov    rdx,QWORD PTR [rbp-0x10]
    14f6:	48 89 d0             	mov    rax,rdx
    14f9:	48 c1 e0 02          	shl    rax,0x2
    14fd:	48 01 d0             	add    rax,rdx
    1500:	48 01 c0             	add    rax,rax
    1503:	48 89 c1             	mov    rcx,rax
    1506:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1509:	48 63 d0             	movsxd rdx,eax
    150c:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1510:	48 01 d0             	add    rax,rdx
    1513:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    1516:	0f be c0             	movsx  eax,al
    1519:	83 e8 30             	sub    eax,0x30
    151c:	48 98                	cdqe
    151e:	48 01 c8             	add    rax,rcx
    1521:	48 89 45 f0          	mov    QWORD PTR [rbp-0x10],rax
    1525:	83 45 fc 01          	add    DWORD PTR [rbp-0x4],0x1
    1529:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    152c:	48 63 d0             	movsxd rdx,eax
    152f:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1533:	48 01 d0             	add    rax,rdx
    1536:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    1539:	3c 2f                	cmp    al,0x2f
    153b:	7e 14                	jle    1551 <raw_parse_int+0x120>
    153d:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1540:	48 63 d0             	movsxd rdx,eax
    1543:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    1547:	48 01 d0             	add    rax,rdx
    154a:	0f b6 00             	movzx  eax,BYTE PTR [rax]
    154d:	3c 39                	cmp    al,0x39
    154f:	7e a1                	jle    14f2 <raw_parse_int+0xc1>
    1551:	48 8b 45 f0          	mov    rax,QWORD PTR [rbp-0x10]
    1555:	89 c2                	mov    edx,eax
    1557:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    155a:	0f af c2             	imul   eax,edx
    155d:	89 c2                	mov    edx,eax
    155f:	48 8b 45 e0          	mov    rax,QWORD PTR [rbp-0x20]
    1563:	89 10                	mov    DWORD PTR [rax],edx
    1565:	b8 01 00 00 00       	mov    eax,0x1
    156a:	5d                   	pop    rbp
    156b:	c3                   	ret

000000000000156c <get_random_number>:
    156c:	f3 0f 1e fa          	endbr64
    1570:	55                   	push   rbp
    1571:	48 89 e5             	mov    rbp,rsp
    1574:	48 83 ec 10          	sub    rsp,0x10
    1578:	be 00 00 00 00       	mov    esi,0x0
    157d:	48 8d 05 d0 2a 00 00 	lea    rax,[rip+0x2ad0]        # 4054 <CHUNK_DEPTH+0x34>
    1584:	48 89 c7             	mov    rdi,rax
    1587:	b8 00 00 00 00       	mov    eax,0x0
    158c:	e8 7f fb ff ff       	call   1110 <open@plt>
    1591:	89 45 fc             	mov    DWORD PTR [rbp-0x4],eax
    1594:	83 7d fc 00          	cmp    DWORD PTR [rbp-0x4],0x0
    1598:	79 16                	jns    15b0 <get_random_number+0x44>
    159a:	48 8d 05 c7 2a 00 00 	lea    rax,[rip+0x2ac7]        # 4068 <CHUNK_DEPTH+0x48>
    15a1:	48 89 c7             	mov    rdi,rax
    15a4:	e8 b0 fc ff ff       	call   1259 <raw_eprint>
    15a9:	b8 01 00 00 00       	mov    eax,0x1
    15ae:	eb 2c                	jmp    15dc <get_random_number+0x70>
    15b0:	48 c7 45 f0 00 00 00 	mov    QWORD PTR [rbp-0x10],0x0
    15b7:	00 
    15b8:	48 8d 4d f0          	lea    rcx,[rbp-0x10]
    15bc:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    15bf:	ba 08 00 00 00       	mov    edx,0x8
    15c4:	48 89 ce             	mov    rsi,rcx
    15c7:	89 c7                	mov    edi,eax
    15c9:	e8 22 fb ff ff       	call   10f0 <read@plt>
    15ce:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    15d1:	89 c7                	mov    edi,eax
    15d3:	e8 08 fb ff ff       	call   10e0 <close@plt>
    15d8:	48 8b 45 f0          	mov    rax,QWORD PTR [rbp-0x10]
    15dc:	c9                   	leave
    15dd:	c3                   	ret

00000000000015de <get_a_fun_fact>:
    15de:	f3 0f 1e fa          	endbr64
    15e2:	55                   	push   rbp
    15e3:	48 89 e5             	mov    rbp,rsp
    15e6:	48 81 ec a0 00 00 00 	sub    rsp,0xa0
    15ed:	e8 7a ff ff ff       	call   156c <get_random_number>
    15f2:	48 89 c1             	mov    rcx,rax
    15f5:	48 ba a3 8b 2e ba e8 	movabs rdx,0x2e8ba2e8ba2e8ba3
    15fc:	a2 8b 2e 
    15ff:	48 89 c8             	mov    rax,rcx
    1602:	48 f7 e2             	mul    rdx
    1605:	48 d1 ea             	shr    rdx,1
    1608:	48 89 d0             	mov    rax,rdx
    160b:	48 c1 e0 02          	shl    rax,0x2
    160f:	48 01 d0             	add    rax,rdx
    1612:	48 01 c0             	add    rax,rax
    1615:	48 01 d0             	add    rax,rdx
    1618:	48 29 c1             	sub    rcx,rax
    161b:	48 89 ca             	mov    rdx,rcx
    161e:	48 83 fa 0a          	cmp    rdx,0xa
    1622:	0f 87 63 02 00 00    	ja     188b <get_a_fun_fact+0x2ad>
    1628:	48 c1 e2 02          	shl    rdx,0x2
    162c:	48 8d 05 61 30 00 00 	lea    rax,[rip+0x3061]        # 4694 <CHUNK_DEPTH+0x674>
    1633:	8b 04 02             	mov    eax,DWORD PTR [rdx+rax*1]
    1636:	48 98                	cdqe
    1638:	48 8d 15 55 30 00 00 	lea    rdx,[rip+0x3055]        # 4694 <CHUNK_DEPTH+0x674>
    163f:	48 01 d0             	add    rax,rdx
    1642:	3e ff e0             	notrack jmp rax
    1645:	48 8d 05 64 2a 00 00 	lea    rax,[rip+0x2a64]        # 40b0 <CHUNK_DEPTH+0x90>
    164c:	48 89 c7             	mov    rdi,rax
    164f:	e8 b5 fb ff ff       	call   1209 <raw_print>
    1654:	8b 05 d6 5e 00 00    	mov    eax,DWORD PTR [rip+0x5ed6]        # 7530 <be_annoying>
    165a:	48 98                	cdqe
    165c:	48 89 45 f0          	mov    QWORD PTR [rbp-0x10],rax
    1660:	48 c7 45 f8 00 00 00 	mov    QWORD PTR [rbp-0x8],0x0
    1667:	00 
    1668:	48 8d 45 f0          	lea    rax,[rbp-0x10]
    166c:	be 00 00 00 00       	mov    esi,0x0
    1671:	48 89 c7             	mov    rdi,rax
    1674:	e8 57 fa ff ff       	call   10d0 <nanosleep@plt>
    1679:	e9 27 02 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    167e:	48 8d 05 13 2b 00 00 	lea    rax,[rip+0x2b13]        # 4198 <CHUNK_DEPTH+0x178>
    1685:	48 89 c7             	mov    rdi,rax
    1688:	e8 7c fb ff ff       	call   1209 <raw_print>
    168d:	8b 05 9d 5e 00 00    	mov    eax,DWORD PTR [rip+0x5e9d]        # 7530 <be_annoying>
    1693:	48 98                	cdqe
    1695:	48 89 45 e0          	mov    QWORD PTR [rbp-0x20],rax
    1699:	48 c7 45 e8 00 00 00 	mov    QWORD PTR [rbp-0x18],0x0
    16a0:	00 
    16a1:	48 8d 45 e0          	lea    rax,[rbp-0x20]
    16a5:	be 00 00 00 00       	mov    esi,0x0
    16aa:	48 89 c7             	mov    rdi,rax
    16ad:	e8 1e fa ff ff       	call   10d0 <nanosleep@plt>
    16b2:	e9 ee 01 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    16b7:	48 8d 05 2a 2b 00 00 	lea    rax,[rip+0x2b2a]        # 41e8 <CHUNK_DEPTH+0x1c8>
    16be:	48 89 c7             	mov    rdi,rax
    16c1:	e8 43 fb ff ff       	call   1209 <raw_print>
    16c6:	8b 05 64 5e 00 00    	mov    eax,DWORD PTR [rip+0x5e64]        # 7530 <be_annoying>
    16cc:	48 98                	cdqe
    16ce:	48 89 45 d0          	mov    QWORD PTR [rbp-0x30],rax
    16d2:	48 c7 45 d8 00 00 00 	mov    QWORD PTR [rbp-0x28],0x0
    16d9:	00 
    16da:	48 8d 45 d0          	lea    rax,[rbp-0x30]
    16de:	be 00 00 00 00       	mov    esi,0x0
    16e3:	48 89 c7             	mov    rdi,rax
    16e6:	e8 e5 f9 ff ff       	call   10d0 <nanosleep@plt>
    16eb:	e9 b5 01 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    16f0:	48 8d 05 61 2b 00 00 	lea    rax,[rip+0x2b61]        # 4258 <CHUNK_DEPTH+0x238>
    16f7:	48 89 c7             	mov    rdi,rax
    16fa:	e8 0a fb ff ff       	call   1209 <raw_print>
    16ff:	8b 05 2b 5e 00 00    	mov    eax,DWORD PTR [rip+0x5e2b]        # 7530 <be_annoying>
    1705:	48 98                	cdqe
    1707:	48 89 45 c0          	mov    QWORD PTR [rbp-0x40],rax
    170b:	48 c7 45 c8 00 00 00 	mov    QWORD PTR [rbp-0x38],0x0
    1712:	00 
    1713:	48 8d 45 c0          	lea    rax,[rbp-0x40]
    1717:	be 00 00 00 00       	mov    esi,0x0
    171c:	48 89 c7             	mov    rdi,rax
    171f:	e8 ac f9 ff ff       	call   10d0 <nanosleep@plt>
    1724:	e9 7c 01 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    1729:	48 8d 05 b0 2b 00 00 	lea    rax,[rip+0x2bb0]        # 42e0 <CHUNK_DEPTH+0x2c0>
    1730:	48 89 c7             	mov    rdi,rax
    1733:	e8 d1 fa ff ff       	call   1209 <raw_print>
    1738:	8b 05 f2 5d 00 00    	mov    eax,DWORD PTR [rip+0x5df2]        # 7530 <be_annoying>
    173e:	48 98                	cdqe
    1740:	48 89 45 b0          	mov    QWORD PTR [rbp-0x50],rax
    1744:	48 c7 45 b8 00 00 00 	mov    QWORD PTR [rbp-0x48],0x0
    174b:	00 
    174c:	48 8d 45 b0          	lea    rax,[rbp-0x50]
    1750:	be 00 00 00 00       	mov    esi,0x0
    1755:	48 89 c7             	mov    rdi,rax
    1758:	e8 73 f9 ff ff       	call   10d0 <nanosleep@plt>
    175d:	e9 43 01 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    1762:	48 8d 05 f7 2b 00 00 	lea    rax,[rip+0x2bf7]        # 4360 <CHUNK_DEPTH+0x340>
    1769:	48 89 c7             	mov    rdi,rax
    176c:	e8 98 fa ff ff       	call   1209 <raw_print>
    1771:	8b 05 b9 5d 00 00    	mov    eax,DWORD PTR [rip+0x5db9]        # 7530 <be_annoying>
    1777:	48 98                	cdqe
    1779:	48 89 45 a0          	mov    QWORD PTR [rbp-0x60],rax
    177d:	48 c7 45 a8 00 00 00 	mov    QWORD PTR [rbp-0x58],0x0
    1784:	00 
    1785:	48 8d 45 a0          	lea    rax,[rbp-0x60]
    1789:	be 00 00 00 00       	mov    esi,0x0
    178e:	48 89 c7             	mov    rdi,rax
    1791:	e8 3a f9 ff ff       	call   10d0 <nanosleep@plt>
    1796:	e9 0a 01 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    179b:	48 8d 05 3e 2c 00 00 	lea    rax,[rip+0x2c3e]        # 43e0 <CHUNK_DEPTH+0x3c0>
    17a2:	48 89 c7             	mov    rdi,rax
    17a5:	e8 5f fa ff ff       	call   1209 <raw_print>
    17aa:	8b 05 80 5d 00 00    	mov    eax,DWORD PTR [rip+0x5d80]        # 7530 <be_annoying>
    17b0:	48 98                	cdqe
    17b2:	48 89 45 90          	mov    QWORD PTR [rbp-0x70],rax
    17b6:	48 c7 45 98 00 00 00 	mov    QWORD PTR [rbp-0x68],0x0
    17bd:	00 
    17be:	48 8d 45 90          	lea    rax,[rbp-0x70]
    17c2:	be 00 00 00 00       	mov    esi,0x0
    17c7:	48 89 c7             	mov    rdi,rax
    17ca:	e8 01 f9 ff ff       	call   10d0 <nanosleep@plt>
    17cf:	e9 d1 00 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    17d4:	48 8d 05 7d 2c 00 00 	lea    rax,[rip+0x2c7d]        # 4458 <CHUNK_DEPTH+0x438>
    17db:	48 89 c7             	mov    rdi,rax
    17de:	e8 26 fa ff ff       	call   1209 <raw_print>
    17e3:	8b 05 47 5d 00 00    	mov    eax,DWORD PTR [rip+0x5d47]        # 7530 <be_annoying>
    17e9:	48 98                	cdqe
    17eb:	48 89 45 80          	mov    QWORD PTR [rbp-0x80],rax
    17ef:	48 c7 45 88 00 00 00 	mov    QWORD PTR [rbp-0x78],0x0
    17f6:	00 
    17f7:	48 8d 45 80          	lea    rax,[rbp-0x80]
    17fb:	be 00 00 00 00       	mov    esi,0x0
    1800:	48 89 c7             	mov    rdi,rax
    1803:	e8 c8 f8 ff ff       	call   10d0 <nanosleep@plt>
    1808:	e9 98 00 00 00       	jmp    18a5 <get_a_fun_fact+0x2c7>
    180d:	48 8d 05 c4 2c 00 00 	lea    rax,[rip+0x2cc4]        # 44d8 <CHUNK_DEPTH+0x4b8>
    1814:	48 89 c7             	mov    rdi,rax
    1817:	e8 ed f9 ff ff       	call   1209 <raw_print>
    181c:	8b 05 0e 5d 00 00    	mov    eax,DWORD PTR [rip+0x5d0e]        # 7530 <be_annoying>
    1822:	48 98                	cdqe
    1824:	48 89 85 70 ff ff ff 	mov    QWORD PTR [rbp-0x90],rax
    182b:	48 c7 85 78 ff ff ff 	mov    QWORD PTR [rbp-0x88],0x0
    1832:	00 00 00 00 
    1836:	48 8d 85 70 ff ff ff 	lea    rax,[rbp-0x90]
    183d:	be 00 00 00 00       	mov    esi,0x0
    1842:	48 89 c7             	mov    rdi,rax
    1845:	e8 86 f8 ff ff       	call   10d0 <nanosleep@plt>
    184a:	eb 59                	jmp    18a5 <get_a_fun_fact+0x2c7>
    184c:	48 8d 05 2d 2d 00 00 	lea    rax,[rip+0x2d2d]        # 4580 <CHUNK_DEPTH+0x560>
    1853:	48 89 c7             	mov    rdi,rax
    1856:	e8 ae f9 ff ff       	call   1209 <raw_print>
    185b:	8b 05 cf 5c 00 00    	mov    eax,DWORD PTR [rip+0x5ccf]        # 7530 <be_annoying>
    1861:	48 98                	cdqe
    1863:	48 89 85 60 ff ff ff 	mov    QWORD PTR [rbp-0xa0],rax
    186a:	48 c7 85 68 ff ff ff 	mov    QWORD PTR [rbp-0x98],0x0
    1871:	00 00 00 00 
    1875:	48 8d 85 60 ff ff ff 	lea    rax,[rbp-0xa0]
    187c:	be 00 00 00 00       	mov    esi,0x0
    1881:	48 89 c7             	mov    rdi,rax
    1884:	e8 47 f8 ff ff       	call   10d0 <nanosleep@plt>
    1889:	eb 1a                	jmp    18a5 <get_a_fun_fact+0x2c7>
    188b:	bf 0b 00 00 00       	mov    edi,0xb
    1890:	e8 31 22 00 00       	call   3ac6 <scream>
    1895:	48 8d 05 bc 2d 00 00 	lea    rax,[rip+0x2dbc]        # 4658 <CHUNK_DEPTH+0x638>
    189c:	48 89 c7             	mov    rdi,rax
    189f:	e8 65 f9 ff ff       	call   1209 <raw_print>
    18a4:	90                   	nop
    18a5:	b8 00 00 00 00       	mov    eax,0x0
    18aa:	c9                   	leave
    18ab:	c3                   	ret

00000000000018ac <place_flag>:
    18ac:	f3 0f 1e fa          	endbr64
    18b0:	55                   	push   rbp
    18b1:	48 89 e5             	mov    rbp,rsp
    18b4:	48 81 ec 00 10 00 00 	sub    rsp,0x1000
    18bb:	48 83 0c 24 00       	or     QWORD PTR [rsp],0x0
    18c0:	48 81 ec 00 10 00 00 	sub    rsp,0x1000
    18c7:	48 83 0c 24 00       	or     QWORD PTR [rsp],0x0
    18cc:	48 83 ec 60          	sub    rsp,0x60
    18d0:	c7 45 fc 00 00 00 00 	mov    DWORD PTR [rbp-0x4],0x0
    18d7:	eb 11                	jmp    18ea <place_flag+0x3e>
    18d9:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    18dc:	48 98                	cdqe
    18de:	c6 84 05 e0 df ff ff 	mov    BYTE PTR [rbp+rax*1-0x2020],0x0
    18e5:	00 
    18e6:	83 45 fc 01          	add    DWORD PTR [rbp-0x4],0x1
    18ea:	81 7d fc ff 1f 00 00 	cmp    DWORD PTR [rbp-0x4],0x1fff
    18f1:	7e e6                	jle    18d9 <place_flag+0x2d>
    18f3:	be 00 00 00 00       	mov    esi,0x0
    18f8:	48 8d 05 c1 2d 00 00 	lea    rax,[rip+0x2dc1]        # 46c0 <CHUNK_DEPTH+0x6a0>
    18ff:	48 89 c7             	mov    rdi,rax
    1902:	b8 00 00 00 00       	mov    eax,0x0
    1907:	e8 04 f8 ff ff       	call   1110 <open@plt>
    190c:	89 45 f0             	mov    DWORD PTR [rbp-0x10],eax
    190f:	83 7d f0 00          	cmp    DWORD PTR [rbp-0x10],0x0
    1913:	79 19                	jns    192e <place_flag+0x82>
    1915:	48 8d 05 b4 2d 00 00 	lea    rax,[rip+0x2db4]        # 46d0 <CHUNK_DEPTH+0x6b0>
    191c:	48 89 c7             	mov    rdi,rax
    191f:	e8 35 f9 ff ff       	call   1259 <raw_eprint>
    1924:	bf 01 00 00 00       	mov    edi,0x1
    1929:	e8 82 f7 ff ff       	call   10b0 <_exit@plt>
    192e:	48 8d 8d a0 df ff ff 	lea    rcx,[rbp-0x2060]
    1935:	8b 45 f0             	mov    eax,DWORD PTR [rbp-0x10]
    1938:	ba 3c 00 00 00       	mov    edx,0x3c
    193d:	48 89 ce             	mov    rsi,rcx
    1940:	89 c7                	mov    edi,eax
    1942:	e8 a9 f7 ff ff       	call   10f0 <read@plt>
    1947:	89 45 f4             	mov    DWORD PTR [rbp-0xc],eax
    194a:	8b 45 f0             	mov    eax,DWORD PTR [rbp-0x10]
    194d:	89 c7                	mov    edi,eax
    194f:	e8 8c f7 ff ff       	call   10e0 <close@plt>
    1954:	83 7d f4 00          	cmp    DWORD PTR [rbp-0xc],0x0
    1958:	79 07                	jns    1961 <place_flag+0xb5>
    195a:	c7 45 f4 00 00 00 00 	mov    DWORD PTR [rbp-0xc],0x0
    1961:	c7 45 fc 00 00 00 00 	mov    DWORD PTR [rbp-0x4],0x0
    1968:	e9 84 00 00 00       	jmp    19f1 <place_flag+0x145>
    196d:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    1970:	48 98                	cdqe
    1972:	48 8d 14 85 00 00 00 	lea    rdx,[rax*4+0x0]
    1979:	00 
    197a:	48 8d 05 9f 26 00 00 	lea    rax,[rip+0x269f]        # 4020 <CHUNK_DEPTH>
    1981:	8b 04 02             	mov    eax,DWORD PTR [rdx+rax*1]
    1984:	ba dc 19 00 00       	mov    edx,0x19dc
    1989:	29 c2                	sub    edx,eax
    198b:	48 63 c2             	movsxd rax,edx
    198e:	48 8d 95 e0 df ff ff 	lea    rdx,[rbp-0x2020]
    1995:	48 01 d0             	add    rax,rdx
    1998:	48 89 45 e8          	mov    QWORD PTR [rbp-0x18],rax
    199c:	c7 45 f8 00 00 00 00 	mov    DWORD PTR [rbp-0x8],0x0
    19a3:	eb 2e                	jmp    19d3 <place_flag+0x127>
    19a5:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    19a8:	8d 14 85 00 00 00 00 	lea    edx,[rax*4+0x0]
    19af:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    19b2:	8d 0c 02             	lea    ecx,[rdx+rax*1]
    19b5:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    19b8:	48 63 d0             	movsxd rdx,eax
    19bb:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    19bf:	48 01 c2             	add    rdx,rax
    19c2:	48 63 c1             	movsxd rax,ecx
    19c5:	0f b6 84 05 a0 df ff 	movzx  eax,BYTE PTR [rbp+rax*1-0x2060]
    19cc:	ff 
    19cd:	88 02                	mov    BYTE PTR [rdx],al
    19cf:	83 45 f8 01          	add    DWORD PTR [rbp-0x8],0x1
    19d3:	83 7d f8 03          	cmp    DWORD PTR [rbp-0x8],0x3
    19d7:	7f 14                	jg     19ed <place_flag+0x141>
    19d9:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    19dc:	8d 14 85 00 00 00 00 	lea    edx,[rax*4+0x0]
    19e3:	8b 45 f8             	mov    eax,DWORD PTR [rbp-0x8]
    19e6:	01 d0                	add    eax,edx
    19e8:	39 45 f4             	cmp    DWORD PTR [rbp-0xc],eax
    19eb:	7f b8                	jg     19a5 <place_flag+0xf9>
    19ed:	83 45 fc 01          	add    DWORD PTR [rbp-0x4],0x1
    19f1:	83 7d fc 0c          	cmp    DWORD PTR [rbp-0x4],0xc
    19f5:	7f 0f                	jg     1a06 <place_flag+0x15a>
    19f7:	8b 45 fc             	mov    eax,DWORD PTR [rbp-0x4]
    19fa:	c1 e0 02             	shl    eax,0x2
    19fd:	39 45 f4             	cmp    DWORD PTR [rbp-0xc],eax
    1a00:	0f 8f 67 ff ff ff    	jg     196d <place_flag+0xc1>
    1a06:	b8 00 00 00 00       	mov    eax,0x0
    1a0b:	c9                   	leave
    1a0c:	c3                   	ret

0000000000001a0d <main>:
    1a0d:	f3 0f 1e fa          	endbr64
    1a11:	55                   	push   rbp
    1a12:	48 89 e5             	mov    rbp,rsp
    1a15:	48 81 ec 10 01 00 00 	sub    rsp,0x110
    1a1c:	c7 85 fc fe ff ff 00 	mov    DWORD PTR [rbp-0x104],0x0
    1a23:	00 00 00 
    1a26:	e8 81 fe ff ff       	call   18ac <place_flag>
    1a2b:	c7 05 4b 5b 00 00 01 	mov    DWORD PTR [rip+0x5b4b],0x1        # 7580 <userData>
    1a32:	00 00 00 
    1a35:	c7 05 45 5b 00 00 00 	mov    DWORD PTR [rip+0x5b45],0x0        # 7584 <userData+0x4>
    1a3c:	00 00 00 
    1a3f:	48 8d 05 ca 2c 00 00 	lea    rax,[rip+0x2cca]        # 4710 <CHUNK_DEPTH+0x6f0>
    1a46:	48 89 c7             	mov    rdi,rax
    1a49:	e8 bb f7 ff ff       	call   1209 <raw_print>
    1a4e:	48 8d 05 34 2d 00 00 	lea    rax,[rip+0x2d34]        # 4789 <CHUNK_DEPTH+0x769>
    1a55:	48 89 c7             	mov    rdi,rax
    1a58:	e8 ac f7 ff ff       	call   1209 <raw_print>
    1a5d:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1a64:	be 00 01 00 00       	mov    esi,0x100
    1a69:	48 89 c7             	mov    rdi,rax
    1a6c:	e8 2b f9 ff ff       	call   139c <raw_readline>
    1a71:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    1a78:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1a7f:	48 89 d6             	mov    rsi,rdx
    1a82:	48 89 c7             	mov    rdi,rax
    1a85:	e8 a7 f9 ff ff       	call   1431 <raw_parse_int>
    1a8a:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1a90:	83 f8 2a             	cmp    eax,0x2a
    1a93:	75 0a                	jne    1a9f <main+0x92>
    1a95:	c7 05 91 5a 00 00 00 	mov    DWORD PTR [rip+0x5a91],0x0        # 7530 <be_annoying>
    1a9c:	00 00 00 
    1a9f:	e8 07 00 00 00       	call   1aab <start_position>
    1aa4:	b8 00 00 00 00       	mov    eax,0x0
    1aa9:	c9                   	leave
    1aaa:	c3                   	ret

0000000000001aab <start_position>:
    1aab:	f3 0f 1e fa          	endbr64
    1aaf:	55                   	push   rbp
    1ab0:	48 89 e5             	mov    rbp,rsp
    1ab3:	48 81 ec 10 01 00 00 	sub    rsp,0x110
    1aba:	c7 85 fc fe ff ff 00 	mov    DWORD PTR [rbp-0x104],0x0
    1ac1:	00 00 00 
    1ac4:	c7 05 b6 5a 00 00 00 	mov    DWORD PTR [rip+0x5ab6],0x0        # 7584 <userData+0x4>
    1acb:	00 00 00 
    1ace:	48 8d 05 ca 2c 00 00 	lea    rax,[rip+0x2cca]        # 479f <CHUNK_DEPTH+0x77f>
    1ad5:	48 89 c7             	mov    rdi,rax
    1ad8:	e8 2c f7 ff ff       	call   1209 <raw_print>
    1add:	48 8d 05 d7 2c 00 00 	lea    rax,[rip+0x2cd7]        # 47bb <CHUNK_DEPTH+0x79b>
    1ae4:	48 89 c7             	mov    rdi,rax
    1ae7:	e8 1d f7 ff ff       	call   1209 <raw_print>
    1aec:	48 8d 05 e5 2c 00 00 	lea    rax,[rip+0x2ce5]        # 47d8 <CHUNK_DEPTH+0x7b8>
    1af3:	48 89 c7             	mov    rdi,rax
    1af6:	e8 0e f7 ff ff       	call   1209 <raw_print>
    1afb:	eb 65                	jmp    1b62 <start_position+0xb7>
    1afd:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1b04:	be 00 01 00 00       	mov    esi,0x100
    1b09:	48 89 c7             	mov    rdi,rax
    1b0c:	e8 8b f8 ff ff       	call   139c <raw_readline>
    1b11:	48 85 c0             	test   rax,rax
    1b14:	75 0f                	jne    1b25 <start_position+0x7a>
    1b16:	48 8d 05 fb 2c 00 00 	lea    rax,[rip+0x2cfb]        # 4818 <CHUNK_DEPTH+0x7f8>
    1b1d:	48 89 c7             	mov    rdi,rax
    1b20:	e8 e4 f6 ff ff       	call   1209 <raw_print>
    1b25:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    1b2c:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1b33:	48 89 d6             	mov    rsi,rdx
    1b36:	48 89 c7             	mov    rdi,rax
    1b39:	e8 f3 f8 ff ff       	call   1431 <raw_parse_int>
    1b3e:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1b44:	83 f8 03             	cmp    eax,0x3
    1b47:	7f 0a                	jg     1b53 <start_position+0xa8>
    1b49:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1b4f:	85 c0                	test   eax,eax
    1b51:	7f 0f                	jg     1b62 <start_position+0xb7>
    1b53:	48 8d 05 06 2d 00 00 	lea    rax,[rip+0x2d06]        # 4860 <CHUNK_DEPTH+0x840>
    1b5a:	48 89 c7             	mov    rdi,rax
    1b5d:	e8 a7 f6 ff ff       	call   1209 <raw_print>
    1b62:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1b68:	83 f8 03             	cmp    eax,0x3
    1b6b:	7f 90                	jg     1afd <start_position+0x52>
    1b6d:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1b73:	85 c0                	test   eax,eax
    1b75:	7e 86                	jle    1afd <start_position+0x52>
    1b77:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1b7d:	83 f8 03             	cmp    eax,0x3
    1b80:	74 29                	je     1bab <start_position+0x100>
    1b82:	83 f8 03             	cmp    eax,0x3
    1b85:	0f 8f 97 00 00 00    	jg     1c22 <start_position+0x177>
    1b8b:	83 f8 01             	cmp    eax,0x1
    1b8e:	74 0a                	je     1b9a <start_position+0xef>
    1b90:	83 f8 02             	cmp    eax,0x2
    1b93:	74 0f                	je     1ba4 <start_position+0xf9>
    1b95:	e9 88 00 00 00       	jmp    1c22 <start_position+0x177>
    1b9a:	e8 8a 00 00 00       	call   1c29 <initial_call>
    1b9f:	e9 83 00 00 00       	jmp    1c27 <start_position+0x17c>
    1ba4:	e8 f5 1e 00 00       	call   3a9e <initial_email>
    1ba9:	eb 7c                	jmp    1c27 <start_position+0x17c>
    1bab:	48 8d 05 ee 2c 00 00 	lea    rax,[rip+0x2cee]        # 48a0 <CHUNK_DEPTH+0x880>
    1bb2:	48 89 c7             	mov    rdi,rax
    1bb5:	e8 4f f6 ff ff       	call   1209 <raw_print>
    1bba:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1bc1:	be 00 01 00 00       	mov    esi,0x100
    1bc6:	48 89 c7             	mov    rdi,rax
    1bc9:	e8 ce f7 ff ff       	call   139c <raw_readline>
    1bce:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    1bd5:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1bdc:	48 89 d6             	mov    rsi,rdx
    1bdf:	48 89 c7             	mov    rdi,rax
    1be2:	e8 4a f8 ff ff       	call   1431 <raw_parse_int>
    1be7:	8b 8d fc fe ff ff    	mov    ecx,DWORD PTR [rbp-0x104]
    1bed:	48 63 c1             	movsxd rax,ecx
    1bf0:	48 69 c0 e9 a2 8b 2e 	imul   rax,rax,0x2e8ba2e9
    1bf7:	48 c1 e8 20          	shr    rax,0x20
    1bfb:	89 c2                	mov    edx,eax
    1bfd:	d1 fa                	sar    edx,1
    1bff:	89 c8                	mov    eax,ecx
    1c01:	c1 f8 1f             	sar    eax,0x1f
    1c04:	29 c2                	sub    edx,eax
    1c06:	89 d0                	mov    eax,edx
    1c08:	c1 e0 02             	shl    eax,0x2
    1c0b:	01 d0                	add    eax,edx
    1c0d:	01 c0                	add    eax,eax
    1c0f:	01 d0                	add    eax,edx
    1c11:	29 c1                	sub    ecx,eax
    1c13:	89 ca                	mov    edx,ecx
    1c15:	89 d7                	mov    edi,edx
    1c17:	e8 aa 1e 00 00       	call   3ac6 <scream>
    1c1c:	e8 8a fe ff ff       	call   1aab <start_position>
    1c21:	90                   	nop
    1c22:	b8 00 00 00 00       	mov    eax,0x0
    1c27:	c9                   	leave
    1c28:	c3                   	ret

0000000000001c29 <initial_call>:
    1c29:	f3 0f 1e fa          	endbr64
    1c2d:	55                   	push   rbp
    1c2e:	48 89 e5             	mov    rbp,rsp
    1c31:	48 81 ec 70 01 00 00 	sub    rsp,0x170
    1c38:	c7 85 fc fe ff ff 00 	mov    DWORD PTR [rbp-0x104],0x0
    1c3f:	00 00 00 
    1c42:	ba 00 00 00 00       	mov    edx,0x0
    1c47:	be 00 00 00 00       	mov    esi,0x0
    1c4c:	48 8d 05 7c 2c 00 00 	lea    rax,[rip+0x2c7c]        # 48cf <CHUNK_DEPTH+0x8af>
    1c53:	48 89 c7             	mov    rdi,rax
    1c56:	e8 c9 1e 00 00       	call   3b24 <prompt>
    1c5b:	ba 00 00 00 00       	mov    edx,0x0
    1c60:	be 00 00 00 00       	mov    esi,0x0
    1c65:	48 8d 05 7c 2c 00 00 	lea    rax,[rip+0x2c7c]        # 48e8 <CHUNK_DEPTH+0x8c8>
    1c6c:	48 89 c7             	mov    rdi,rax
    1c6f:	e8 b0 1e 00 00       	call   3b24 <prompt>
    1c74:	ba 00 00 00 00       	mov    edx,0x0
    1c79:	be 00 00 00 00       	mov    esi,0x0
    1c7e:	48 8d 05 8b 2c 00 00 	lea    rax,[rip+0x2c8b]        # 4910 <CHUNK_DEPTH+0x8f0>
    1c85:	48 89 c7             	mov    rdi,rax
    1c88:	e8 97 1e 00 00       	call   3b24 <prompt>
    1c8d:	e9 d3 01 00 00       	jmp    1e65 <initial_call+0x23c>
    1c92:	48 8d 05 c7 2c 00 00 	lea    rax,[rip+0x2cc7]        # 4960 <CHUNK_DEPTH+0x940>
    1c99:	48 89 c7             	mov    rdi,rax
    1c9c:	e8 68 f5 ff ff       	call   1209 <raw_print>
    1ca1:	8b 05 89 58 00 00    	mov    eax,DWORD PTR [rip+0x5889]        # 7530 <be_annoying>
    1ca7:	48 98                	cdqe
    1ca9:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    1cb0:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    1cb7:	00 00 00 00 
    1cbb:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    1cc2:	be 00 00 00 00       	mov    esi,0x0
    1cc7:	48 89 c7             	mov    rdi,rax
    1cca:	e8 01 f4 ff ff       	call   10d0 <nanosleep@plt>
    1ccf:	48 8d 05 ca 2c 00 00 	lea    rax,[rip+0x2cca]        # 49a0 <CHUNK_DEPTH+0x980>
    1cd6:	48 89 c7             	mov    rdi,rax
    1cd9:	e8 2b f5 ff ff       	call   1209 <raw_print>
    1cde:	8b 05 4c 58 00 00    	mov    eax,DWORD PTR [rip+0x584c]        # 7530 <be_annoying>
    1ce4:	48 98                	cdqe
    1ce6:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    1ced:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    1cf4:	00 00 00 00 
    1cf8:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    1cff:	be 00 00 00 00       	mov    esi,0x0
    1d04:	48 89 c7             	mov    rdi,rax
    1d07:	e8 c4 f3 ff ff       	call   10d0 <nanosleep@plt>
    1d0c:	48 8d 05 cd 2c 00 00 	lea    rax,[rip+0x2ccd]        # 49e0 <CHUNK_DEPTH+0x9c0>
    1d13:	48 89 c7             	mov    rdi,rax
    1d16:	e8 ee f4 ff ff       	call   1209 <raw_print>
    1d1b:	8b 05 0f 58 00 00    	mov    eax,DWORD PTR [rip+0x580f]        # 7530 <be_annoying>
    1d21:	48 98                	cdqe
    1d23:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    1d2a:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    1d31:	00 00 00 00 
    1d35:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    1d3c:	be 00 00 00 00       	mov    esi,0x0
    1d41:	48 89 c7             	mov    rdi,rax
    1d44:	e8 87 f3 ff ff       	call   10d0 <nanosleep@plt>
    1d49:	48 8d 05 c0 2c 00 00 	lea    rax,[rip+0x2cc0]        # 4a10 <CHUNK_DEPTH+0x9f0>
    1d50:	48 89 c7             	mov    rdi,rax
    1d53:	e8 b1 f4 ff ff       	call   1209 <raw_print>
    1d58:	8b 05 d2 57 00 00    	mov    eax,DWORD PTR [rip+0x57d2]        # 7530 <be_annoying>
    1d5e:	48 98                	cdqe
    1d60:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    1d67:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    1d6e:	00 00 00 00 
    1d72:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    1d79:	be 00 00 00 00       	mov    esi,0x0
    1d7e:	48 89 c7             	mov    rdi,rax
    1d81:	e8 4a f3 ff ff       	call   10d0 <nanosleep@plt>
    1d86:	48 8d 05 ab 2c 00 00 	lea    rax,[rip+0x2cab]        # 4a38 <CHUNK_DEPTH+0xa18>
    1d8d:	48 89 c7             	mov    rdi,rax
    1d90:	e8 74 f4 ff ff       	call   1209 <raw_print>
    1d95:	8b 05 95 57 00 00    	mov    eax,DWORD PTR [rip+0x5795]        # 7530 <be_annoying>
    1d9b:	48 98                	cdqe
    1d9d:	48 89 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],rax
    1da4:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    1dab:	00 00 00 00 
    1daf:	48 8d 85 a0 fe ff ff 	lea    rax,[rbp-0x160]
    1db6:	be 00 00 00 00       	mov    esi,0x0
    1dbb:	48 89 c7             	mov    rdi,rax
    1dbe:	e8 0d f3 ff ff       	call   10d0 <nanosleep@plt>
    1dc3:	48 8d 05 a6 2c 00 00 	lea    rax,[rip+0x2ca6]        # 4a70 <CHUNK_DEPTH+0xa50>
    1dca:	48 89 c7             	mov    rdi,rax
    1dcd:	e8 37 f4 ff ff       	call   1209 <raw_print>
    1dd2:	8b 05 58 57 00 00    	mov    eax,DWORD PTR [rip+0x5758]        # 7530 <be_annoying>
    1dd8:	48 98                	cdqe
    1dda:	48 89 85 90 fe ff ff 	mov    QWORD PTR [rbp-0x170],rax
    1de1:	48 c7 85 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],0x0
    1de8:	00 00 00 00 
    1dec:	48 8d 85 90 fe ff ff 	lea    rax,[rbp-0x170]
    1df3:	be 00 00 00 00       	mov    esi,0x0
    1df8:	48 89 c7             	mov    rdi,rax
    1dfb:	e8 d0 f2 ff ff       	call   10d0 <nanosleep@plt>
    1e00:	48 8d 05 b9 2c 00 00 	lea    rax,[rip+0x2cb9]        # 4ac0 <CHUNK_DEPTH+0xaa0>
    1e07:	48 89 c7             	mov    rdi,rax
    1e0a:	e8 fa f3 ff ff       	call   1209 <raw_print>
    1e0f:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1e16:	ba 00 01 00 00       	mov    edx,0x100
    1e1b:	48 89 c6             	mov    rsi,rax
    1e1e:	bf 00 00 00 00       	mov    edi,0x0
    1e23:	e8 fc 1c 00 00       	call   3b24 <prompt>
    1e28:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    1e2f:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1e36:	48 89 d6             	mov    rsi,rdx
    1e39:	48 89 c7             	mov    rdi,rax
    1e3c:	e8 f0 f5 ff ff       	call   1431 <raw_parse_int>
    1e41:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1e47:	83 f8 07             	cmp    eax,0x7
    1e4a:	7f 0a                	jg     1e56 <initial_call+0x22d>
    1e4c:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1e52:	85 c0                	test   eax,eax
    1e54:	7f 0f                	jg     1e65 <initial_call+0x23c>
    1e56:	48 8d 05 93 2c 00 00 	lea    rax,[rip+0x2c93]        # 4af0 <CHUNK_DEPTH+0xad0>
    1e5d:	48 89 c7             	mov    rdi,rax
    1e60:	e8 a4 f3 ff ff       	call   1209 <raw_print>
    1e65:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1e6b:	83 f8 06             	cmp    eax,0x6
    1e6e:	0f 8f 1e fe ff ff    	jg     1c92 <initial_call+0x69>
    1e74:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1e7a:	85 c0                	test   eax,eax
    1e7c:	0f 8e 10 fe ff ff    	jle    1c92 <initial_call+0x69>
    1e82:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    1e88:	83 f8 06             	cmp    eax,0x6
    1e8b:	77 4d                	ja     1eda <initial_call+0x2b1>
    1e8d:	89 c0                	mov    eax,eax
    1e8f:	48 8d 14 85 00 00 00 	lea    rdx,[rax*4+0x0]
    1e96:	00 
    1e97:	48 8d 05 92 2c 00 00 	lea    rax,[rip+0x2c92]        # 4b30 <CHUNK_DEPTH+0xb10>
    1e9e:	8b 04 02             	mov    eax,DWORD PTR [rdx+rax*1]
    1ea1:	48 98                	cdqe
    1ea3:	48 8d 15 86 2c 00 00 	lea    rdx,[rip+0x2c86]        # 4b30 <CHUNK_DEPTH+0xb10>
    1eaa:	48 01 d0             	add    rax,rdx
    1ead:	3e ff e0             	notrack jmp rax
    1eb0:	e8 2c 00 00 00       	call   1ee1 <start_service>
    1eb5:	eb 28                	jmp    1edf <initial_call+0x2b6>
    1eb7:	e8 14 04 00 00       	call   22d0 <report_outage>
    1ebc:	eb 21                	jmp    1edf <initial_call+0x2b6>
    1ebe:	e8 59 05 00 00       	call   241c <billing_department>
    1ec3:	eb 1a                	jmp    1edf <initial_call+0x2b6>
    1ec5:	e8 6c 07 00 00       	call   2636 <technical_support>
    1eca:	eb 13                	jmp    1edf <initial_call+0x2b6>
    1ecc:	e8 05 09 00 00       	call   27d6 <upgrade_or_change>
    1ed1:	eb 0c                	jmp    1edf <initial_call+0x2b6>
    1ed3:	e8 4d 0b 00 00       	call   2a25 <other_inquiries>
    1ed8:	eb 05                	jmp    1edf <initial_call+0x2b6>
    1eda:	b8 00 00 00 00       	mov    eax,0x0
    1edf:	c9                   	leave
    1ee0:	c3                   	ret

0000000000001ee1 <start_service>:
    1ee1:	f3 0f 1e fa          	endbr64
    1ee5:	55                   	push   rbp
    1ee6:	48 89 e5             	mov    rbp,rsp
    1ee9:	48 81 ec c0 01 00 00 	sub    rsp,0x1c0
    1ef0:	48 8d 05 59 2c 00 00 	lea    rax,[rip+0x2c59]        # 4b50 <CHUNK_DEPTH+0xb30>
    1ef7:	48 89 c7             	mov    rdi,rax
    1efa:	e8 0a f3 ff ff       	call   1209 <raw_print>
    1eff:	8b 05 2b 56 00 00    	mov    eax,DWORD PTR [rip+0x562b]        # 7530 <be_annoying>
    1f05:	48 98                	cdqe
    1f07:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    1f0e:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    1f15:	00 00 00 00 
    1f19:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    1f20:	be 00 00 00 00       	mov    esi,0x0
    1f25:	48 89 c7             	mov    rdi,rax
    1f28:	e8 a3 f1 ff ff       	call   10d0 <nanosleep@plt>
    1f2d:	e8 ac f6 ff ff       	call   15de <get_a_fun_fact>
    1f32:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    1f39:	ba 00 01 00 00       	mov    edx,0x100
    1f3e:	48 89 c6             	mov    rsi,rax
    1f41:	48 8d 05 38 2c 00 00 	lea    rax,[rip+0x2c38]        # 4b80 <CHUNK_DEPTH+0xb60>
    1f48:	48 89 c7             	mov    rdi,rax
    1f4b:	e8 d4 1b 00 00       	call   3b24 <prompt>
    1f50:	8b 05 da 55 00 00    	mov    eax,DWORD PTR [rip+0x55da]        # 7530 <be_annoying>
    1f56:	48 98                	cdqe
    1f58:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    1f5f:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    1f66:	00 00 00 00 
    1f6a:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    1f71:	be 00 00 00 00       	mov    esi,0x0
    1f76:	48 89 c7             	mov    rdi,rax
    1f79:	e8 52 f1 ff ff       	call   10d0 <nanosleep@plt>
    1f7e:	48 8d 05 53 2c 00 00 	lea    rax,[rip+0x2c53]        # 4bd8 <CHUNK_DEPTH+0xbb8>
    1f85:	48 89 c7             	mov    rdi,rax
    1f88:	e8 7c f2 ff ff       	call   1209 <raw_print>
    1f8d:	8b 05 9d 55 00 00    	mov    eax,DWORD PTR [rip+0x559d]        # 7530 <be_annoying>
    1f93:	48 98                	cdqe
    1f95:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    1f9c:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    1fa3:	00 00 00 00 
    1fa7:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    1fae:	be 00 00 00 00       	mov    esi,0x0
    1fb3:	48 89 c7             	mov    rdi,rax
    1fb6:	e8 15 f1 ff ff       	call   10d0 <nanosleep@plt>
    1fbb:	48 8d 05 56 2c 00 00 	lea    rax,[rip+0x2c56]        # 4c18 <CHUNK_DEPTH+0xbf8>
    1fc2:	48 89 c7             	mov    rdi,rax
    1fc5:	e8 3f f2 ff ff       	call   1209 <raw_print>
    1fca:	8b 05 60 55 00 00    	mov    eax,DWORD PTR [rip+0x5560]        # 7530 <be_annoying>
    1fd0:	48 98                	cdqe
    1fd2:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    1fd9:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    1fe0:	00 00 00 00 
    1fe4:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    1feb:	be 00 00 00 00       	mov    esi,0x0
    1ff0:	48 89 c7             	mov    rdi,rax
    1ff3:	e8 d8 f0 ff ff       	call   10d0 <nanosleep@plt>
    1ff8:	48 8d 05 61 2c 00 00 	lea    rax,[rip+0x2c61]        # 4c60 <CHUNK_DEPTH+0xc40>
    1fff:	48 89 c7             	mov    rdi,rax
    2002:	e8 02 f2 ff ff       	call   1209 <raw_print>
    2007:	8b 05 23 55 00 00    	mov    eax,DWORD PTR [rip+0x5523]        # 7530 <be_annoying>
    200d:	48 98                	cdqe
    200f:	48 89 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],rax
    2016:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    201d:	00 00 00 00 
    2021:	48 8d 85 a0 fe ff ff 	lea    rax,[rbp-0x160]
    2028:	be 00 00 00 00       	mov    esi,0x0
    202d:	48 89 c7             	mov    rdi,rax
    2030:	e8 9b f0 ff ff       	call   10d0 <nanosleep@plt>
    2035:	48 8d 05 74 2c 00 00 	lea    rax,[rip+0x2c74]        # 4cb0 <CHUNK_DEPTH+0xc90>
    203c:	48 89 c7             	mov    rdi,rax
    203f:	e8 c5 f1 ff ff       	call   1209 <raw_print>
    2044:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    204b:	be 00 01 00 00       	mov    esi,0x100
    2050:	48 89 c7             	mov    rdi,rax
    2053:	e8 44 f3 ff ff       	call   139c <raw_readline>
    2058:	48 85 c0             	test   rax,rax
    205b:	75 0f                	jne    206c <start_service+0x18b>
    205d:	48 8d 05 b4 27 00 00 	lea    rax,[rip+0x27b4]        # 4818 <CHUNK_DEPTH+0x7f8>
    2064:	48 89 c7             	mov    rdi,rax
    2067:	e8 9d f1 ff ff       	call   1209 <raw_print>
    206c:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    2073:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    207a:	48 89 d6             	mov    rsi,rdx
    207d:	48 89 c7             	mov    rdi,rax
    2080:	e8 ac f3 ff ff       	call   1431 <raw_parse_int>
    2085:	8b 05 a5 54 00 00    	mov    eax,DWORD PTR [rip+0x54a5]        # 7530 <be_annoying>
    208b:	48 98                	cdqe
    208d:	48 89 85 90 fe ff ff 	mov    QWORD PTR [rbp-0x170],rax
    2094:	48 c7 85 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],0x0
    209b:	00 00 00 00 
    209f:	48 8d 85 90 fe ff ff 	lea    rax,[rbp-0x170]
    20a6:	be 00 00 00 00       	mov    esi,0x0
    20ab:	48 89 c7             	mov    rdi,rax
    20ae:	e8 1d f0 ff ff       	call   10d0 <nanosleep@plt>
    20b3:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    20b9:	83 f8 01             	cmp    eax,0x1
    20bc:	74 0a                	je     20c8 <start_service+0x1e7>
    20be:	83 f8 02             	cmp    eax,0x2
    20c1:	74 51                	je     2114 <start_service+0x233>
    20c3:	e9 95 00 00 00       	jmp    215d <start_service+0x27c>
    20c8:	48 8d 05 49 2c 00 00 	lea    rax,[rip+0x2c49]        # 4d18 <CHUNK_DEPTH+0xcf8>
    20cf:	48 89 c7             	mov    rdi,rax
    20d2:	e8 32 f1 ff ff       	call   1209 <raw_print>
    20d7:	8b 05 53 54 00 00    	mov    eax,DWORD PTR [rip+0x5453]        # 7530 <be_annoying>
    20dd:	48 98                	cdqe
    20df:	48 89 85 60 fe ff ff 	mov    QWORD PTR [rbp-0x1a0],rax
    20e6:	48 c7 85 68 fe ff ff 	mov    QWORD PTR [rbp-0x198],0x0
    20ed:	00 00 00 00 
    20f1:	48 8d 85 60 fe ff ff 	lea    rax,[rbp-0x1a0]
    20f8:	be 00 00 00 00       	mov    esi,0x0
    20fd:	48 89 c7             	mov    rdi,rax
    2100:	e8 cb ef ff ff       	call   10d0 <nanosleep@plt>
    2105:	c7 05 71 54 00 00 01 	mov    DWORD PTR [rip+0x5471],0x1        # 7580 <userData>
    210c:	00 00 00 
    210f:	e9 91 00 00 00       	jmp    21a5 <start_service+0x2c4>
    2114:	48 8d 05 25 2c 00 00 	lea    rax,[rip+0x2c25]        # 4d40 <CHUNK_DEPTH+0xd20>
    211b:	48 89 c7             	mov    rdi,rax
    211e:	e8 e6 f0 ff ff       	call   1209 <raw_print>
    2123:	8b 05 07 54 00 00    	mov    eax,DWORD PTR [rip+0x5407]        # 7530 <be_annoying>
    2129:	48 98                	cdqe
    212b:	48 89 85 50 fe ff ff 	mov    QWORD PTR [rbp-0x1b0],rax
    2132:	48 c7 85 58 fe ff ff 	mov    QWORD PTR [rbp-0x1a8],0x0
    2139:	00 00 00 00 
    213d:	48 8d 85 50 fe ff ff 	lea    rax,[rbp-0x1b0]
    2144:	be 00 00 00 00       	mov    esi,0x0
    2149:	48 89 c7             	mov    rdi,rax
    214c:	e8 7f ef ff ff       	call   10d0 <nanosleep@plt>
    2151:	c7 05 25 54 00 00 02 	mov    DWORD PTR [rip+0x5425],0x2        # 7580 <userData>
    2158:	00 00 00 
    215b:	eb 48                	jmp    21a5 <start_service+0x2c4>
    215d:	48 8d 05 14 2c 00 00 	lea    rax,[rip+0x2c14]        # 4d78 <CHUNK_DEPTH+0xd58>
    2164:	48 89 c7             	mov    rdi,rax
    2167:	e8 9d f0 ff ff       	call   1209 <raw_print>
    216c:	8b 05 be 53 00 00    	mov    eax,DWORD PTR [rip+0x53be]        # 7530 <be_annoying>
    2172:	48 98                	cdqe
    2174:	48 89 85 40 fe ff ff 	mov    QWORD PTR [rbp-0x1c0],rax
    217b:	48 c7 85 48 fe ff ff 	mov    QWORD PTR [rbp-0x1b8],0x0
    2182:	00 00 00 00 
    2186:	48 8d 85 40 fe ff ff 	lea    rax,[rbp-0x1c0]
    218d:	be 00 00 00 00       	mov    esi,0x0
    2192:	48 89 c7             	mov    rdi,rax
    2195:	e8 36 ef ff ff       	call   10d0 <nanosleep@plt>
    219a:	c7 05 dc 53 00 00 03 	mov    DWORD PTR [rip+0x53dc],0x3        # 7580 <userData>
    21a1:	00 00 00 
    21a4:	90                   	nop
    21a5:	ba 00 00 00 00       	mov    edx,0x0
    21aa:	be 00 00 00 00       	mov    esi,0x0
    21af:	48 8d 05 0a 2c 00 00 	lea    rax,[rip+0x2c0a]        # 4dc0 <CHUNK_DEPTH+0xda0>
    21b6:	48 89 c7             	mov    rdi,rax
    21b9:	e8 66 19 00 00       	call   3b24 <prompt>
    21be:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    21c5:	ba 00 01 00 00       	mov    edx,0x100
    21ca:	48 89 c6             	mov    rsi,rax
    21cd:	48 8d 05 4c 2c 00 00 	lea    rax,[rip+0x2c4c]        # 4e20 <CHUNK_DEPTH+0xe00>
    21d4:	48 89 c7             	mov    rdi,rax
    21d7:	e8 48 19 00 00       	call   3b24 <prompt>
    21dc:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    21e3:	ba 00 01 00 00       	mov    edx,0x100
    21e8:	48 89 c6             	mov    rsi,rax
    21eb:	48 8d 05 76 2c 00 00 	lea    rax,[rip+0x2c76]        # 4e68 <CHUNK_DEPTH+0xe48>
    21f2:	48 89 c7             	mov    rdi,rax
    21f5:	e8 2a 19 00 00       	call   3b24 <prompt>
    21fa:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2201:	ba 00 01 00 00       	mov    edx,0x100
    2206:	48 89 c6             	mov    rsi,rax
    2209:	48 8d 05 88 2c 00 00 	lea    rax,[rip+0x2c88]        # 4e98 <CHUNK_DEPTH+0xe78>
    2210:	48 89 c7             	mov    rdi,rax
    2213:	e8 0c 19 00 00       	call   3b24 <prompt>
    2218:	ba 00 00 00 00       	mov    edx,0x0
    221d:	be 00 00 00 00       	mov    esi,0x0
    2222:	48 8d 05 99 2c 00 00 	lea    rax,[rip+0x2c99]        # 4ec2 <CHUNK_DEPTH+0xea2>
    2229:	48 89 c7             	mov    rdi,rax
    222c:	e8 f3 18 00 00       	call   3b24 <prompt>
    2231:	c7 05 49 53 00 00 01 	mov    DWORD PTR [rip+0x5349],0x1        # 7584 <userData+0x4>
    2238:	00 00 00 
    223b:	48 8d 05 9e 2c 00 00 	lea    rax,[rip+0x2c9e]        # 4ee0 <CHUNK_DEPTH+0xec0>
    2242:	48 89 c7             	mov    rdi,rax
    2245:	e8 bf ef ff ff       	call   1209 <raw_print>
    224a:	8b 05 e0 52 00 00    	mov    eax,DWORD PTR [rip+0x52e0]        # 7530 <be_annoying>
    2250:	48 98                	cdqe
    2252:	48 89 85 80 fe ff ff 	mov    QWORD PTR [rbp-0x180],rax
    2259:	48 c7 85 88 fe ff ff 	mov    QWORD PTR [rbp-0x178],0x0
    2260:	00 00 00 00 
    2264:	48 8d 85 80 fe ff ff 	lea    rax,[rbp-0x180]
    226b:	be 00 00 00 00       	mov    esi,0x0
    2270:	48 89 c7             	mov    rdi,rax
    2273:	e8 58 ee ff ff       	call   10d0 <nanosleep@plt>
    2278:	e8 e7 16 00 00       	call   3964 <payment_info>
    227d:	48 8d 05 b4 2c 00 00 	lea    rax,[rip+0x2cb4]        # 4f38 <CHUNK_DEPTH+0xf18>
    2284:	48 89 c7             	mov    rdi,rax
    2287:	e8 7d ef ff ff       	call   1209 <raw_print>
    228c:	8b 05 9e 52 00 00    	mov    eax,DWORD PTR [rip+0x529e]        # 7530 <be_annoying>
    2292:	48 98                	cdqe
    2294:	48 89 85 70 fe ff ff 	mov    QWORD PTR [rbp-0x190],rax
    229b:	48 c7 85 78 fe ff ff 	mov    QWORD PTR [rbp-0x188],0x0
    22a2:	00 00 00 00 
    22a6:	48 8d 85 70 fe ff ff 	lea    rax,[rbp-0x190]
    22ad:	be 00 00 00 00       	mov    esi,0x0
    22b2:	48 89 c7             	mov    rdi,rax
    22b5:	e8 16 ee ff ff       	call   10d0 <nanosleep@plt>
    22ba:	48 8d 05 af 2c 00 00 	lea    rax,[rip+0x2caf]        # 4f70 <CHUNK_DEPTH+0xf50>
    22c1:	48 89 c7             	mov    rdi,rax
    22c4:	e8 40 ef ff ff       	call   1209 <raw_print>
    22c9:	b8 00 00 00 00       	mov    eax,0x0
    22ce:	c9                   	leave
    22cf:	c3                   	ret

00000000000022d0 <report_outage>:
    22d0:	f3 0f 1e fa          	endbr64
    22d4:	55                   	push   rbp
    22d5:	48 89 e5             	mov    rbp,rsp
    22d8:	48 81 ec 50 01 00 00 	sub    rsp,0x150
    22df:	48 8d 05 da 2c 00 00 	lea    rax,[rip+0x2cda]        # 4fc0 <CHUNK_DEPTH+0xfa0>
    22e6:	48 89 c7             	mov    rdi,rax
    22e9:	e8 1b ef ff ff       	call   1209 <raw_print>
    22ee:	8b 05 3c 52 00 00    	mov    eax,DWORD PTR [rip+0x523c]        # 7530 <be_annoying>
    22f4:	48 98                	cdqe
    22f6:	48 89 85 f0 fe ff ff 	mov    QWORD PTR [rbp-0x110],rax
    22fd:	48 c7 85 f8 fe ff ff 	mov    QWORD PTR [rbp-0x108],0x0
    2304:	00 00 00 00 
    2308:	48 8d 85 f0 fe ff ff 	lea    rax,[rbp-0x110]
    230f:	be 00 00 00 00       	mov    esi,0x0
    2314:	48 89 c7             	mov    rdi,rax
    2317:	e8 b4 ed ff ff       	call   10d0 <nanosleep@plt>
    231c:	48 8d 05 dd 2c 00 00 	lea    rax,[rip+0x2cdd]        # 5000 <CHUNK_DEPTH+0xfe0>
    2323:	48 89 c7             	mov    rdi,rax
    2326:	e8 de ee ff ff       	call   1209 <raw_print>
    232b:	8b 05 ff 51 00 00    	mov    eax,DWORD PTR [rip+0x51ff]        # 7530 <be_annoying>
    2331:	48 98                	cdqe
    2333:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    233a:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    2341:	00 00 00 00 
    2345:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    234c:	be 00 00 00 00       	mov    esi,0x0
    2351:	48 89 c7             	mov    rdi,rax
    2354:	e8 77 ed ff ff       	call   10d0 <nanosleep@plt>
    2359:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2360:	be 00 01 00 00       	mov    esi,0x100
    2365:	48 89 c7             	mov    rdi,rax
    2368:	e8 2f f0 ff ff       	call   139c <raw_readline>
    236d:	8b 05 bd 51 00 00    	mov    eax,DWORD PTR [rip+0x51bd]        # 7530 <be_annoying>
    2373:	48 98                	cdqe
    2375:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    237c:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    2383:	00 00 00 00 
    2387:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    238e:	be 00 00 00 00       	mov    esi,0x0
    2393:	48 89 c7             	mov    rdi,rax
    2396:	e8 35 ed ff ff       	call   10d0 <nanosleep@plt>
    239b:	48 8d 05 86 2c 00 00 	lea    rax,[rip+0x2c86]        # 5028 <CHUNK_DEPTH+0x1008>
    23a2:	48 89 c7             	mov    rdi,rax
    23a5:	e8 5f ee ff ff       	call   1209 <raw_print>
    23aa:	8b 05 80 51 00 00    	mov    eax,DWORD PTR [rip+0x5180]        # 7530 <be_annoying>
    23b0:	48 98                	cdqe
    23b2:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    23b9:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    23c0:	00 00 00 00 
    23c4:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    23cb:	be 00 00 00 00       	mov    esi,0x0
    23d0:	48 89 c7             	mov    rdi,rax
    23d3:	e8 f8 ec ff ff       	call   10d0 <nanosleep@plt>
    23d8:	48 8d 05 6b 2c 00 00 	lea    rax,[rip+0x2c6b]        # 504a <CHUNK_DEPTH+0x102a>
    23df:	48 89 c7             	mov    rdi,rax
    23e2:	e8 22 ee ff ff       	call   1209 <raw_print>
    23e7:	8b 05 43 51 00 00    	mov    eax,DWORD PTR [rip+0x5143]        # 7530 <be_annoying>
    23ed:	48 98                	cdqe
    23ef:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    23f6:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    23fd:	00 00 00 00 
    2401:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    2408:	be 00 00 00 00       	mov    esi,0x0
    240d:	48 89 c7             	mov    rdi,rax
    2410:	e8 bb ec ff ff       	call   10d0 <nanosleep@plt>
    2415:	e8 91 f6 ff ff       	call   1aab <start_position>
    241a:	c9                   	leave
    241b:	c3                   	ret

000000000000241c <billing_department>:
    241c:	f3 0f 1e fa          	endbr64
    2420:	55                   	push   rbp
    2421:	48 89 e5             	mov    rbp,rsp
    2424:	48 81 ec 80 01 00 00 	sub    rsp,0x180
    242b:	48 8d 05 26 2c 00 00 	lea    rax,[rip+0x2c26]        # 5058 <CHUNK_DEPTH+0x1038>
    2432:	48 89 c7             	mov    rdi,rax
    2435:	e8 cf ed ff ff       	call   1209 <raw_print>
    243a:	8b 05 f0 50 00 00    	mov    eax,DWORD PTR [rip+0x50f0]        # 7530 <be_annoying>
    2440:	48 98                	cdqe
    2442:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    2449:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    2450:	00 00 00 00 
    2454:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    245b:	be 00 00 00 00       	mov    esi,0x0
    2460:	48 89 c7             	mov    rdi,rax
    2463:	e8 68 ec ff ff       	call   10d0 <nanosleep@plt>
    2468:	e8 85 15 00 00       	call   39f2 <login_roleplay>
    246d:	48 8d 05 0c 2c 00 00 	lea    rax,[rip+0x2c0c]        # 5080 <CHUNK_DEPTH+0x1060>
    2474:	48 89 c7             	mov    rdi,rax
    2477:	e8 8d ed ff ff       	call   1209 <raw_print>
    247c:	8b 05 ae 50 00 00    	mov    eax,DWORD PTR [rip+0x50ae]        # 7530 <be_annoying>
    2482:	48 98                	cdqe
    2484:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    248b:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    2492:	00 00 00 00 
    2496:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    249d:	be 00 00 00 00       	mov    esi,0x0
    24a2:	48 89 c7             	mov    rdi,rax
    24a5:	e8 26 ec ff ff       	call   10d0 <nanosleep@plt>
    24aa:	48 8d 05 ff 2b 00 00 	lea    rax,[rip+0x2bff]        # 50b0 <CHUNK_DEPTH+0x1090>
    24b1:	48 89 c7             	mov    rdi,rax
    24b4:	e8 50 ed ff ff       	call   1209 <raw_print>
    24b9:	8b 05 71 50 00 00    	mov    eax,DWORD PTR [rip+0x5071]        # 7530 <be_annoying>
    24bf:	48 98                	cdqe
    24c1:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    24c8:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    24cf:	00 00 00 00 
    24d3:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    24da:	be 00 00 00 00       	mov    esi,0x0
    24df:	48 89 c7             	mov    rdi,rax
    24e2:	e8 e9 eb ff ff       	call   10d0 <nanosleep@plt>
    24e7:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    24ee:	be 00 01 00 00       	mov    esi,0x100
    24f3:	48 89 c7             	mov    rdi,rax
    24f6:	e8 a1 ee ff ff       	call   139c <raw_readline>
    24fb:	48 85 c0             	test   rax,rax
    24fe:	75 0f                	jne    250f <billing_department+0xf3>
    2500:	48 8d 05 11 23 00 00 	lea    rax,[rip+0x2311]        # 4818 <CHUNK_DEPTH+0x7f8>
    2507:	48 89 c7             	mov    rdi,rax
    250a:	e8 fa ec ff ff       	call   1209 <raw_print>
    250f:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    2516:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    251d:	48 89 d6             	mov    rsi,rdx
    2520:	48 89 c7             	mov    rdi,rax
    2523:	e8 09 ef ff ff       	call   1431 <raw_parse_int>
    2528:	8b 05 02 50 00 00    	mov    eax,DWORD PTR [rip+0x5002]        # 7530 <be_annoying>
    252e:	48 98                	cdqe
    2530:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    2537:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    253e:	00 00 00 00 
    2542:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    2549:	be 00 00 00 00       	mov    esi,0x0
    254e:	48 89 c7             	mov    rdi,rax
    2551:	e8 7a eb ff ff       	call   10d0 <nanosleep@plt>
    2556:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    255c:	83 f8 01             	cmp    eax,0x1
    255f:	74 07                	je     2568 <billing_department+0x14c>
    2561:	83 f8 02             	cmp    eax,0x2
    2564:	74 41                	je     25a7 <billing_department+0x18b>
    2566:	eb 7e                	jmp    25e6 <billing_department+0x1ca>
    2568:	48 8d 05 89 2b 00 00 	lea    rax,[rip+0x2b89]        # 50f8 <CHUNK_DEPTH+0x10d8>
    256f:	48 89 c7             	mov    rdi,rax
    2572:	e8 92 ec ff ff       	call   1209 <raw_print>
    2577:	8b 05 b3 4f 00 00    	mov    eax,DWORD PTR [rip+0x4fb3]        # 7530 <be_annoying>
    257d:	48 98                	cdqe
    257f:	48 89 85 90 fe ff ff 	mov    QWORD PTR [rbp-0x170],rax
    2586:	48 c7 85 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],0x0
    258d:	00 00 00 00 
    2591:	48 8d 85 90 fe ff ff 	lea    rax,[rbp-0x170]
    2598:	be 00 00 00 00       	mov    esi,0x0
    259d:	48 89 c7             	mov    rdi,rax
    25a0:	e8 2b eb ff ff       	call   10d0 <nanosleep@plt>
    25a5:	eb 46                	jmp    25ed <billing_department+0x1d1>
    25a7:	48 8d 05 ea 2b 00 00 	lea    rax,[rip+0x2bea]        # 5198 <CHUNK_DEPTH+0x1178>
    25ae:	48 89 c7             	mov    rdi,rax
    25b1:	e8 53 ec ff ff       	call   1209 <raw_print>
    25b6:	8b 05 74 4f 00 00    	mov    eax,DWORD PTR [rip+0x4f74]        # 7530 <be_annoying>
    25bc:	48 98                	cdqe
    25be:	48 89 85 80 fe ff ff 	mov    QWORD PTR [rbp-0x180],rax
    25c5:	48 c7 85 88 fe ff ff 	mov    QWORD PTR [rbp-0x178],0x0
    25cc:	00 00 00 00 
    25d0:	48 8d 85 80 fe ff ff 	lea    rax,[rbp-0x180]
    25d7:	be 00 00 00 00       	mov    esi,0x0
    25dc:	48 89 c7             	mov    rdi,rax
    25df:	e8 ec ea ff ff       	call   10d0 <nanosleep@plt>
    25e4:	eb 07                	jmp    25ed <billing_department+0x1d1>
    25e6:	e8 31 fe ff ff       	call   241c <billing_department>
    25eb:	eb 47                	jmp    2634 <billing_department+0x218>
    25ed:	e8 72 13 00 00       	call   3964 <payment_info>
    25f2:	48 8d 05 c7 2b 00 00 	lea    rax,[rip+0x2bc7]        # 51c0 <CHUNK_DEPTH+0x11a0>
    25f9:	48 89 c7             	mov    rdi,rax
    25fc:	e8 08 ec ff ff       	call   1209 <raw_print>
    2601:	8b 05 29 4f 00 00    	mov    eax,DWORD PTR [rip+0x4f29]        # 7530 <be_annoying>
    2607:	48 98                	cdqe
    2609:	48 89 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],rax
    2610:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    2617:	00 00 00 00 
    261b:	48 8d 85 a0 fe ff ff 	lea    rax,[rbp-0x160]
    2622:	be 00 00 00 00       	mov    esi,0x0
    2627:	48 89 c7             	mov    rdi,rax
    262a:	e8 a1 ea ff ff       	call   10d0 <nanosleep@plt>
    262f:	e8 77 f4 ff ff       	call   1aab <start_position>
    2634:	c9                   	leave
    2635:	c3                   	ret

0000000000002636 <technical_support>:
    2636:	f3 0f 1e fa          	endbr64
    263a:	55                   	push   rbp
    263b:	48 89 e5             	mov    rbp,rsp
    263e:	48 81 ec 60 01 00 00 	sub    rsp,0x160
    2645:	48 8d 05 94 2b 00 00 	lea    rax,[rip+0x2b94]        # 51e0 <CHUNK_DEPTH+0x11c0>
    264c:	48 89 c7             	mov    rdi,rax
    264f:	e8 b5 eb ff ff       	call   1209 <raw_print>
    2654:	8b 05 d6 4e 00 00    	mov    eax,DWORD PTR [rip+0x4ed6]        # 7530 <be_annoying>
    265a:	48 98                	cdqe
    265c:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    2663:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    266a:	00 00 00 00 
    266e:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    2675:	be 00 00 00 00       	mov    esi,0x0
    267a:	48 89 c7             	mov    rdi,rax
    267d:	e8 4e ea ff ff       	call   10d0 <nanosleep@plt>
    2682:	48 8d 05 7f 2b 00 00 	lea    rax,[rip+0x2b7f]        # 5208 <CHUNK_DEPTH+0x11e8>
    2689:	48 89 c7             	mov    rdi,rax
    268c:	e8 78 eb ff ff       	call   1209 <raw_print>
    2691:	8b 05 99 4e 00 00    	mov    eax,DWORD PTR [rip+0x4e99]        # 7530 <be_annoying>
    2697:	48 98                	cdqe
    2699:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    26a0:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    26a7:	00 00 00 00 
    26ab:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    26b2:	be 00 00 00 00       	mov    esi,0x0
    26b7:	48 89 c7             	mov    rdi,rax
    26ba:	e8 11 ea ff ff       	call   10d0 <nanosleep@plt>
    26bf:	48 8d 05 7a 2b 00 00 	lea    rax,[rip+0x2b7a]        # 5240 <CHUNK_DEPTH+0x1220>
    26c6:	48 89 c7             	mov    rdi,rax
    26c9:	e8 3b eb ff ff       	call   1209 <raw_print>
    26ce:	8b 05 5c 4e 00 00    	mov    eax,DWORD PTR [rip+0x4e5c]        # 7530 <be_annoying>
    26d4:	48 98                	cdqe
    26d6:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    26dd:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    26e4:	00 00 00 00 
    26e8:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    26ef:	be 00 00 00 00       	mov    esi,0x0
    26f4:	48 89 c7             	mov    rdi,rax
    26f7:	e8 d4 e9 ff ff       	call   10d0 <nanosleep@plt>
    26fc:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2703:	be 00 01 00 00       	mov    esi,0x100
    2708:	48 89 c7             	mov    rdi,rax
    270b:	e8 8c ec ff ff       	call   139c <raw_readline>
    2710:	48 85 c0             	test   rax,rax
    2713:	75 0f                	jne    2724 <technical_support+0xee>
    2715:	48 8d 05 fc 20 00 00 	lea    rax,[rip+0x20fc]        # 4818 <CHUNK_DEPTH+0x7f8>
    271c:	48 89 c7             	mov    rdi,rax
    271f:	e8 e5 ea ff ff       	call   1209 <raw_print>
    2724:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    272b:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2732:	48 89 d6             	mov    rsi,rdx
    2735:	48 89 c7             	mov    rdi,rax
    2738:	e8 f4 ec ff ff       	call   1431 <raw_parse_int>
    273d:	8b 05 ed 4d 00 00    	mov    eax,DWORD PTR [rip+0x4ded]        # 7530 <be_annoying>
    2743:	48 98                	cdqe
    2745:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    274c:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    2753:	00 00 00 00 
    2757:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    275e:	be 00 00 00 00       	mov    esi,0x0
    2763:	48 89 c7             	mov    rdi,rax
    2766:	e8 65 e9 ff ff       	call   10d0 <nanosleep@plt>
    276b:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    2771:	83 f8 01             	cmp    eax,0x1
    2774:	74 07                	je     277d <technical_support+0x147>
    2776:	83 f8 02             	cmp    eax,0x2
    2779:	74 09                	je     2784 <technical_support+0x14e>
    277b:	eb 4b                	jmp    27c8 <technical_support+0x192>
    277d:	e8 4e fb ff ff       	call   22d0 <report_outage>
    2782:	eb 4b                	jmp    27cf <technical_support+0x199>
    2784:	e8 69 12 00 00       	call   39f2 <login_roleplay>
    2789:	48 8d 05 e0 2a 00 00 	lea    rax,[rip+0x2ae0]        # 5270 <CHUNK_DEPTH+0x1250>
    2790:	48 89 c7             	mov    rdi,rax
    2793:	e8 71 ea ff ff       	call   1209 <raw_print>
    2798:	8b 05 92 4d 00 00    	mov    eax,DWORD PTR [rip+0x4d92]        # 7530 <be_annoying>
    279e:	48 98                	cdqe
    27a0:	48 89 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],rax
    27a7:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    27ae:	00 00 00 00 
    27b2:	48 8d 85 a0 fe ff ff 	lea    rax,[rbp-0x160]
    27b9:	be 00 00 00 00       	mov    esi,0x0
    27be:	48 89 c7             	mov    rdi,rax
    27c1:	e8 0a e9 ff ff       	call   10d0 <nanosleep@plt>
    27c6:	eb 07                	jmp    27cf <technical_support+0x199>
    27c8:	e8 69 fe ff ff       	call   2636 <technical_support>
    27cd:	eb 05                	jmp    27d4 <technical_support+0x19e>
    27cf:	e8 d7 f2 ff ff       	call   1aab <start_position>
    27d4:	c9                   	leave
    27d5:	c3                   	ret

00000000000027d6 <upgrade_or_change>:
    27d6:	f3 0f 1e fa          	endbr64
    27da:	55                   	push   rbp
    27db:	48 89 e5             	mov    rbp,rsp
    27de:	48 81 ec 90 01 00 00 	sub    rsp,0x190
    27e5:	e8 f4 ed ff ff       	call   15de <get_a_fun_fact>
    27ea:	48 8d 05 cf 2a 00 00 	lea    rax,[rip+0x2acf]        # 52c0 <CHUNK_DEPTH+0x12a0>
    27f1:	48 89 c7             	mov    rdi,rax
    27f4:	e8 10 ea ff ff       	call   1209 <raw_print>
    27f9:	8b 05 31 4d 00 00    	mov    eax,DWORD PTR [rip+0x4d31]        # 7530 <be_annoying>
    27ff:	48 98                	cdqe
    2801:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    2808:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    280f:	00 00 00 00 
    2813:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    281a:	be 00 00 00 00       	mov    esi,0x0
    281f:	48 89 c7             	mov    rdi,rax
    2822:	e8 a9 e8 ff ff       	call   10d0 <nanosleep@plt>
    2827:	48 8d 05 ca 2a 00 00 	lea    rax,[rip+0x2aca]        # 52f8 <CHUNK_DEPTH+0x12d8>
    282e:	48 89 c7             	mov    rdi,rax
    2831:	e8 d3 e9 ff ff       	call   1209 <raw_print>
    2836:	8b 05 f4 4c 00 00    	mov    eax,DWORD PTR [rip+0x4cf4]        # 7530 <be_annoying>
    283c:	48 98                	cdqe
    283e:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    2845:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    284c:	00 00 00 00 
    2850:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    2857:	be 00 00 00 00       	mov    esi,0x0
    285c:	48 89 c7             	mov    rdi,rax
    285f:	e8 6c e8 ff ff       	call   10d0 <nanosleep@plt>
    2864:	48 8d 05 0d 2b 00 00 	lea    rax,[rip+0x2b0d]        # 5378 <CHUNK_DEPTH+0x1358>
    286b:	48 89 c7             	mov    rdi,rax
    286e:	e8 96 e9 ff ff       	call   1209 <raw_print>
    2873:	8b 05 b7 4c 00 00    	mov    eax,DWORD PTR [rip+0x4cb7]        # 7530 <be_annoying>
    2879:	48 98                	cdqe
    287b:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    2882:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    2889:	00 00 00 00 
    288d:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    2894:	be 00 00 00 00       	mov    esi,0x0
    2899:	48 89 c7             	mov    rdi,rax
    289c:	e8 2f e8 ff ff       	call   10d0 <nanosleep@plt>
    28a1:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    28a8:	be 00 01 00 00       	mov    esi,0x100
    28ad:	48 89 c7             	mov    rdi,rax
    28b0:	e8 e7 ea ff ff       	call   139c <raw_readline>
    28b5:	48 85 c0             	test   rax,rax
    28b8:	75 0f                	jne    28c9 <upgrade_or_change+0xf3>
    28ba:	48 8d 05 57 1f 00 00 	lea    rax,[rip+0x1f57]        # 4818 <CHUNK_DEPTH+0x7f8>
    28c1:	48 89 c7             	mov    rdi,rax
    28c4:	e8 40 e9 ff ff       	call   1209 <raw_print>
    28c9:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    28d0:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    28d7:	48 89 d6             	mov    rsi,rdx
    28da:	48 89 c7             	mov    rdi,rax
    28dd:	e8 4f eb ff ff       	call   1431 <raw_parse_int>
    28e2:	8b 05 48 4c 00 00    	mov    eax,DWORD PTR [rip+0x4c48]        # 7530 <be_annoying>
    28e8:	48 98                	cdqe
    28ea:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    28f1:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    28f8:	00 00 00 00 
    28fc:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    2903:	be 00 00 00 00       	mov    esi,0x0
    2908:	48 89 c7             	mov    rdi,rax
    290b:	e8 c0 e7 ff ff       	call   10d0 <nanosleep@plt>
    2910:	8b 05 6e 4c 00 00    	mov    eax,DWORD PTR [rip+0x4c6e]        # 7584 <userData+0x4>
    2916:	85 c0                	test   eax,eax
    2918:	75 05                	jne    291f <upgrade_or_change+0x149>
    291a:	e8 d3 10 00 00       	call   39f2 <login_roleplay>
    291f:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    2925:	83 f8 01             	cmp    eax,0x1
    2928:	74 0e                	je     2938 <upgrade_or_change+0x162>
    292a:	83 f8 02             	cmp    eax,0x2
    292d:	0f 84 a0 00 00 00    	je     29d3 <upgrade_or_change+0x1fd>
    2933:	e9 df 00 00 00       	jmp    2a17 <upgrade_or_change+0x241>
    2938:	8b 05 42 4c 00 00    	mov    eax,DWORD PTR [rip+0x4c42]        # 7580 <userData>
    293e:	83 f8 03             	cmp    eax,0x3
    2941:	74 51                	je     2994 <upgrade_or_change+0x1be>
    2943:	48 8d 05 a6 2a 00 00 	lea    rax,[rip+0x2aa6]        # 53f0 <CHUNK_DEPTH+0x13d0>
    294a:	48 89 c7             	mov    rdi,rax
    294d:	e8 b7 e8 ff ff       	call   1209 <raw_print>
    2952:	8b 05 d8 4b 00 00    	mov    eax,DWORD PTR [rip+0x4bd8]        # 7530 <be_annoying>
    2958:	48 98                	cdqe
    295a:	48 89 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],rax
    2961:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    2968:	00 00 00 00 
    296c:	48 8d 85 a0 fe ff ff 	lea    rax,[rbp-0x160]
    2973:	be 00 00 00 00       	mov    esi,0x0
    2978:	48 89 c7             	mov    rdi,rax
    297b:	e8 50 e7 ff ff       	call   10d0 <nanosleep@plt>
    2980:	c7 05 f6 4b 00 00 03 	mov    DWORD PTR [rip+0x4bf6],0x3        # 7580 <userData>
    2987:	00 00 00 
    298a:	e8 1c f1 ff ff       	call   1aab <start_position>
    298f:	e9 8a 00 00 00       	jmp    2a1e <upgrade_or_change+0x248>
    2994:	48 8d 05 a5 2a 00 00 	lea    rax,[rip+0x2aa5]        # 5440 <CHUNK_DEPTH+0x1420>
    299b:	48 89 c7             	mov    rdi,rax
    299e:	e8 66 e8 ff ff       	call   1209 <raw_print>
    29a3:	8b 05 87 4b 00 00    	mov    eax,DWORD PTR [rip+0x4b87]        # 7530 <be_annoying>
    29a9:	48 98                	cdqe
    29ab:	48 89 85 90 fe ff ff 	mov    QWORD PTR [rbp-0x170],rax
    29b2:	48 c7 85 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],0x0
    29b9:	00 00 00 00 
    29bd:	48 8d 85 90 fe ff ff 	lea    rax,[rbp-0x170]
    29c4:	be 00 00 00 00       	mov    esi,0x0
    29c9:	48 89 c7             	mov    rdi,rax
    29cc:	e8 ff e6 ff ff       	call   10d0 <nanosleep@plt>
    29d1:	eb 4b                	jmp    2a1e <upgrade_or_change+0x248>
    29d3:	48 8d 05 9e 2a 00 00 	lea    rax,[rip+0x2a9e]        # 5478 <CHUNK_DEPTH+0x1458>
    29da:	48 89 c7             	mov    rdi,rax
    29dd:	e8 27 e8 ff ff       	call   1209 <raw_print>
    29e2:	8b 05 48 4b 00 00    	mov    eax,DWORD PTR [rip+0x4b48]        # 7530 <be_annoying>
    29e8:	48 98                	cdqe
    29ea:	48 89 85 80 fe ff ff 	mov    QWORD PTR [rbp-0x180],rax
    29f1:	48 c7 85 88 fe ff ff 	mov    QWORD PTR [rbp-0x178],0x0
    29f8:	00 00 00 00 
    29fc:	48 8d 85 80 fe ff ff 	lea    rax,[rbp-0x180]
    2a03:	be 00 00 00 00       	mov    esi,0x0
    2a08:	48 89 c7             	mov    rdi,rax
    2a0b:	e8 c0 e6 ff ff       	call   10d0 <nanosleep@plt>
    2a10:	e8 cc f4 ff ff       	call   1ee1 <start_service>
    2a15:	eb 0c                	jmp    2a23 <upgrade_or_change+0x24d>
    2a17:	e8 ba fd ff ff       	call   27d6 <upgrade_or_change>
    2a1c:	eb 05                	jmp    2a23 <upgrade_or_change+0x24d>
    2a1e:	e8 88 f0 ff ff       	call   1aab <start_position>
    2a23:	c9                   	leave
    2a24:	c3                   	ret

0000000000002a25 <other_inquiries>:
    2a25:	f3 0f 1e fa          	endbr64
    2a29:	55                   	push   rbp
    2a2a:	48 89 e5             	mov    rbp,rsp
    2a2d:	48 81 ec 90 01 00 00 	sub    rsp,0x190
    2a34:	e8 a5 eb ff ff       	call   15de <get_a_fun_fact>
    2a39:	48 8d 05 a0 2a 00 00 	lea    rax,[rip+0x2aa0]        # 54e0 <CHUNK_DEPTH+0x14c0>
    2a40:	48 89 c7             	mov    rdi,rax
    2a43:	e8 c1 e7 ff ff       	call   1209 <raw_print>
    2a48:	8b 05 e2 4a 00 00    	mov    eax,DWORD PTR [rip+0x4ae2]        # 7530 <be_annoying>
    2a4e:	48 98                	cdqe
    2a50:	48 89 85 e0 fe ff ff 	mov    QWORD PTR [rbp-0x120],rax
    2a57:	48 c7 85 e8 fe ff ff 	mov    QWORD PTR [rbp-0x118],0x0
    2a5e:	00 00 00 00 
    2a62:	48 8d 85 e0 fe ff ff 	lea    rax,[rbp-0x120]
    2a69:	be 00 00 00 00       	mov    esi,0x0
    2a6e:	48 89 c7             	mov    rdi,rax
    2a71:	e8 5a e6 ff ff       	call   10d0 <nanosleep@plt>
    2a76:	48 8d 05 b3 2a 00 00 	lea    rax,[rip+0x2ab3]        # 5530 <CHUNK_DEPTH+0x1510>
    2a7d:	48 89 c7             	mov    rdi,rax
    2a80:	e8 84 e7 ff ff       	call   1209 <raw_print>
    2a85:	8b 05 a5 4a 00 00    	mov    eax,DWORD PTR [rip+0x4aa5]        # 7530 <be_annoying>
    2a8b:	48 98                	cdqe
    2a8d:	48 89 85 d0 fe ff ff 	mov    QWORD PTR [rbp-0x130],rax
    2a94:	48 c7 85 d8 fe ff ff 	mov    QWORD PTR [rbp-0x128],0x0
    2a9b:	00 00 00 00 
    2a9f:	48 8d 85 d0 fe ff ff 	lea    rax,[rbp-0x130]
    2aa6:	be 00 00 00 00       	mov    esi,0x0
    2aab:	48 89 c7             	mov    rdi,rax
    2aae:	e8 1d e6 ff ff       	call   10d0 <nanosleep@plt>
    2ab3:	48 8d 05 a6 2a 00 00 	lea    rax,[rip+0x2aa6]        # 5560 <CHUNK_DEPTH+0x1540>
    2aba:	48 89 c7             	mov    rdi,rax
    2abd:	e8 47 e7 ff ff       	call   1209 <raw_print>
    2ac2:	8b 05 68 4a 00 00    	mov    eax,DWORD PTR [rip+0x4a68]        # 7530 <be_annoying>
    2ac8:	48 98                	cdqe
    2aca:	48 89 85 c0 fe ff ff 	mov    QWORD PTR [rbp-0x140],rax
    2ad1:	48 c7 85 c8 fe ff ff 	mov    QWORD PTR [rbp-0x138],0x0
    2ad8:	00 00 00 00 
    2adc:	48 8d 85 c0 fe ff ff 	lea    rax,[rbp-0x140]
    2ae3:	be 00 00 00 00       	mov    esi,0x0
    2ae8:	48 89 c7             	mov    rdi,rax
    2aeb:	e8 e0 e5 ff ff       	call   10d0 <nanosleep@plt>
    2af0:	48 8d 05 91 2a 00 00 	lea    rax,[rip+0x2a91]        # 5588 <CHUNK_DEPTH+0x1568>
    2af7:	48 89 c7             	mov    rdi,rax
    2afa:	e8 0a e7 ff ff       	call   1209 <raw_print>
    2aff:	8b 05 2b 4a 00 00    	mov    eax,DWORD PTR [rip+0x4a2b]        # 7530 <be_annoying>
    2b05:	48 98                	cdqe
    2b07:	48 89 85 b0 fe ff ff 	mov    QWORD PTR [rbp-0x150],rax
    2b0e:	48 c7 85 b8 fe ff ff 	mov    QWORD PTR [rbp-0x148],0x0
    2b15:	00 00 00 00 
    2b19:	48 8d 85 b0 fe ff ff 	lea    rax,[rbp-0x150]
    2b20:	be 00 00 00 00       	mov    esi,0x0
    2b25:	48 89 c7             	mov    rdi,rax
    2b28:	e8 a3 e5 ff ff       	call   10d0 <nanosleep@plt>
    2b2d:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2b34:	be 00 01 00 00       	mov    esi,0x100
    2b39:	48 89 c7             	mov    rdi,rax
    2b3c:	e8 5b e8 ff ff       	call   139c <raw_readline>
    2b41:	48 85 c0             	test   rax,rax
    2b44:	75 0f                	jne    2b55 <other_inquiries+0x130>
    2b46:	48 8d 05 cb 1c 00 00 	lea    rax,[rip+0x1ccb]        # 4818 <CHUNK_DEPTH+0x7f8>
    2b4d:	48 89 c7             	mov    rdi,rax
    2b50:	e8 b4 e6 ff ff       	call   1209 <raw_print>
    2b55:	48 8d 95 fc fe ff ff 	lea    rdx,[rbp-0x104]
    2b5c:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2b63:	48 89 d6             	mov    rsi,rdx
    2b66:	48 89 c7             	mov    rdi,rax
    2b69:	e8 c3 e8 ff ff       	call   1431 <raw_parse_int>
    2b6e:	8b 05 bc 49 00 00    	mov    eax,DWORD PTR [rip+0x49bc]        # 7530 <be_annoying>
    2b74:	48 98                	cdqe
    2b76:	48 89 85 a0 fe ff ff 	mov    QWORD PTR [rbp-0x160],rax
    2b7d:	48 c7 85 a8 fe ff ff 	mov    QWORD PTR [rbp-0x158],0x0
    2b84:	00 00 00 00 
    2b88:	48 8d 85 a0 fe ff ff 	lea    rax,[rbp-0x160]
    2b8f:	be 00 00 00 00       	mov    esi,0x0
    2b94:	48 89 c7             	mov    rdi,rax
    2b97:	e8 34 e5 ff ff       	call   10d0 <nanosleep@plt>
    2b9c:	8b 85 fc fe ff ff    	mov    eax,DWORD PTR [rbp-0x104]
    2ba2:	83 f8 03             	cmp    eax,0x3
    2ba5:	0f 84 f5 00 00 00    	je     2ca0 <other_inquiries+0x27b>
    2bab:	83 f8 03             	cmp    eax,0x3
    2bae:	0f 8f f3 00 00 00    	jg     2ca7 <other_inquiries+0x282>
    2bb4:	83 f8 01             	cmp    eax,0x1
    2bb7:	74 0e                	je     2bc7 <other_inquiries+0x1a2>
    2bb9:	83 f8 02             	cmp    eax,0x2
    2bbc:	0f 84 d7 00 00 00    	je     2c99 <other_inquiries+0x274>
    2bc2:	e9 e0 00 00 00       	jmp    2ca7 <other_inquiries+0x282>
    2bc7:	48 8d 05 e2 29 00 00 	lea    rax,[rip+0x29e2]        # 55b0 <CHUNK_DEPTH+0x1590>
    2bce:	48 89 c7             	mov    rdi,rax
    2bd1:	e8 33 e6 ff ff       	call   1209 <raw_print>
    2bd6:	8b 05 54 49 00 00    	mov    eax,DWORD PTR [rip+0x4954]        # 7530 <be_annoying>
    2bdc:	48 98                	cdqe
    2bde:	48 89 85 90 fe ff ff 	mov    QWORD PTR [rbp-0x170],rax
    2be5:	48 c7 85 98 fe ff ff 	mov    QWORD PTR [rbp-0x168],0x0
    2bec:	00 00 00 00 
    2bf0:	48 8d 85 90 fe ff ff 	lea    rax,[rbp-0x170]
    2bf7:	be 00 00 00 00       	mov    esi,0x0
    2bfc:	48 89 c7             	mov    rdi,rax
    2bff:	e8 cc e4 ff ff       	call   10d0 <nanosleep@plt>
    2c04:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    2c0b:	be 00 01 00 00       	mov    esi,0x100
    2c10:	48 89 c7             	mov    rdi,rax
    2c13:	e8 84 e7 ff ff       	call   139c <raw_readline>
    2c18:	48 85 c0             	test   rax,rax
    2c1b:	75 0f                	jne    2c2c <other_inquiries+0x207>
    2c1d:	48 8d 05 f4 1b 00 00 	lea    rax,[rip+0x1bf4]        # 4818 <CHUNK_DEPTH+0x7f8>
    2c24:	48 89 c7             	mov    rdi,rax
    2c27:	e8 dd e5 ff ff       	call   1209 <raw_print>
    2c2c:	8b 05 fe 48 00 00    	mov    eax,DWORD PTR [rip+0x48fe]        # 7530 <be_annoying>
    2c32:	48 98                	cdqe
    2c34:	48 89 85 80 fe ff ff 	mov    QWORD PTR [rbp-0x180],rax
    2c3b:	48 c7 85 88 fe ff ff 	mov    QWORD PTR [rbp-0x178],0x0
    2c42:	00 00 00 00 
    2c46:	48 8d 85 80 fe ff ff 	lea    rax,[rbp-0x180]
    2c4d:	be 00 00 00 00       	mov    esi,0x0
    2c52:	48 89 c7             	mov    rdi,rax
    2c55:	e8 76 e4 ff ff       	call   10d0 <nanosleep@plt>
    2c5a:	48 8d 05 e7 29 00 00 	lea    rax,[rip+0x29e7]        # 5648 <CHUNK_DEPTH+0x1628>
    2c61:	48 89 c7             	mov    rdi,rax
    2c64:	e8 a0 e5 ff ff       	call   1209 <raw_print>
    2c69:	8b 05 c1 48 00 00    	mov    eax,DWORD PTR [rip+0x48c1]        # 7530 <be_annoying>
    2c6f:	48 98                	cdqe
    2c71:	48 89 85 70 fe ff ff 	mov    QWORD PTR [rbp-0x190],rax
    2c78:	48 c7 85 78 fe ff ff 	mov    QWORD PTR [rbp-0x188],0x0
    2c7f:	00 00 00 00 
    2c83:	48 8d 85 70 fe ff ff 	lea    rax,[rbp-0x190]
    2c8a:	be 00 00 00 00       	mov    esi,0x0
    2c8f:	48 89 c7             	mov    rdi,rax
    2c92:	e8 39 e4 ff ff       	call   10d0 <nanosleep@plt>
    2c97:	eb 15                	jmp    2cae <other_inquiries+0x289>
    2c99:	e8 12 00 00 00       	call   2cb0 <cancel_plan>
    2c9e:	eb 0e                	jmp    2cae <other_inquiries+0x289>
    2ca0:	e8 d1 0a 00 00       	call   3776 <speak_with_an_operator>
    2ca5:	eb 07                	jmp    2cae <other_inquiries+0x289>
    2ca7:	e8 ca 0a 00 00       	call   3776 <speak_with_an_operator>
    2cac:	eb 00                	jmp    2cae <other_inquiries+0x289>
    2cae:	c9                   	leave
    2caf:	c3                   	ret

0000000000002cb0 <cancel_plan>:
    2cb0:	f3 0f 1e fa          	endbr64
    2cb4:	55                   	push   rbp
    2cb5:	48 89 e5             	mov    rbp,rsp
    2cb8:	48 81 ec 30 04 00 00 	sub    rsp,0x430
    2cbf:	8b 05 bf 48 00 00    	mov    eax,DWORD PTR [rip+0x48bf]        # 7584 <userData+0x4>
    2cc5:	85 c0                	test   eax,eax
    2cc7:	75 05                	jne    2cce <cancel_plan+0x1e>
    2cc9:	e8 24 0d 00 00       	call   39f2 <login_roleplay>
    2cce:	e8 0b e9 ff ff       	call   15de <get_a_fun_fact>
    2cd3:	48 8d 05 8e 29 00 00 	lea    rax,[rip+0x298e]        # 5668 <CHUNK_DEPTH+0x1648>
    2cda:	48 89 c7             	mov    rdi,rax
    2cdd:	e8 27 e5 ff ff       	call   1209 <raw_print>
    2ce2:	8b 05 48 48 00 00    	mov    eax,DWORD PTR [rip+0x4848]        # 7530 <be_annoying>
    2ce8:	48 98                	cdqe
    2cea:	48 89 85 e0 fd ff ff 	mov    QWORD PTR [rbp-0x220],rax
    2cf1:	48 c7 85 e8 fd ff ff 	mov    QWORD PTR [rbp-0x218],0x0
    2cf8:	00 00 00 00 
    2cfc:	48 8d 85 e0 fd ff ff 	lea    rax,[rbp-0x220]
    2d03:	be 00 00 00 00       	mov    esi,0x0
    2d08:	48 89 c7             	mov    rdi,rax
    2d0b:	e8 c0 e3 ff ff       	call   10d0 <nanosleep@plt>
    2d10:	48 8d 05 91 29 00 00 	lea    rax,[rip+0x2991]        # 56a8 <CHUNK_DEPTH+0x1688>
    2d17:	48 89 c7             	mov    rdi,rax
    2d1a:	e8 ea e4 ff ff       	call   1209 <raw_print>
    2d1f:	8b 05 0b 48 00 00    	mov    eax,DWORD PTR [rip+0x480b]        # 7530 <be_annoying>
    2d25:	48 98                	cdqe
    2d27:	48 89 85 d0 fd ff ff 	mov    QWORD PTR [rbp-0x230],rax
    2d2e:	48 c7 85 d8 fd ff ff 	mov    QWORD PTR [rbp-0x228],0x0
    2d35:	00 00 00 00 
    2d39:	48 8d 85 d0 fd ff ff 	lea    rax,[rbp-0x230]
    2d40:	be 00 00 00 00       	mov    esi,0x0
    2d45:	48 89 c7             	mov    rdi,rax
    2d48:	e8 83 e3 ff ff       	call   10d0 <nanosleep@plt>
    2d4d:	48 8d 05 65 29 00 00 	lea    rax,[rip+0x2965]        # 56b9 <CHUNK_DEPTH+0x1699>
    2d54:	48 89 c7             	mov    rdi,rax
    2d57:	e8 ad e4 ff ff       	call   1209 <raw_print>
    2d5c:	8b 05 ce 47 00 00    	mov    eax,DWORD PTR [rip+0x47ce]        # 7530 <be_annoying>
    2d62:	48 98                	cdqe
    2d64:	48 89 85 c0 fd ff ff 	mov    QWORD PTR [rbp-0x240],rax
    2d6b:	48 c7 85 c8 fd ff ff 	mov    QWORD PTR [rbp-0x238],0x0
    2d72:	00 00 00 00 
    2d76:	48 8d 85 c0 fd ff ff 	lea    rax,[rbp-0x240]
    2d7d:	be 00 00 00 00       	mov    esi,0x0
    2d82:	48 89 c7             	mov    rdi,rax
    2d85:	e8 46 e3 ff ff       	call   10d0 <nanosleep@plt>
    2d8a:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    2d91:	be 00 02 00 00       	mov    esi,0x200
    2d96:	48 89 c7             	mov    rdi,rax
    2d99:	e8 fe e5 ff ff       	call   139c <raw_readline>
    2d9e:	48 85 c0             	test   rax,rax
    2da1:	75 0f                	jne    2db2 <cancel_plan+0x102>
    2da3:	48 8d 05 6e 1a 00 00 	lea    rax,[rip+0x1a6e]        # 4818 <CHUNK_DEPTH+0x7f8>
    2daa:	48 89 c7             	mov    rdi,rax
    2dad:	e8 57 e4 ff ff       	call   1209 <raw_print>
    2db2:	48 8d 95 fc fd ff ff 	lea    rdx,[rbp-0x204]
    2db9:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    2dc0:	48 89 d6             	mov    rsi,rdx
    2dc3:	48 89 c7             	mov    rdi,rax
    2dc6:	e8 66 e6 ff ff       	call   1431 <raw_parse_int>
    2dcb:	8b 05 5f 47 00 00    	mov    eax,DWORD PTR [rip+0x475f]        # 7530 <be_annoying>
    2dd1:	48 98                	cdqe
    2dd3:	48 89 85 b0 fd ff ff 	mov    QWORD PTR [rbp-0x250],rax
    2dda:	48 c7 85 b8 fd ff ff 	mov    QWORD PTR [rbp-0x248],0x0
    2de1:	00 00 00 00 
    2de5:	48 8d 85 b0 fd ff ff 	lea    rax,[rbp-0x250]
    2dec:	be 00 00 00 00       	mov    esi,0x0
    2df1:	48 89 c7             	mov    rdi,rax
    2df4:	e8 d7 e2 ff ff       	call   10d0 <nanosleep@plt>
    2df9:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    2dff:	83 f8 01             	cmp    eax,0x1
    2e02:	75 0a                	jne    2e0e <cancel_plan+0x15e>
    2e04:	e8 a2 ec ff ff       	call   1aab <start_position>
    2e09:	e9 66 09 00 00       	jmp    3774 <cancel_plan+0xac4>
    2e0e:	48 8d 05 b6 28 00 00 	lea    rax,[rip+0x28b6]        # 56cb <CHUNK_DEPTH+0x16ab>
    2e15:	48 89 c7             	mov    rdi,rax
    2e18:	e8 ec e3 ff ff       	call   1209 <raw_print>
    2e1d:	8b 05 0d 47 00 00    	mov    eax,DWORD PTR [rip+0x470d]        # 7530 <be_annoying>
    2e23:	48 98                	cdqe
    2e25:	48 89 85 a0 fd ff ff 	mov    QWORD PTR [rbp-0x260],rax
    2e2c:	48 c7 85 a8 fd ff ff 	mov    QWORD PTR [rbp-0x258],0x0
    2e33:	00 00 00 00 
    2e37:	48 8d 85 a0 fd ff ff 	lea    rax,[rbp-0x260]
    2e3e:	be 00 00 00 00       	mov    esi,0x0
    2e43:	48 89 c7             	mov    rdi,rax
    2e46:	e8 85 e2 ff ff       	call   10d0 <nanosleep@plt>
    2e4b:	48 8d 05 56 28 00 00 	lea    rax,[rip+0x2856]        # 56a8 <CHUNK_DEPTH+0x1688>
    2e52:	48 89 c7             	mov    rdi,rax
    2e55:	e8 af e3 ff ff       	call   1209 <raw_print>
    2e5a:	8b 05 d0 46 00 00    	mov    eax,DWORD PTR [rip+0x46d0]        # 7530 <be_annoying>
    2e60:	48 98                	cdqe
    2e62:	48 89 85 90 fd ff ff 	mov    QWORD PTR [rbp-0x270],rax
    2e69:	48 c7 85 98 fd ff ff 	mov    QWORD PTR [rbp-0x268],0x0
    2e70:	00 00 00 00 
    2e74:	48 8d 85 90 fd ff ff 	lea    rax,[rbp-0x270]
    2e7b:	be 00 00 00 00       	mov    esi,0x0
    2e80:	48 89 c7             	mov    rdi,rax
    2e83:	e8 48 e2 ff ff       	call   10d0 <nanosleep@plt>
    2e88:	48 8d 05 2a 28 00 00 	lea    rax,[rip+0x282a]        # 56b9 <CHUNK_DEPTH+0x1699>
    2e8f:	48 89 c7             	mov    rdi,rax
    2e92:	e8 72 e3 ff ff       	call   1209 <raw_print>
    2e97:	8b 05 93 46 00 00    	mov    eax,DWORD PTR [rip+0x4693]        # 7530 <be_annoying>
    2e9d:	48 98                	cdqe
    2e9f:	48 89 85 80 fd ff ff 	mov    QWORD PTR [rbp-0x280],rax
    2ea6:	48 c7 85 88 fd ff ff 	mov    QWORD PTR [rbp-0x278],0x0
    2ead:	00 00 00 00 
    2eb1:	48 8d 85 80 fd ff ff 	lea    rax,[rbp-0x280]
    2eb8:	be 00 00 00 00       	mov    esi,0x0
    2ebd:	48 89 c7             	mov    rdi,rax
    2ec0:	e8 0b e2 ff ff       	call   10d0 <nanosleep@plt>
    2ec5:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    2ecc:	be 00 02 00 00       	mov    esi,0x200
    2ed1:	48 89 c7             	mov    rdi,rax
    2ed4:	e8 c3 e4 ff ff       	call   139c <raw_readline>
    2ed9:	48 85 c0             	test   rax,rax
    2edc:	75 0f                	jne    2eed <cancel_plan+0x23d>
    2ede:	48 8d 05 33 19 00 00 	lea    rax,[rip+0x1933]        # 4818 <CHUNK_DEPTH+0x7f8>
    2ee5:	48 89 c7             	mov    rdi,rax
    2ee8:	e8 1c e3 ff ff       	call   1209 <raw_print>
    2eed:	48 8d 95 fc fd ff ff 	lea    rdx,[rbp-0x204]
    2ef4:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    2efb:	48 89 d6             	mov    rsi,rdx
    2efe:	48 89 c7             	mov    rdi,rax
    2f01:	e8 2b e5 ff ff       	call   1431 <raw_parse_int>
    2f06:	8b 05 24 46 00 00    	mov    eax,DWORD PTR [rip+0x4624]        # 7530 <be_annoying>
    2f0c:	48 98                	cdqe
    2f0e:	48 89 85 70 fd ff ff 	mov    QWORD PTR [rbp-0x290],rax
    2f15:	48 c7 85 78 fd ff ff 	mov    QWORD PTR [rbp-0x288],0x0
    2f1c:	00 00 00 00 
    2f20:	48 8d 85 70 fd ff ff 	lea    rax,[rbp-0x290]
    2f27:	be 00 00 00 00       	mov    esi,0x0
    2f2c:	48 89 c7             	mov    rdi,rax
    2f2f:	e8 9c e1 ff ff       	call   10d0 <nanosleep@plt>
    2f34:	48 8d 05 a3 27 00 00 	lea    rax,[rip+0x27a3]        # 56de <CHUNK_DEPTH+0x16be>
    2f3b:	48 89 c7             	mov    rdi,rax
    2f3e:	e8 c6 e2 ff ff       	call   1209 <raw_print>
    2f43:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    2f49:	89 c7                	mov    edi,eax
    2f4b:	e8 59 e3 ff ff       	call   12a9 <raw_print_int>
    2f50:	48 8d 05 98 27 00 00 	lea    rax,[rip+0x2798]        # 56ef <CHUNK_DEPTH+0x16cf>
    2f57:	48 89 c7             	mov    rdi,rax
    2f5a:	e8 aa e2 ff ff       	call   1209 <raw_print>
    2f5f:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    2f65:	83 f8 01             	cmp    eax,0x1
    2f68:	74 0a                	je     2f74 <cancel_plan+0x2c4>
    2f6a:	e8 3c eb ff ff       	call   1aab <start_position>
    2f6f:	e9 00 08 00 00       	jmp    3774 <cancel_plan+0xac4>
    2f74:	48 8d 05 8d 27 00 00 	lea    rax,[rip+0x278d]        # 5708 <CHUNK_DEPTH+0x16e8>
    2f7b:	48 89 c7             	mov    rdi,rax
    2f7e:	e8 86 e2 ff ff       	call   1209 <raw_print>
    2f83:	8b 05 a7 45 00 00    	mov    eax,DWORD PTR [rip+0x45a7]        # 7530 <be_annoying>
    2f89:	48 98                	cdqe
    2f8b:	48 89 85 60 fd ff ff 	mov    QWORD PTR [rbp-0x2a0],rax
    2f92:	48 c7 85 68 fd ff ff 	mov    QWORD PTR [rbp-0x298],0x0
    2f99:	00 00 00 00 
    2f9d:	48 8d 85 60 fd ff ff 	lea    rax,[rbp-0x2a0]
    2fa4:	be 00 00 00 00       	mov    esi,0x0
    2fa9:	48 89 c7             	mov    rdi,rax
    2fac:	e8 1f e1 ff ff       	call   10d0 <nanosleep@plt>
    2fb1:	48 8d 05 90 27 00 00 	lea    rax,[rip+0x2790]        # 5748 <CHUNK_DEPTH+0x1728>
    2fb8:	48 89 c7             	mov    rdi,rax
    2fbb:	e8 49 e2 ff ff       	call   1209 <raw_print>
    2fc0:	8b 05 6a 45 00 00    	mov    eax,DWORD PTR [rip+0x456a]        # 7530 <be_annoying>
    2fc6:	48 98                	cdqe
    2fc8:	48 89 85 50 fd ff ff 	mov    QWORD PTR [rbp-0x2b0],rax
    2fcf:	48 c7 85 58 fd ff ff 	mov    QWORD PTR [rbp-0x2a8],0x0
    2fd6:	00 00 00 00 
    2fda:	48 8d 85 50 fd ff ff 	lea    rax,[rbp-0x2b0]
    2fe1:	be 00 00 00 00       	mov    esi,0x0
    2fe6:	48 89 c7             	mov    rdi,rax
    2fe9:	e8 e2 e0 ff ff       	call   10d0 <nanosleep@plt>
    2fee:	48 8d 05 8b 27 00 00 	lea    rax,[rip+0x278b]        # 5780 <CHUNK_DEPTH+0x1760>
    2ff5:	48 89 c7             	mov    rdi,rax
    2ff8:	e8 0c e2 ff ff       	call   1209 <raw_print>
    2ffd:	8b 05 2d 45 00 00    	mov    eax,DWORD PTR [rip+0x452d]        # 7530 <be_annoying>
    3003:	48 98                	cdqe
    3005:	48 89 85 40 fd ff ff 	mov    QWORD PTR [rbp-0x2c0],rax
    300c:	48 c7 85 48 fd ff ff 	mov    QWORD PTR [rbp-0x2b8],0x0
    3013:	00 00 00 00 
    3017:	48 8d 85 40 fd ff ff 	lea    rax,[rbp-0x2c0]
    301e:	be 00 00 00 00       	mov    esi,0x0
    3023:	48 89 c7             	mov    rdi,rax
    3026:	e8 a5 e0 ff ff       	call   10d0 <nanosleep@plt>
    302b:	48 8d 05 6e 27 00 00 	lea    rax,[rip+0x276e]        # 57a0 <CHUNK_DEPTH+0x1780>
    3032:	48 89 c7             	mov    rdi,rax
    3035:	e8 cf e1 ff ff       	call   1209 <raw_print>
    303a:	8b 05 f0 44 00 00    	mov    eax,DWORD PTR [rip+0x44f0]        # 7530 <be_annoying>
    3040:	48 98                	cdqe
    3042:	48 89 85 30 fd ff ff 	mov    QWORD PTR [rbp-0x2d0],rax
    3049:	48 c7 85 38 fd ff ff 	mov    QWORD PTR [rbp-0x2c8],0x0
    3050:	00 00 00 00 
    3054:	48 8d 85 30 fd ff ff 	lea    rax,[rbp-0x2d0]
    305b:	be 00 00 00 00       	mov    esi,0x0
    3060:	48 89 c7             	mov    rdi,rax
    3063:	e8 68 e0 ff ff       	call   10d0 <nanosleep@plt>
    3068:	48 8d 05 59 27 00 00 	lea    rax,[rip+0x2759]        # 57c8 <CHUNK_DEPTH+0x17a8>
    306f:	48 89 c7             	mov    rdi,rax
    3072:	e8 92 e1 ff ff       	call   1209 <raw_print>
    3077:	8b 05 b3 44 00 00    	mov    eax,DWORD PTR [rip+0x44b3]        # 7530 <be_annoying>
    307d:	48 98                	cdqe
    307f:	48 89 85 20 fd ff ff 	mov    QWORD PTR [rbp-0x2e0],rax
    3086:	48 c7 85 28 fd ff ff 	mov    QWORD PTR [rbp-0x2d8],0x0
    308d:	00 00 00 00 
    3091:	48 8d 85 20 fd ff ff 	lea    rax,[rbp-0x2e0]
    3098:	be 00 00 00 00       	mov    esi,0x0
    309d:	48 89 c7             	mov    rdi,rax
    30a0:	e8 2b e0 ff ff       	call   10d0 <nanosleep@plt>
    30a5:	48 8d 05 54 27 00 00 	lea    rax,[rip+0x2754]        # 5800 <CHUNK_DEPTH+0x17e0>
    30ac:	48 89 c7             	mov    rdi,rax
    30af:	e8 55 e1 ff ff       	call   1209 <raw_print>
    30b4:	8b 05 76 44 00 00    	mov    eax,DWORD PTR [rip+0x4476]        # 7530 <be_annoying>
    30ba:	48 98                	cdqe
    30bc:	48 89 85 10 fd ff ff 	mov    QWORD PTR [rbp-0x2f0],rax
    30c3:	48 c7 85 18 fd ff ff 	mov    QWORD PTR [rbp-0x2e8],0x0
    30ca:	00 00 00 00 
    30ce:	48 8d 85 10 fd ff ff 	lea    rax,[rbp-0x2f0]
    30d5:	be 00 00 00 00       	mov    esi,0x0
    30da:	48 89 c7             	mov    rdi,rax
    30dd:	e8 ee df ff ff       	call   10d0 <nanosleep@plt>
    30e2:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    30e9:	be 00 02 00 00       	mov    esi,0x200
    30ee:	48 89 c7             	mov    rdi,rax
    30f1:	e8 a6 e2 ff ff       	call   139c <raw_readline>
    30f6:	48 85 c0             	test   rax,rax
    30f9:	75 0f                	jne    310a <cancel_plan+0x45a>
    30fb:	48 8d 05 16 17 00 00 	lea    rax,[rip+0x1716]        # 4818 <CHUNK_DEPTH+0x7f8>
    3102:	48 89 c7             	mov    rdi,rax
    3105:	e8 ff e0 ff ff       	call   1209 <raw_print>
    310a:	48 8d 95 fc fd ff ff 	lea    rdx,[rbp-0x204]
    3111:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    3118:	48 89 d6             	mov    rsi,rdx
    311b:	48 89 c7             	mov    rdi,rax
    311e:	e8 0e e3 ff ff       	call   1431 <raw_parse_int>
    3123:	8b 05 07 44 00 00    	mov    eax,DWORD PTR [rip+0x4407]        # 7530 <be_annoying>
    3129:	48 98                	cdqe
    312b:	48 89 85 00 fd ff ff 	mov    QWORD PTR [rbp-0x300],rax
    3132:	48 c7 85 08 fd ff ff 	mov    QWORD PTR [rbp-0x2f8],0x0
    3139:	00 00 00 00 
    313d:	48 8d 85 00 fd ff ff 	lea    rax,[rbp-0x300]
    3144:	be 00 00 00 00       	mov    esi,0x0
    3149:	48 89 c7             	mov    rdi,rax
    314c:	e8 7f df ff ff       	call   10d0 <nanosleep@plt>
    3151:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    3157:	83 f8 05             	cmp    eax,0x5
    315a:	0f 87 08 06 00 00    	ja     3768 <cancel_plan+0xab8>
    3160:	89 c0                	mov    eax,eax
    3162:	48 8d 14 85 00 00 00 	lea    rdx,[rax*4+0x0]
    3169:	00 
    316a:	48 8d 05 6b 29 00 00 	lea    rax,[rip+0x296b]        # 5adc <CHUNK_DEPTH+0x1abc>
    3171:	8b 04 02             	mov    eax,DWORD PTR [rdx+rax*1]
    3174:	48 98                	cdqe
    3176:	48 8d 15 5f 29 00 00 	lea    rdx,[rip+0x295f]        # 5adc <CHUNK_DEPTH+0x1abc>
    317d:	48 01 d0             	add    rax,rdx
    3180:	3e ff e0             	notrack jmp rax
    3183:	e8 4e f6 ff ff       	call   27d6 <upgrade_or_change>
    3188:	e9 e2 05 00 00       	jmp    376f <cancel_plan+0xabf>
    318d:	e8 3e f1 ff ff       	call   22d0 <report_outage>
    3192:	e9 d8 05 00 00       	jmp    376f <cancel_plan+0xabf>
    3197:	e8 9a f4 ff ff       	call   2636 <technical_support>
    319c:	e9 ce 05 00 00       	jmp    376f <cancel_plan+0xabf>
    31a1:	e8 38 e4 ff ff       	call   15de <get_a_fun_fact>
    31a6:	e8 05 fb ff ff       	call   2cb0 <cancel_plan>
    31ab:	e9 bf 05 00 00       	jmp    376f <cancel_plan+0xabf>
    31b0:	48 8d 05 71 26 00 00 	lea    rax,[rip+0x2671]        # 5828 <CHUNK_DEPTH+0x1808>
    31b7:	48 89 c7             	mov    rdi,rax
    31ba:	e8 4a e0 ff ff       	call   1209 <raw_print>
    31bf:	8b 05 6b 43 00 00    	mov    eax,DWORD PTR [rip+0x436b]        # 7530 <be_annoying>
    31c5:	48 98                	cdqe
    31c7:	48 89 85 f0 fc ff ff 	mov    QWORD PTR [rbp-0x310],rax
    31ce:	48 c7 85 f8 fc ff ff 	mov    QWORD PTR [rbp-0x308],0x0
    31d5:	00 00 00 00 
    31d9:	48 8d 85 f0 fc ff ff 	lea    rax,[rbp-0x310]
    31e0:	be 00 00 00 00       	mov    esi,0x0
    31e5:	48 89 c7             	mov    rdi,rax
    31e8:	e8 e3 de ff ff       	call   10d0 <nanosleep@plt>
    31ed:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    31f4:	be 00 02 00 00       	mov    esi,0x200
    31f9:	48 89 c7             	mov    rdi,rax
    31fc:	e8 9b e1 ff ff       	call   139c <raw_readline>
    3201:	48 85 c0             	test   rax,rax
    3204:	75 0f                	jne    3215 <cancel_plan+0x565>
    3206:	48 8d 05 0b 16 00 00 	lea    rax,[rip+0x160b]        # 4818 <CHUNK_DEPTH+0x7f8>
    320d:	48 89 c7             	mov    rdi,rax
    3210:	e8 f4 df ff ff       	call   1209 <raw_print>
    3215:	8b 05 15 43 00 00    	mov    eax,DWORD PTR [rip+0x4315]        # 7530 <be_annoying>
    321b:	48 98                	cdqe
    321d:	48 89 85 e0 fc ff ff 	mov    QWORD PTR [rbp-0x320],rax
    3224:	48 c7 85 e8 fc ff ff 	mov    QWORD PTR [rbp-0x318],0x0
    322b:	00 00 00 00 
    322f:	48 8d 85 e0 fc ff ff 	lea    rax,[rbp-0x320]
    3236:	be 00 00 00 00       	mov    esi,0x0
    323b:	48 89 c7             	mov    rdi,rax
    323e:	e8 8d de ff ff       	call   10d0 <nanosleep@plt>
    3243:	e8 96 e3 ff ff       	call   15de <get_a_fun_fact>
    3248:	48 8d 05 19 24 00 00 	lea    rax,[rip+0x2419]        # 5668 <CHUNK_DEPTH+0x1648>
    324f:	48 89 c7             	mov    rdi,rax
    3252:	e8 b2 df ff ff       	call   1209 <raw_print>
    3257:	8b 05 d3 42 00 00    	mov    eax,DWORD PTR [rip+0x42d3]        # 7530 <be_annoying>
    325d:	48 98                	cdqe
    325f:	48 89 85 d0 fc ff ff 	mov    QWORD PTR [rbp-0x330],rax
    3266:	48 c7 85 d8 fc ff ff 	mov    QWORD PTR [rbp-0x328],0x0
    326d:	00 00 00 00 
    3271:	48 8d 85 d0 fc ff ff 	lea    rax,[rbp-0x330]
    3278:	be 00 00 00 00       	mov    esi,0x0
    327d:	48 89 c7             	mov    rdi,rax
    3280:	e8 4b de ff ff       	call   10d0 <nanosleep@plt>
    3285:	48 8d 05 09 26 00 00 	lea    rax,[rip+0x2609]        # 5895 <CHUNK_DEPTH+0x1875>
    328c:	48 89 c7             	mov    rdi,rax
    328f:	e8 75 df ff ff       	call   1209 <raw_print>
    3294:	8b 05 96 42 00 00    	mov    eax,DWORD PTR [rip+0x4296]        # 7530 <be_annoying>
    329a:	48 98                	cdqe
    329c:	48 89 85 c0 fc ff ff 	mov    QWORD PTR [rbp-0x340],rax
    32a3:	48 c7 85 c8 fc ff ff 	mov    QWORD PTR [rbp-0x338],0x0
    32aa:	00 00 00 00 
    32ae:	48 8d 85 c0 fc ff ff 	lea    rax,[rbp-0x340]
    32b5:	be 00 00 00 00       	mov    esi,0x0
    32ba:	48 89 c7             	mov    rdi,rax
    32bd:	e8 0e de ff ff       	call   10d0 <nanosleep@plt>
    32c2:	48 8d 05 dd 25 00 00 	lea    rax,[rip+0x25dd]        # 58a6 <CHUNK_DEPTH+0x1886>
    32c9:	48 89 c7             	mov    rdi,rax
    32cc:	e8 38 df ff ff       	call   1209 <raw_print>
    32d1:	8b 05 59 42 00 00    	mov    eax,DWORD PTR [rip+0x4259]        # 7530 <be_annoying>
    32d7:	48 98                	cdqe
    32d9:	48 89 85 b0 fc ff ff 	mov    QWORD PTR [rbp-0x350],rax
    32e0:	48 c7 85 b8 fc ff ff 	mov    QWORD PTR [rbp-0x348],0x0
    32e7:	00 00 00 00 
    32eb:	48 8d 85 b0 fc ff ff 	lea    rax,[rbp-0x350]
    32f2:	be 00 00 00 00       	mov    esi,0x0
    32f7:	48 89 c7             	mov    rdi,rax
    32fa:	e8 d1 dd ff ff       	call   10d0 <nanosleep@plt>
    32ff:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    3306:	be 00 02 00 00       	mov    esi,0x200
    330b:	48 89 c7             	mov    rdi,rax
    330e:	e8 89 e0 ff ff       	call   139c <raw_readline>
    3313:	48 85 c0             	test   rax,rax
    3316:	75 0f                	jne    3327 <cancel_plan+0x677>
    3318:	48 8d 05 f9 14 00 00 	lea    rax,[rip+0x14f9]        # 4818 <CHUNK_DEPTH+0x7f8>
    331f:	48 89 c7             	mov    rdi,rax
    3322:	e8 e2 de ff ff       	call   1209 <raw_print>
    3327:	48 8d 95 fc fd ff ff 	lea    rdx,[rbp-0x204]
    332e:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    3335:	48 89 d6             	mov    rsi,rdx
    3338:	48 89 c7             	mov    rdi,rax
    333b:	e8 f1 e0 ff ff       	call   1431 <raw_parse_int>
    3340:	8b 05 ea 41 00 00    	mov    eax,DWORD PTR [rip+0x41ea]        # 7530 <be_annoying>
    3346:	48 98                	cdqe
    3348:	48 89 85 a0 fc ff ff 	mov    QWORD PTR [rbp-0x360],rax
    334f:	48 c7 85 a8 fc ff ff 	mov    QWORD PTR [rbp-0x358],0x0
    3356:	00 00 00 00 
    335a:	48 8d 85 a0 fc ff ff 	lea    rax,[rbp-0x360]
    3361:	be 00 00 00 00       	mov    esi,0x0
    3366:	48 89 c7             	mov    rdi,rax
    3369:	e8 62 dd ff ff       	call   10d0 <nanosleep@plt>
    336e:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    3374:	83 f8 03             	cmp    eax,0x3
    3377:	74 0a                	je     3383 <cancel_plan+0x6d3>
    3379:	e8 2d e7 ff ff       	call   1aab <start_position>
    337e:	e9 f1 03 00 00       	jmp    3774 <cancel_plan+0xac4>
    3383:	48 8d 05 2e 25 00 00 	lea    rax,[rip+0x252e]        # 58b8 <CHUNK_DEPTH+0x1898>
    338a:	48 89 c7             	mov    rdi,rax
    338d:	e8 77 de ff ff       	call   1209 <raw_print>
    3392:	8b 05 98 41 00 00    	mov    eax,DWORD PTR [rip+0x4198]        # 7530 <be_annoying>
    3398:	48 98                	cdqe
    339a:	48 89 85 90 fc ff ff 	mov    QWORD PTR [rbp-0x370],rax
    33a1:	48 c7 85 98 fc ff ff 	mov    QWORD PTR [rbp-0x368],0x0
    33a8:	00 00 00 00 
    33ac:	48 8d 85 90 fc ff ff 	lea    rax,[rbp-0x370]
    33b3:	be 00 00 00 00       	mov    esi,0x0
    33b8:	48 89 c7             	mov    rdi,rax
    33bb:	e8 10 dd ff ff       	call   10d0 <nanosleep@plt>
    33c0:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    33c7:	be 00 02 00 00       	mov    esi,0x200
    33cc:	48 89 c7             	mov    rdi,rax
    33cf:	e8 c8 df ff ff       	call   139c <raw_readline>
    33d4:	48 85 c0             	test   rax,rax
    33d7:	75 0f                	jne    33e8 <cancel_plan+0x738>
    33d9:	48 8d 05 38 14 00 00 	lea    rax,[rip+0x1438]        # 4818 <CHUNK_DEPTH+0x7f8>
    33e0:	48 89 c7             	mov    rdi,rax
    33e3:	e8 21 de ff ff       	call   1209 <raw_print>
    33e8:	8b 05 42 41 00 00    	mov    eax,DWORD PTR [rip+0x4142]        # 7530 <be_annoying>
    33ee:	48 98                	cdqe
    33f0:	48 89 85 80 fc ff ff 	mov    QWORD PTR [rbp-0x380],rax
    33f7:	48 c7 85 88 fc ff ff 	mov    QWORD PTR [rbp-0x378],0x0
    33fe:	00 00 00 00 
    3402:	48 8d 85 80 fc ff ff 	lea    rax,[rbp-0x380]
    3409:	be 00 00 00 00       	mov    esi,0x0
    340e:	48 89 c7             	mov    rdi,rax
    3411:	e8 ba dc ff ff       	call   10d0 <nanosleep@plt>
    3416:	e8 c3 e1 ff ff       	call   15de <get_a_fun_fact>
    341b:	48 8d 05 46 22 00 00 	lea    rax,[rip+0x2246]        # 5668 <CHUNK_DEPTH+0x1648>
    3422:	48 89 c7             	mov    rdi,rax
    3425:	e8 df dd ff ff       	call   1209 <raw_print>
    342a:	8b 05 00 41 00 00    	mov    eax,DWORD PTR [rip+0x4100]        # 7530 <be_annoying>
    3430:	48 98                	cdqe
    3432:	48 89 85 70 fc ff ff 	mov    QWORD PTR [rbp-0x390],rax
    3439:	48 c7 85 78 fc ff ff 	mov    QWORD PTR [rbp-0x388],0x0
    3440:	00 00 00 00 
    3444:	48 8d 85 70 fc ff ff 	lea    rax,[rbp-0x390]
    344b:	be 00 00 00 00       	mov    esi,0x0
    3450:	48 89 c7             	mov    rdi,rax
    3453:	e8 78 dc ff ff       	call   10d0 <nanosleep@plt>
    3458:	48 8d 05 c0 24 00 00 	lea    rax,[rip+0x24c0]        # 591f <CHUNK_DEPTH+0x18ff>
    345f:	48 89 c7             	mov    rdi,rax
    3462:	e8 a2 dd ff ff       	call   1209 <raw_print>
    3467:	8b 05 c3 40 00 00    	mov    eax,DWORD PTR [rip+0x40c3]        # 7530 <be_annoying>
    346d:	48 98                	cdqe
    346f:	48 89 85 60 fc ff ff 	mov    QWORD PTR [rbp-0x3a0],rax
    3476:	48 c7 85 68 fc ff ff 	mov    QWORD PTR [rbp-0x398],0x0
    347d:	00 00 00 00 
    3481:	48 8d 85 60 fc ff ff 	lea    rax,[rbp-0x3a0]
    3488:	be 00 00 00 00       	mov    esi,0x0
    348d:	48 89 c7             	mov    rdi,rax
    3490:	e8 3b dc ff ff       	call   10d0 <nanosleep@plt>
    3495:	48 8d 05 94 24 00 00 	lea    rax,[rip+0x2494]        # 5930 <CHUNK_DEPTH+0x1910>
    349c:	48 89 c7             	mov    rdi,rax
    349f:	e8 65 dd ff ff       	call   1209 <raw_print>
    34a4:	8b 05 86 40 00 00    	mov    eax,DWORD PTR [rip+0x4086]        # 7530 <be_annoying>
    34aa:	48 98                	cdqe
    34ac:	48 89 85 50 fc ff ff 	mov    QWORD PTR [rbp-0x3b0],rax
    34b3:	48 c7 85 58 fc ff ff 	mov    QWORD PTR [rbp-0x3a8],0x0
    34ba:	00 00 00 00 
    34be:	48 8d 85 50 fc ff ff 	lea    rax,[rbp-0x3b0]
    34c5:	be 00 00 00 00       	mov    esi,0x0
    34ca:	48 89 c7             	mov    rdi,rax
    34cd:	e8 fe db ff ff       	call   10d0 <nanosleep@plt>
    34d2:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    34d9:	be 00 02 00 00       	mov    esi,0x200
    34de:	48 89 c7             	mov    rdi,rax
    34e1:	e8 b6 de ff ff       	call   139c <raw_readline>
    34e6:	48 85 c0             	test   rax,rax
    34e9:	75 0f                	jne    34fa <cancel_plan+0x84a>
    34eb:	48 8d 05 26 13 00 00 	lea    rax,[rip+0x1326]        # 4818 <CHUNK_DEPTH+0x7f8>
    34f2:	48 89 c7             	mov    rdi,rax
    34f5:	e8 0f dd ff ff       	call   1209 <raw_print>
    34fa:	48 8d 95 fc fd ff ff 	lea    rdx,[rbp-0x204]
    3501:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    3508:	48 89 d6             	mov    rsi,rdx
    350b:	48 89 c7             	mov    rdi,rax
    350e:	e8 1e df ff ff       	call   1431 <raw_parse_int>
    3513:	8b 05 17 40 00 00    	mov    eax,DWORD PTR [rip+0x4017]        # 7530 <be_annoying>
    3519:	48 98                	cdqe
    351b:	48 89 85 40 fc ff ff 	mov    QWORD PTR [rbp-0x3c0],rax
    3522:	48 c7 85 48 fc ff ff 	mov    QWORD PTR [rbp-0x3b8],0x0
    3529:	00 00 00 00 
    352d:	48 8d 85 40 fc ff ff 	lea    rax,[rbp-0x3c0]
    3534:	be 00 00 00 00       	mov    esi,0x0
    3539:	48 89 c7             	mov    rdi,rax
    353c:	e8 8f db ff ff       	call   10d0 <nanosleep@plt>
    3541:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    3547:	85 c0                	test   eax,eax
    3549:	74 0a                	je     3555 <cancel_plan+0x8a5>
    354b:	e8 5b e5 ff ff       	call   1aab <start_position>
    3550:	e9 1f 02 00 00       	jmp    3774 <cancel_plan+0xac4>
    3555:	48 8d 05 ec 23 00 00 	lea    rax,[rip+0x23ec]        # 5948 <CHUNK_DEPTH+0x1928>
    355c:	48 89 c7             	mov    rdi,rax
    355f:	e8 a5 dc ff ff       	call   1209 <raw_print>
    3564:	8b 05 c6 3f 00 00    	mov    eax,DWORD PTR [rip+0x3fc6]        # 7530 <be_annoying>
    356a:	48 98                	cdqe
    356c:	48 89 85 30 fc ff ff 	mov    QWORD PTR [rbp-0x3d0],rax
    3573:	48 c7 85 38 fc ff ff 	mov    QWORD PTR [rbp-0x3c8],0x0
    357a:	00 00 00 00 
    357e:	48 8d 85 30 fc ff ff 	lea    rax,[rbp-0x3d0]
    3585:	be 00 00 00 00       	mov    esi,0x0
    358a:	48 89 c7             	mov    rdi,rax
    358d:	e8 3e db ff ff       	call   10d0 <nanosleep@plt>
    3592:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    3599:	be 00 02 00 00       	mov    esi,0x200
    359e:	48 89 c7             	mov    rdi,rax
    35a1:	e8 f6 dd ff ff       	call   139c <raw_readline>
    35a6:	48 85 c0             	test   rax,rax
    35a9:	75 0f                	jne    35ba <cancel_plan+0x90a>
    35ab:	48 8d 05 66 12 00 00 	lea    rax,[rip+0x1266]        # 4818 <CHUNK_DEPTH+0x7f8>
    35b2:	48 89 c7             	mov    rdi,rax
    35b5:	e8 4f dc ff ff       	call   1209 <raw_print>
    35ba:	8b 05 70 3f 00 00    	mov    eax,DWORD PTR [rip+0x3f70]        # 7530 <be_annoying>
    35c0:	48 98                	cdqe
    35c2:	48 89 85 20 fc ff ff 	mov    QWORD PTR [rbp-0x3e0],rax
    35c9:	48 c7 85 28 fc ff ff 	mov    QWORD PTR [rbp-0x3d8],0x0
    35d0:	00 00 00 00 
    35d4:	48 8d 85 20 fc ff ff 	lea    rax,[rbp-0x3e0]
    35db:	be 00 00 00 00       	mov    esi,0x0
    35e0:	48 89 c7             	mov    rdi,rax
    35e3:	e8 e8 da ff ff       	call   10d0 <nanosleep@plt>
    35e8:	e8 f1 df ff ff       	call   15de <get_a_fun_fact>
    35ed:	48 8d 05 d4 23 00 00 	lea    rax,[rip+0x23d4]        # 59c8 <CHUNK_DEPTH+0x19a8>
    35f4:	48 89 c7             	mov    rdi,rax
    35f7:	e8 0d dc ff ff       	call   1209 <raw_print>
    35fc:	8b 05 2e 3f 00 00    	mov    eax,DWORD PTR [rip+0x3f2e]        # 7530 <be_annoying>
    3602:	48 98                	cdqe
    3604:	48 89 85 10 fc ff ff 	mov    QWORD PTR [rbp-0x3f0],rax
    360b:	48 c7 85 18 fc ff ff 	mov    QWORD PTR [rbp-0x3e8],0x0
    3612:	00 00 00 00 
    3616:	48 8d 85 10 fc ff ff 	lea    rax,[rbp-0x3f0]
    361d:	be 00 00 00 00       	mov    esi,0x0
    3622:	48 89 c7             	mov    rdi,rax
    3625:	e8 a6 da ff ff       	call   10d0 <nanosleep@plt>
    362a:	48 8d 05 d9 23 00 00 	lea    rax,[rip+0x23d9]        # 5a0a <CHUNK_DEPTH+0x19ea>
    3631:	48 89 c7             	mov    rdi,rax
    3634:	e8 d0 db ff ff       	call   1209 <raw_print>
    3639:	8b 05 f1 3e 00 00    	mov    eax,DWORD PTR [rip+0x3ef1]        # 7530 <be_annoying>
    363f:	48 98                	cdqe
    3641:	48 89 85 00 fc ff ff 	mov    QWORD PTR [rbp-0x400],rax
    3648:	48 c7 85 08 fc ff ff 	mov    QWORD PTR [rbp-0x3f8],0x0
    364f:	00 00 00 00 
    3653:	48 8d 85 00 fc ff ff 	lea    rax,[rbp-0x400]
    365a:	be 00 00 00 00       	mov    esi,0x0
    365f:	48 89 c7             	mov    rdi,rax
    3662:	e8 69 da ff ff       	call   10d0 <nanosleep@plt>
    3667:	48 8d 05 ad 23 00 00 	lea    rax,[rip+0x23ad]        # 5a1b <CHUNK_DEPTH+0x19fb>
    366e:	48 89 c7             	mov    rdi,rax
    3671:	e8 93 db ff ff       	call   1209 <raw_print>
    3676:	8b 05 b4 3e 00 00    	mov    eax,DWORD PTR [rip+0x3eb4]        # 7530 <be_annoying>
    367c:	48 98                	cdqe
    367e:	48 89 85 f0 fb ff ff 	mov    QWORD PTR [rbp-0x410],rax
    3685:	48 c7 85 f8 fb ff ff 	mov    QWORD PTR [rbp-0x408],0x0
    368c:	00 00 00 00 
    3690:	48 8d 85 f0 fb ff ff 	lea    rax,[rbp-0x410]
    3697:	be 00 00 00 00       	mov    esi,0x0
    369c:	48 89 c7             	mov    rdi,rax
    369f:	e8 2c da ff ff       	call   10d0 <nanosleep@plt>
    36a4:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    36ab:	be 00 02 00 00       	mov    esi,0x200
    36b0:	48 89 c7             	mov    rdi,rax
    36b3:	e8 e4 dc ff ff       	call   139c <raw_readline>
    36b8:	48 85 c0             	test   rax,rax
    36bb:	75 0f                	jne    36cc <cancel_plan+0xa1c>
    36bd:	48 8d 05 54 11 00 00 	lea    rax,[rip+0x1154]        # 4818 <CHUNK_DEPTH+0x7f8>
    36c4:	48 89 c7             	mov    rdi,rax
    36c7:	e8 3d db ff ff       	call   1209 <raw_print>
    36cc:	48 8d 95 fc fd ff ff 	lea    rdx,[rbp-0x204]
    36d3:	48 8d 85 00 fe ff ff 	lea    rax,[rbp-0x200]
    36da:	48 89 d6             	mov    rsi,rdx
    36dd:	48 89 c7             	mov    rdi,rax
    36e0:	e8 4c dd ff ff       	call   1431 <raw_parse_int>
    36e5:	8b 05 45 3e 00 00    	mov    eax,DWORD PTR [rip+0x3e45]        # 7530 <be_annoying>
    36eb:	48 98                	cdqe
    36ed:	48 89 85 e0 fb ff ff 	mov    QWORD PTR [rbp-0x420],rax
    36f4:	48 c7 85 e8 fb ff ff 	mov    QWORD PTR [rbp-0x418],0x0
    36fb:	00 00 00 00 
    36ff:	48 8d 85 e0 fb ff ff 	lea    rax,[rbp-0x420]
    3706:	be 00 00 00 00       	mov    esi,0x0
    370b:	48 89 c7             	mov    rdi,rax
    370e:	e8 bd d9 ff ff       	call   10d0 <nanosleep@plt>
    3713:	8b 85 fc fd ff ff    	mov    eax,DWORD PTR [rbp-0x204]
    3719:	85 c0                	test   eax,eax
    371b:	74 07                	je     3724 <cancel_plan+0xa74>
    371d:	e8 89 e3 ff ff       	call   1aab <start_position>
    3722:	eb 50                	jmp    3774 <cancel_plan+0xac4>
    3724:	48 8d 05 05 23 00 00 	lea    rax,[rip+0x2305]        # 5a30 <CHUNK_DEPTH+0x1a10>
    372b:	48 89 c7             	mov    rdi,rax
    372e:	e8 d6 da ff ff       	call   1209 <raw_print>
    3733:	8b 05 f7 3d 00 00    	mov    eax,DWORD PTR [rip+0x3df7]        # 7530 <be_annoying>
    3739:	48 98                	cdqe
    373b:	48 89 85 d0 fb ff ff 	mov    QWORD PTR [rbp-0x430],rax
    3742:	48 c7 85 d8 fb ff ff 	mov    QWORD PTR [rbp-0x428],0x0
    3749:	00 00 00 00 
    374d:	48 8d 85 d0 fb ff ff 	lea    rax,[rbp-0x430]
    3754:	be 00 00 00 00       	mov    esi,0x0
    3759:	48 89 c7             	mov    rdi,rax
    375c:	e8 6f d9 ff ff       	call   10d0 <nanosleep@plt>
    3761:	e8 10 00 00 00       	call   3776 <speak_with_an_operator>
    3766:	eb 07                	jmp    376f <cancel_plan+0xabf>
    3768:	e8 3e e3 ff ff       	call   1aab <start_position>
    376d:	eb 05                	jmp    3774 <cancel_plan+0xac4>
    376f:	e8 37 e3 ff ff       	call   1aab <start_position>
    3774:	c9                   	leave
    3775:	c3                   	ret

0000000000003776 <speak_with_an_operator>:
    3776:	f3 0f 1e fa          	endbr64
    377a:	55                   	push   rbp
    377b:	48 89 e5             	mov    rbp,rsp
    377e:	48 83 ec 70          	sub    rsp,0x70
    3782:	48 8d 05 6f 23 00 00 	lea    rax,[rip+0x236f]        # 5af8 <CHUNK_DEPTH+0x1ad8>
    3789:	48 89 c7             	mov    rdi,rax
    378c:	e8 78 da ff ff       	call   1209 <raw_print>
    3791:	8b 05 99 3d 00 00    	mov    eax,DWORD PTR [rip+0x3d99]        # 7530 <be_annoying>
    3797:	48 98                	cdqe
    3799:	48 89 45 f0          	mov    QWORD PTR [rbp-0x10],rax
    379d:	48 c7 45 f8 00 00 00 	mov    QWORD PTR [rbp-0x8],0x0
    37a4:	00 
    37a5:	48 8d 45 f0          	lea    rax,[rbp-0x10]
    37a9:	be 00 00 00 00       	mov    esi,0x0
    37ae:	48 89 c7             	mov    rdi,rax
    37b1:	e8 1a d9 ff ff       	call   10d0 <nanosleep@plt>
    37b6:	48 8d 05 7b 23 00 00 	lea    rax,[rip+0x237b]        # 5b38 <CHUNK_DEPTH+0x1b18>
    37bd:	48 89 c7             	mov    rdi,rax
    37c0:	e8 44 da ff ff       	call   1209 <raw_print>
    37c5:	8b 05 65 3d 00 00    	mov    eax,DWORD PTR [rip+0x3d65]        # 7530 <be_annoying>
    37cb:	48 98                	cdqe
    37cd:	48 89 45 e0          	mov    QWORD PTR [rbp-0x20],rax
    37d1:	48 c7 45 e8 00 00 00 	mov    QWORD PTR [rbp-0x18],0x0
    37d8:	00 
    37d9:	48 8d 45 e0          	lea    rax,[rbp-0x20]
    37dd:	be 00 00 00 00       	mov    esi,0x0
    37e2:	48 89 c7             	mov    rdi,rax
    37e5:	e8 e6 d8 ff ff       	call   10d0 <nanosleep@plt>
    37ea:	48 8d 05 47 23 00 00 	lea    rax,[rip+0x2347]        # 5b38 <CHUNK_DEPTH+0x1b18>
    37f1:	48 89 c7             	mov    rdi,rax
    37f4:	e8 10 da ff ff       	call   1209 <raw_print>
    37f9:	8b 05 31 3d 00 00    	mov    eax,DWORD PTR [rip+0x3d31]        # 7530 <be_annoying>
    37ff:	48 98                	cdqe
    3801:	48 89 45 d0          	mov    QWORD PTR [rbp-0x30],rax
    3805:	48 c7 45 d8 00 00 00 	mov    QWORD PTR [rbp-0x28],0x0
    380c:	00 
    380d:	48 8d 45 d0          	lea    rax,[rbp-0x30]
    3811:	be 00 00 00 00       	mov    esi,0x0
    3816:	48 89 c7             	mov    rdi,rax
    3819:	e8 b2 d8 ff ff       	call   10d0 <nanosleep@plt>
    381e:	48 8d 05 13 23 00 00 	lea    rax,[rip+0x2313]        # 5b38 <CHUNK_DEPTH+0x1b18>
    3825:	48 89 c7             	mov    rdi,rax
    3828:	e8 dc d9 ff ff       	call   1209 <raw_print>
    382d:	8b 05 fd 3c 00 00    	mov    eax,DWORD PTR [rip+0x3cfd]        # 7530 <be_annoying>
    3833:	48 98                	cdqe
    3835:	48 89 45 c0          	mov    QWORD PTR [rbp-0x40],rax
    3839:	48 c7 45 c8 00 00 00 	mov    QWORD PTR [rbp-0x38],0x0
    3840:	00 
    3841:	48 8d 45 c0          	lea    rax,[rbp-0x40]
    3845:	be 00 00 00 00       	mov    esi,0x0
    384a:	48 89 c7             	mov    rdi,rax
    384d:	e8 7e d8 ff ff       	call   10d0 <nanosleep@plt>
    3852:	48 8d 05 df 22 00 00 	lea    rax,[rip+0x22df]        # 5b38 <CHUNK_DEPTH+0x1b18>
    3859:	48 89 c7             	mov    rdi,rax
    385c:	e8 a8 d9 ff ff       	call   1209 <raw_print>
    3861:	8b 05 c9 3c 00 00    	mov    eax,DWORD PTR [rip+0x3cc9]        # 7530 <be_annoying>
    3867:	48 98                	cdqe
    3869:	48 89 45 b0          	mov    QWORD PTR [rbp-0x50],rax
    386d:	48 c7 45 b8 00 00 00 	mov    QWORD PTR [rbp-0x48],0x0
    3874:	00 
    3875:	48 8d 45 b0          	lea    rax,[rbp-0x50]
    3879:	be 00 00 00 00       	mov    esi,0x0
    387e:	48 89 c7             	mov    rdi,rax
    3881:	e8 4a d8 ff ff       	call   10d0 <nanosleep@plt>
    3886:	48 8d 05 c3 22 00 00 	lea    rax,[rip+0x22c3]        # 5b50 <CHUNK_DEPTH+0x1b30>
    388d:	48 89 c7             	mov    rdi,rax
    3890:	e8 74 d9 ff ff       	call   1209 <raw_print>
    3895:	8b 05 95 3c 00 00    	mov    eax,DWORD PTR [rip+0x3c95]        # 7530 <be_annoying>
    389b:	48 98                	cdqe
    389d:	48 89 45 a0          	mov    QWORD PTR [rbp-0x60],rax
    38a1:	48 c7 45 a8 00 00 00 	mov    QWORD PTR [rbp-0x58],0x0
    38a8:	00 
    38a9:	48 8d 45 a0          	lea    rax,[rbp-0x60]
    38ad:	be 00 00 00 00       	mov    esi,0x0
    38b2:	48 89 c7             	mov    rdi,rax
    38b5:	e8 16 d8 ff ff       	call   10d0 <nanosleep@plt>
    38ba:	48 8d 05 f6 22 00 00 	lea    rax,[rip+0x22f6]        # 5bb7 <CHUNK_DEPTH+0x1b97>
    38c1:	48 89 c7             	mov    rdi,rax
    38c4:	e8 40 d9 ff ff       	call   1209 <raw_print>
    38c9:	8b 15 61 3c 00 00    	mov    edx,DWORD PTR [rip+0x3c61]        # 7530 <be_annoying>
    38cf:	89 d0                	mov    eax,edx
    38d1:	01 c0                	add    eax,eax
    38d3:	01 d0                	add    eax,edx
    38d5:	48 98                	cdqe
    38d7:	48 89 45 90          	mov    QWORD PTR [rbp-0x70],rax
    38db:	48 c7 45 98 00 00 00 	mov    QWORD PTR [rbp-0x68],0x0
    38e2:	00 
    38e3:	48 8d 45 90          	lea    rax,[rbp-0x70]
    38e7:	be 00 00 00 00       	mov    esi,0x0
    38ec:	48 89 c7             	mov    rdi,rax
    38ef:	e8 dc d7 ff ff       	call   10d0 <nanosleep@plt>
    38f4:	e8 73 dc ff ff       	call   156c <get_random_number>
    38f9:	83 e0 03             	and    eax,0x3
    38fc:	48 85 c0             	test   rax,rax
    38ff:	75 05                	jne    3906 <speak_with_an_operator+0x190>
    3901:	e8 d8 dc ff ff       	call   15de <get_a_fun_fact>
    3906:	e8 61 dc ff ff       	call   156c <get_random_number>
    390b:	48 89 c1             	mov    rcx,rax
    390e:	48 89 c8             	mov    rax,rcx
    3911:	48 c1 e8 02          	shr    rax,0x2
    3915:	48 ba c3 f5 28 5c 8f 	movabs rdx,0x28f5c28f5c28f5c3
    391c:	c2 f5 28 
    391f:	48 f7 e2             	mul    rdx
    3922:	48 c1 ea 02          	shr    rdx,0x2
    3926:	48 89 d0             	mov    rax,rdx
    3929:	48 c1 e0 02          	shl    rax,0x2
    392d:	48 01 d0             	add    rax,rdx
    3930:	48 8d 14 85 00 00 00 	lea    rdx,[rax*4+0x0]
    3937:	00 
    3938:	48 01 d0             	add    rax,rdx
    393b:	48 c1 e0 02          	shl    rax,0x2
    393f:	48 29 c1             	sub    rcx,rax
    3942:	48 89 ca             	mov    rdx,rcx
    3945:	48 85 d2             	test   rdx,rdx
    3948:	0f 85 6c ff ff ff    	jne    38ba <speak_with_an_operator+0x144>
    394e:	48 8d 05 74 22 00 00 	lea    rax,[rip+0x2274]        # 5bc9 <CHUNK_DEPTH+0x1ba9>
    3955:	48 89 c7             	mov    rdi,rax
    3958:	e8 ac d8 ff ff       	call   1209 <raw_print>
    395d:	e8 49 e1 ff ff       	call   1aab <start_position>
    3962:	c9                   	leave
    3963:	c3                   	ret

0000000000003964 <payment_info>:
    3964:	f3 0f 1e fa          	endbr64
    3968:	55                   	push   rbp
    3969:	48 89 e5             	mov    rbp,rsp
    396c:	48 81 ec 00 01 00 00 	sub    rsp,0x100
    3973:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    397a:	ba 00 01 00 00       	mov    edx,0x100
    397f:	48 89 c6             	mov    rsi,rax
    3982:	48 8d 05 4f 22 00 00 	lea    rax,[rip+0x224f]        # 5bd8 <CHUNK_DEPTH+0x1bb8>
    3989:	48 89 c7             	mov    rdi,rax
    398c:	e8 93 01 00 00       	call   3b24 <prompt>
    3991:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    3998:	ba 00 01 00 00       	mov    edx,0x100
    399d:	48 89 c6             	mov    rsi,rax
    39a0:	48 8d 05 59 22 00 00 	lea    rax,[rip+0x2259]        # 5c00 <CHUNK_DEPTH+0x1be0>
    39a7:	48 89 c7             	mov    rdi,rax
    39aa:	e8 75 01 00 00       	call   3b24 <prompt>
    39af:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    39b6:	ba 00 01 00 00       	mov    edx,0x100
    39bb:	48 89 c6             	mov    rsi,rax
    39be:	48 8d 05 63 22 00 00 	lea    rax,[rip+0x2263]        # 5c28 <CHUNK_DEPTH+0x1c08>
    39c5:	48 89 c7             	mov    rdi,rax
    39c8:	e8 57 01 00 00       	call   3b24 <prompt>
    39cd:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    39d4:	ba 00 01 00 00       	mov    edx,0x100
    39d9:	48 89 c6             	mov    rsi,rax
    39dc:	48 8d 05 6d 22 00 00 	lea    rax,[rip+0x226d]        # 5c50 <CHUNK_DEPTH+0x1c30>
    39e3:	48 89 c7             	mov    rdi,rax
    39e6:	e8 39 01 00 00       	call   3b24 <prompt>
    39eb:	b8 00 00 00 00       	mov    eax,0x0
    39f0:	c9                   	leave
    39f1:	c3                   	ret

00000000000039f2 <login_roleplay>:
    39f2:	f3 0f 1e fa          	endbr64
    39f6:	55                   	push   rbp
    39f7:	48 89 e5             	mov    rbp,rsp
    39fa:	48 81 ec 00 01 00 00 	sub    rsp,0x100
    3a01:	ba 00 00 00 00       	mov    edx,0x0
    3a06:	be 00 00 00 00       	mov    esi,0x0
    3a0b:	48 8d 05 6e 22 00 00 	lea    rax,[rip+0x226e]        # 5c80 <CHUNK_DEPTH+0x1c60>
    3a12:	48 89 c7             	mov    rdi,rax
    3a15:	e8 0a 01 00 00       	call   3b24 <prompt>
    3a1a:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    3a21:	ba 00 01 00 00       	mov    edx,0x100
    3a26:	48 89 c6             	mov    rsi,rax
    3a29:	48 8d 05 b0 22 00 00 	lea    rax,[rip+0x22b0]        # 5ce0 <CHUNK_DEPTH+0x1cc0>
    3a30:	48 89 c7             	mov    rdi,rax
    3a33:	e8 ec 00 00 00       	call   3b24 <prompt>
    3a38:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    3a3f:	ba 00 01 00 00       	mov    edx,0x100
    3a44:	48 89 c6             	mov    rsi,rax
    3a47:	48 8d 05 d2 22 00 00 	lea    rax,[rip+0x22d2]        # 5d20 <CHUNK_DEPTH+0x1d00>
    3a4e:	48 89 c7             	mov    rdi,rax
    3a51:	e8 ce 00 00 00       	call   3b24 <prompt>
    3a56:	48 8d 85 00 ff ff ff 	lea    rax,[rbp-0x100]
    3a5d:	ba 00 01 00 00       	mov    edx,0x100
    3a62:	48 89 c6             	mov    rsi,rax
    3a65:	48 8d 05 e4 22 00 00 	lea    rax,[rip+0x22e4]        # 5d50 <CHUNK_DEPTH+0x1d30>
    3a6c:	48 89 c7             	mov    rdi,rax
    3a6f:	e8 b0 00 00 00       	call   3b24 <prompt>
    3a74:	ba 00 00 00 00       	mov    edx,0x0
    3a79:	be 00 00 00 00       	mov    esi,0x0
    3a7e:	48 8d 05 f4 22 00 00 	lea    rax,[rip+0x22f4]        # 5d79 <CHUNK_DEPTH+0x1d59>
    3a85:	48 89 c7             	mov    rdi,rax
    3a88:	e8 97 00 00 00       	call   3b24 <prompt>
    3a8d:	c7 05 ed 3a 00 00 01 	mov    DWORD PTR [rip+0x3aed],0x1        # 7584 <userData+0x4>
    3a94:	00 00 00 
    3a97:	b8 00 00 00 00       	mov    eax,0x0
    3a9c:	c9                   	leave
    3a9d:	c3                   	ret

0000000000003a9e <initial_email>:
    3a9e:	f3 0f 1e fa          	endbr64
    3aa2:	55                   	push   rbp
    3aa3:	48 89 e5             	mov    rbp,rsp
    3aa6:	ba 00 00 00 00       	mov    edx,0x0
    3aab:	be 00 00 00 00       	mov    esi,0x0
    3ab0:	48 8d 05 d9 22 00 00 	lea    rax,[rip+0x22d9]        # 5d90 <CHUNK_DEPTH+0x1d70>
    3ab7:	48 89 c7             	mov    rdi,rax
    3aba:	e8 65 00 00 00       	call   3b24 <prompt>
    3abf:	b8 00 00 00 00       	mov    eax,0x0
    3ac4:	5d                   	pop    rbp
    3ac5:	c3                   	ret

0000000000003ac6 <scream>:
    3ac6:	f3 0f 1e fa          	endbr64
    3aca:	55                   	push   rbp
    3acb:	48 89 e5             	mov    rbp,rsp
    3ace:	48 83 ec 10          	sub    rsp,0x10
    3ad2:	89 7d fc             	mov    DWORD PTR [rbp-0x4],edi
    3ad5:	eb 13                	jmp    3aea <scream+0x24>
    3ad7:	48 8d 05 da 22 00 00 	lea    rax,[rip+0x22da]        # 5db8 <CHUNK_DEPTH+0x1d98>
    3ade:	48 89 c7             	mov    rdi,rax
    3ae1:	e8 23 d7 ff ff       	call   1209 <raw_print>
    3ae6:	83 6d fc 01          	sub    DWORD PTR [rbp-0x4],0x1
    3aea:	83 7d fc 00          	cmp    DWORD PTR [rbp-0x4],0x0
    3aee:	75 e7                	jne    3ad7 <scream+0x11>
    3af0:	48 8d 05 c6 22 00 00 	lea    rax,[rip+0x22c6]        # 5dbd <CHUNK_DEPTH+0x1d9d>
    3af7:	48 89 c7             	mov    rdi,rax
    3afa:	e8 0a d7 ff ff       	call   1209 <raw_print>
    3aff:	48 8d 05 ba 22 00 00 	lea    rax,[rip+0x22ba]        # 5dc0 <CHUNK_DEPTH+0x1da0>
    3b06:	48 89 c7             	mov    rdi,rax
    3b09:	e8 fb d6 ff ff       	call   1209 <raw_print>
    3b0e:	48 8d 05 a8 22 00 00 	lea    rax,[rip+0x22a8]        # 5dbd <CHUNK_DEPTH+0x1d9d>
    3b15:	48 89 c7             	mov    rdi,rax
    3b18:	e8 ec d6 ff ff       	call   1209 <raw_print>
    3b1d:	b8 00 00 00 00       	mov    eax,0x0
    3b22:	c9                   	leave
    3b23:	c3                   	ret

0000000000003b24 <prompt>:
    3b24:	f3 0f 1e fa          	endbr64
    3b28:	55                   	push   rbp
    3b29:	48 89 e5             	mov    rbp,rsp
    3b2c:	48 83 ec 30          	sub    rsp,0x30
    3b30:	48 89 7d e8          	mov    QWORD PTR [rbp-0x18],rdi
    3b34:	48 89 75 e0          	mov    QWORD PTR [rbp-0x20],rsi
    3b38:	89 55 dc             	mov    DWORD PTR [rbp-0x24],edx
    3b3b:	48 83 7d e8 00       	cmp    QWORD PTR [rbp-0x18],0x0
    3b40:	74 1b                	je     3b5d <prompt+0x39>
    3b42:	48 8b 45 e8          	mov    rax,QWORD PTR [rbp-0x18]
    3b46:	48 89 c7             	mov    rdi,rax
    3b49:	e8 bb d6 ff ff       	call   1209 <raw_print>
    3b4e:	48 8d 05 68 22 00 00 	lea    rax,[rip+0x2268]        # 5dbd <CHUNK_DEPTH+0x1d9d>
    3b55:	48 89 c7             	mov    rdi,rax
    3b58:	e8 ac d6 ff ff       	call   1209 <raw_print>
    3b5d:	48 83 7d e0 00       	cmp    QWORD PTR [rbp-0x20],0x0
    3b62:	74 25                	je     3b89 <prompt+0x65>
    3b64:	8b 55 dc             	mov    edx,DWORD PTR [rbp-0x24]
    3b67:	48 8b 45 e0          	mov    rax,QWORD PTR [rbp-0x20]
    3b6b:	89 d6                	mov    esi,edx
    3b6d:	48 89 c7             	mov    rdi,rax
    3b70:	e8 27 d8 ff ff       	call   139c <raw_readline>
    3b75:	48 85 c0             	test   rax,rax
    3b78:	75 0f                	jne    3b89 <prompt+0x65>
    3b7a:	48 8d 05 97 0c 00 00 	lea    rax,[rip+0xc97]        # 4818 <CHUNK_DEPTH+0x7f8>
    3b81:	48 89 c7             	mov    rdi,rax
    3b84:	e8 80 d6 ff ff       	call   1209 <raw_print>
    3b89:	8b 05 a1 39 00 00    	mov    eax,DWORD PTR [rip+0x39a1]        # 7530 <be_annoying>
    3b8f:	48 98                	cdqe
    3b91:	48 89 45 f0          	mov    QWORD PTR [rbp-0x10],rax
    3b95:	48 c7 45 f8 00 00 00 	mov    QWORD PTR [rbp-0x8],0x0
    3b9c:	00 
    3b9d:	48 8d 45 f0          	lea    rax,[rbp-0x10]
    3ba1:	be 00 00 00 00       	mov    esi,0x0
    3ba6:	48 89 c7             	mov    rdi,rax
    3ba9:	e8 22 d5 ff ff       	call   10d0 <nanosleep@plt>
    3bae:	b8 00 00 00 00       	mov    eax,0x0
    3bb3:	c9                   	leave
    3bb4:	c3                   	ret

0000000000003bb5 <pwnable_unbuffer_init>:
    3bb5:	f3 0f 1e fa          	endbr64
    3bb9:	55                   	push   rbp
    3bba:	48 89 e5             	mov    rbp,rsp
    3bbd:	48 8b 05 7c 39 00 00 	mov    rax,QWORD PTR [rip+0x397c]        # 7540 <stdout@GLIBC_2.2.5>
    3bc4:	b9 00 00 00 00       	mov    ecx,0x0
    3bc9:	ba 02 00 00 00       	mov    edx,0x2
    3bce:	be 00 00 00 00       	mov    esi,0x0
    3bd3:	48 89 c7             	mov    rdi,rax
    3bd6:	e8 25 d5 ff ff       	call   1100 <setvbuf@plt>
    3bdb:	48 8b 05 7e 39 00 00 	mov    rax,QWORD PTR [rip+0x397e]        # 7560 <stderr@GLIBC_2.2.5>
    3be2:	b9 00 00 00 00       	mov    ecx,0x0
    3be7:	ba 02 00 00 00       	mov    edx,0x2
    3bec:	be 00 00 00 00       	mov    esi,0x0
    3bf1:	48 89 c7             	mov    rdi,rax
    3bf4:	e8 07 d5 ff ff       	call   1100 <setvbuf@plt>
    3bf9:	90                   	nop
    3bfa:	5d                   	pop    rbp
    3bfb:	c3                   	ret
