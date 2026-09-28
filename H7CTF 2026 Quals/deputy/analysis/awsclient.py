"""Fake-AWS client for the Deputy mock (no boto3 needed).

The mock never verifies the SigV4 signature: it reads the access key id from the
Authorization header (and session tokens from X-Amz-Security-Token). Every API is
dispatched from "/" by the Action parameter; /iam, /s3 ... are GET-only routes.
"""
import datetime
import requests

BASE = "https://web-d8f0b09a99a6a969.web.h7tex.com"
AK = "AKIAANALYST0000000000"
SK = "wJalrAnalystSecretKeyEXAMPLEbPxRfiCY"
VER = {"sts": "2011-06-15", "iam": "2010-05-08", "lambda": "2015-03-31",
       "kms": "2014-11-01", "dynamodb": "2012-08-10"}
_day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")


def call(action, svc="iam", params=None, token=None, key=None, version=None):
    d = {"Action": action}
    v = version or VER.get(svc)
    if v:
        d["Version"] = v
    d.update(params or {})
    kid = key or AK
    h = {"Authorization": "AWS4-HMAC-SHA256 Credential=" + kid + "/" + _day +
        "/us-east-1/" + svc + "/aws4_request, SignedHeaders=host, Signature=x"}
    if token:
        h["X-Amz-Security-Token"] = token
    r = requests.post(BASE + "/", data=d, headers=h, timeout=30)
    return r.status_code, r.text


def must(action, svc="iam", **kw):
    st, tx = call(action, svc, **kw)
    print("[%s] %s -> %d" % (svc, action, st))
    print(tx[:4000].strip(), "\n")
    return st, tx
