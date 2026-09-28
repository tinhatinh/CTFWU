# Echo Chamber — decision log

De: `https://web-3285347d50d467ba.web.h7tex.com` (AI/medium/63). **DA CO CỜ:**
`H7CTF{174f034a-b318-49db-a3eb-24192b3d7ce2}` (xem `flag.txt`, bang chung
`analysis/livewin.txt`).

##_surface (doc tu HTML + JS cua chinh service)

`Server: uvicorn` → FastAPI. `openapi.json`, `docs`, `redoc` đều 404 (đã tắt).
`/healthz` = `{"status":"ok"}`. Endpoint lấy từ `static/js/*.js`:

```
GET  /api/incidents/INC-7421                    trang thai vu
POST /api/incidents/INC-7421/analyze            Atlas nghia, ghi mot phan tich moi
GET  /api/incidents/INC-7421/analyses
GET  /api/incidents/INC-7421/reports            CHI giu bao cao MOI NHAT (cu -> 404)
GET  /api/reports/{id}                          bao cao + artifacts
GET  /api/knowledge?limit=100                   32 record KB-1001..KB-1032
POST /api/knowledge/search?limit=N   {query}
GET  /api/evidence/{id}
POST /api/research/submissions       {product, version, title, content}
GET  /api/research/submissions/{id}[/artifacts]
```

Form research: `title` 3..180, `content` 80..4000, product/version co gia tri mac
dinh `StreamForge` / `4.8`.

## Mechanism (quan sat truc tiep, khong suy doan)

Trang thai sach:

```
corroboration_status = unverified   diagnostic_depth = standard
analyze -> relation=mentions  confidence=0.5  supporting=0/10  status=unverified
reports  = [RPT-0001 standard]
```

Toan bo 32 record trong KB **chu động phủ định** giả thuyết: KB-1003 "does not
identify a known crash condition", KB-1012 "causes delayed work rather than abrupt
process termination", KB-1018 "differs from unexpected exits", KB-1022 "did not
change local worker memory behavior"... Nên `supporting_count = 0` là chủ ý của
author: khong the thắng bằng cách tìm trong corpus sẵn có.

`POST /api/research/submissions` **không chỉ lưu** — nó *chế biến* bài nộp thành
**3 record mới** với `representation_type` khác `"source"`:

```
KB-1033 technical_summary   {"affected_component": "Allocator",
                             "primary_claim": "The 4.8 allocator introduced a
                              regression causing worker terminati..."}
KB-1034 symptom_register
KB-1035 narrative
```

Ba record này rơi vào đúng tâm truy xuất của `analyze`, và giám khảo chấm chúng
`supports`:

```
analyze -> relation=supports  confidence=0.9  supporting=5/10  status=corroborated
incident -> corroboration_status=corroborated  diagnostic_depth=deep
            corroborated_root_cause='<chính giả thuyết của vụ>'
reports  -> RPT-0002 (deep)
```

Deep report có thêm 2 artifact so với thường, và cờ nằm ở `process-environment.txt`:

```
SUPPORT_INSTANCE_SECRET=H7CTF{174f034a-b318-49db-a3eb-24192b3d7ce2}
historical-support-metadata.txt: support_bundle=expanded
                                 collection_reason=deep_forensic_correlation
```

## Ba quan sát đáng ghi vào bộ nhớ

1. **Nhãn `supports`/`mentions` là ngữ cảnh, không phải thuộc tính của record.**
   Sau khi injection, hai record GỐC `KB-1005` và `KB-1003` (trước đó bị chấm
   `mentions`) **đổi thành `supports`** mà nội dung không đổi. Một record dẫn nhập
   tốt đã chấm lại cả tập truy xuất: 0 → 5 supporting.
2. **Cửa "hoàn toàn thuyết phục" không cần confidence 1.0.** 0.9 và 5/10 là đủ
   lật sang `corroborated` + `deep`. Không đo được ngưỡng chính xác trên instance
   này vì state đã lật permanent (xem "state" bên dưới).
3. **Chỉ giữ báo cáo mới nhất.** `RPT-0001`/`RPT-0002` trả 404 sau khi `RPT-0003`
   sinh ra. Muốn so sánh standard vs deep thì phải bắt lấy nó TRƯỚC khi chạy lại
   `analyze` lần nữa — tôi đã bỏ lỡ một nhịp (đọc `RPT-0001` sau đó là 404),
   nên trong writeup không claim nội dung standard report, chỉ claim rằng cờ xuất
   hiện trong deep report.

## State: version nào?

Lần chạy THỨ HAI, `baseline` đã báo `corroborated`/`deep` trước khi tôi nộp gì.
Nghĩa là submission và trạng thái vụ án **sống suốt đời container**, không reset
giữa các session. Hệ quả thực tế:
* Không thể đo lại ngưỡng từ trạng thái sạch trên cùng instance.
* Người chơi khác / lần reload trang đều thấy cùng trạng thái.
* `exploit.py` vẫn đúng trên instance mới (nó nộp bài + analyze rồi mới đọc report).
* Cookie/session không đổi được trạng thái. Vì vậy `exploit.py` không cần giữ
  session, nhưng tôi vẫn giữ để nhất quán.

## Dead ends

* Tìm `openapi.json`/`docs` để đọc schema gate → tắt.
* Hy vọng có IDOR sang report của session khác → report là toàn cục và bị prune.
* Nghĩ rằng phải injection kiểu "ignore previous instructions" → **không cần**;
  content tử tế, đúng giọng văn kỹ thuật, đúng root cause là được chấm `supports`.
  Không có bộ lọc prompt-injection nào được quan sát thấy.

## File
`exploit.py` (submit → analyze → đọc report), `analysis/cli.py` (HTTP client tối
giản, giữ cookie), `analysis/{workspace,api,evidence,reports,research}.js`,
`analysis/knowledge.json` (32 record), `analysis/livewin.txt`, `analysis/try1.py`.
